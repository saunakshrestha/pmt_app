
from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Q

from accounts.api.v1.utils.exceptions import ApiValidationError
from accounts.models import CustomUser
from projects.api.v1.utils.permissions import require_project_permission
from projects.api.v1.validator.projects import validate_project_unique_name
from projects.models import Project, Board, ProjectMember, Sprint, Task, Label, Comment
from accounts.api.v1.utils.response import api_response
from projects.api.v1.utils.pagination import paginate_queryset
from projects.api.v1.schemas.projects import *
from starlette import status
from accounts.api.v1.services.auth import JWTAuth
from django.contrib.auth.models import Group

import logging
logger = logging.getLogger('api')

projects_api = Router(tags=["Projects"])

auth = JWTAuth()

# -------------------- PROJECT --------------------
# LIST
@projects_api.get("", auth=auth)
def list_projects(request, page: int = 1, limit: int = 20):
    filters = Q(tenant=request.user.tenant)
    filters.add(Q(project_member__user=request.user), Q.AND)
    qs = Project.objects.select_related("tenant", "created_by").filter(filters)
    # paginate_queryset is your helper
    results, meta = paginate_queryset(qs, page, limit)
    return api_response(
        data=[ProjectOut.model_validate(obj) for obj in results],
        message="Projects fetched",
        meta=meta
    )

@projects_api.post("", auth=auth)
def create_project(request, payload: ProjectIn):
    try:
        validate_project_unique_name(payload.name, request.user.tenant)
        project_data = payload.model_dump()
        project_data["created_by"] = request.user
        project_data["tenant"] = request.user.tenant
        project = Project.objects.create(**project_data)
        return api_response(
            data=ProjectOut.model_validate(project),
            message="Project created"
        )

    except ApiValidationError as exc:
        logger.error(f"Validation error: {exc}")
        return api_response(
            status_code=400,
            error={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        )
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return api_response(
            status_code=500,
            message="Error creating project",
            error=str(e)
        )

@projects_api.get("/{id}/", auth=auth)
def get_project(request, id: int):
    project = get_object_or_404(Project.objects.select_related("tenant", "created_by"), id=id)
    return api_response(data=ProjectOut.model_validate(project), message="Project fetched")

@projects_api.put("/{id}/", auth=auth)
def update_project(request, id: int, payload: ProjectIn):
    project = get_object_or_404(Project, id=id)
    validate_project_unique_name(name=payload.name, tenant=request.user.tenant, project=project)
    for attr, value in payload.model_dump().items():
        setattr(project, attr, value)
    project.save(update_fields=list(payload.model_dump().keys()))
    return api_response(data=ProjectOut.model_validate(project), message="Project updated")

@projects_api.patch("/{id}/", response=ProjectOut, auth=auth)
def update_partial_project(request, id: int, payload: ProjectPatchIn):
    project = get_object_or_404(Project, id=id)
    validate_project_unique_name(name=payload.name, tenant=request.user.tenant, project=project)

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    project.save()

    return api_response(
        data=ProjectOut.model_validate(project),
        message="Project updated successfully"
    )

# DELETE
@projects_api.delete("/{id}/", auth=auth)
def delete_project(request, id: int):
    project = get_object_or_404(Project, id=id)
    project.delete()
    return api_response(message="Project deleted", data=None, status_code=status.HTTP_204_NO_CONTENT)

# -------------------- PROJECT MEMBERS --------------------

@projects_api.get("/project-members", response=ProjectMemberOut, auth=auth)
def list_project_members(request):
    members = ProjectMember.objects.filter(project__tenant=request.user.tenant)
    return api_response(
        data=[ProjectMemberOut.model_validate(m) for m in members],
        message="Project members fetched"
    )

@projects_api.post("/project-members", response=ProjectMemberOut, auth=auth)
def create_project_member(request, payload: ProjectMemberIn):
    project = get_object_or_404(Project, id=payload.project_id, tenant=request.user.tenant)
    user = get_object_or_404(CustomUser, id=payload.user_id)
    role = get_object_or_404(Group, id=payload.role_id)

    member = ProjectMember.objects.create(
        project=project,
        user=user,
        role=role
    )
    return api_response(data=ProjectMemberOut.model_validate(member), message="Member added")

@projects_api.get("/project-members/{id}", response=ProjectMemberOut, auth=auth)
def get_project_member(request, id: int):
    member = get_object_or_404(ProjectMember, id=id, project__tenant=request.user.tenant)
    return api_response(data=ProjectMemberOut.model_validate(member), message="Member fetched")

@projects_api.put("/project-members/{id}", response=ProjectMemberOut, auth=auth)
def update_project_member(request, id: int, payload: ProjectMemberIn):
    member = get_object_or_404(ProjectMember, id=id, project__tenant=request.user.tenant)

    member.project_id = payload.project_id
    member.user_id = payload.user_id
    member.role_id = payload.role_id
    member.save()

    return api_response(data=ProjectMemberOut.model_validate(member), message="Member updated")

@projects_api.patch("/project-members/{id}", response=ProjectMemberOut, auth=auth)
def patch_project_member(request, id: int, payload: ProjectMemberPatchIn):
    member = get_object_or_404(ProjectMember, id=id, project__tenant=request.user.tenant)
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(member, field, value)
    member.save(update_fields=list(update_data.keys()))

    return api_response(data=ProjectMemberOut.model_validate(member), message="Member updated")

@projects_api.delete("/project-members/{id}", auth=auth)
def delete_project_member(request, id: int):
    member = get_object_or_404(ProjectMember, id=id, project__tenant=request.user.tenant)
    member.delete()
    return api_response(message="Member deleted", status_code=status.HTTP_200_OK)

# -------------------- BOARD --------------------
@projects_api.get("{project_id}/board/", auth=auth)
@require_project_permission("view_board", project_kwarg="project_id")
def list_boards(request, project_id: int, page: int = 1, limit: int = 20):
    qs = Board.objects.select_related("project", "created_by").filter(
        tenant=request.user.tenant
    ).order_by("-created_at")

    result, meta = paginate_queryset(qs, page, limit)
    data = [BoardOut.model_validate(obj) for obj in result]

    return api_response(data=data, message="Boards fetched successfully")


@projects_api.post("{project_id}/board/", auth=auth)
@require_project_permission("add_board", project_kwarg="project_id")
def create_board(request, payload: BoardIn, project_id: int):
    project = get_object_or_404(Project, id=project_id, tenant=request.user.tenant)
    board = Board.objects.create(
        name=payload.name,
        project=project,
        tenant=request.user.tenant,
        created_by=request.user
    )
    return api_response(data=BoardOut.model_validate(board), message="Board created")


@projects_api.get("{project_id}/board/{board_id}/", auth=auth)
@require_project_permission("view_board", project_kwarg="project_id")
def get_board(request, project_id: int, board_id: int):
    board = get_object_or_404(Board, id=board_id, project_id=project_id, tenant=request.user.tenant)
    return api_response(data=BoardOut.model_validate(board), message="Board fetched")


@projects_api.put("{project_id}/board/{board_id}/", auth=auth)
@require_project_permission("change_board", project_kwarg="project_id")
def update_board(request, project_id: int, board_id: int, payload: BoardIn):
    board = get_object_or_404(Board, id=board_id, project_id=project_id, tenant=request.user.tenant)
    board.name = payload.name
    board.save()
    return api_response(data=BoardOut.model_validate(board), message="Board updated")


@projects_api.patch("{project_id}/board/{board_id}/", auth=auth)
@require_project_permission("change_board", project_kwarg="project_id")
def patch_board(request, project_id: int, board_id: int, payload: BoardPatchIn):
    board = get_object_or_404(Board, id=board_id, project_id=project_id, tenant=request.user.tenant)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        board.name = update_data["name"]

    board.save(update_fields=list(update_data.keys()))
    return api_response(data=BoardOut.model_validate(board), message="Board patched")


@projects_api.delete("{project_id}/board/{board_id}/", auth=auth)
@require_project_permission("delete_board", project_kwarg="project_id")
def delete_board(request, project_id: int, board_id: int):
    board = get_object_or_404(Board, id=board_id, project_id=project_id, tenant=request.user.tenant)
    board.delete()
    return api_response(message="Board deleted", status_code=status.HTTP_200_OK)

# -------------------- SPRINTS --------------------
@projects_api.post("board/{board_id}/sprints/", auth=auth)
@require_project_permission("add_sprint", resolve_from="board_id")
def create_sprint(request, board_id: int, payload: SprintIn):
    board = get_object_or_404(Board, id=board_id, tenant=request.user.tenant)
    sprint = Sprint.objects.create(
        board=board,
        project=board.project,
        tenant=request.user.tenant,
        **payload.model_dump()
    )
    return api_response(data=SprintOut.model_validate(sprint), message="Sprint created")

@projects_api.get("board/{board_id}/sprints/", auth=auth)
@require_project_permission("view_sprint", resolve_from="board_id")
def list_sprints(request, board_id: int, page: int = 1, limit: int = 20):
    sprints = Sprint.objects.filter(board_id=board_id, tenant=request.user.tenant).order_by("-created_at")
    result, meta = paginate_queryset(sprints, page, limit)
    return api_response(data=[SprintOut.model_validate(s) for s in result], message="Sprints fetched", meta=meta)

@projects_api.get("board/{board_id}/sprints/{sprint_id}/", auth=auth)
@require_project_permission("view_sprint", resolve_from="sprint_id")
def get_sprint(request,  board_id: int, sprint_id: int):
    sprint = get_object_or_404(Sprint, id=sprint_id,  board_id= board_id, tenant=request.user.tenant)
    return api_response(data=SprintOut.model_validate(sprint), message="Sprint fetched")

@projects_api.put("board/{board_id}/sprints/{sprint_id}/", auth=auth)
@require_project_permission("change_sprint", resolve_from="sprint_id")
def update_sprint(request, board_id: int, sprint_id: int, payload: SprintIn):
    sprint = get_object_or_404(Sprint, id=sprint_id, board_id= board_id, tenant=request.user.tenant)
    for attr, value in payload.model_dump().items():
        setattr(sprint, attr, value)
    sprint.save()
    return api_response(data=SprintOut.model_validate(sprint), message="Sprint updated")

@projects_api.patch("board/{board_id}/sprints/{sprint_id}/", auth=auth)
@require_project_permission("change_sprint", resolve_from="sprint_id")
def patch_sprint(request, board_id: int, sprint_id: int, payload: SprintPatchIn):
    sprint = get_object_or_404(Sprint, id=sprint_id, board_id= board_id, tenant=request.user.tenant)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sprint, field, value)
    sprint.save(update_fields=list(update_data.keys()))
    return api_response(data=SprintOut.model_validate(sprint), message="Sprint updated")

@projects_api.delete("board/{board_id}/sprints/{sprint_id}/", auth=auth)
@require_project_permission("delete_sprint", resolve_from="sprint_id")
def delete_sprint(request, board_id: int, sprint_id: int):
    sprint = get_object_or_404(Sprint, id=sprint_id, board_id= board_id, tenant=request.user.tenant)
    sprint.delete()
    return api_response(message="Sprint deleted")


# -------------------- TASKS --------------------
@projects_api.post("/board/{board_id}/task/", auth=auth)
@require_project_permission("add_task", resolve_from="board_id")
def create_task(request, board_id: int, payload: TaskIn):
    board = get_object_or_404(Board, id=board_id, tenant=request.user.tenant)
    task = Task.objects.create(
        board=board,
        project=board.project,
        tenant=request.user.tenant,
        created_by=request.user,
        updated_by=request.user,
        **payload.model_dump(exclude={"label_ids"})
    )
    if payload.label_ids:
        task.labels.set(Label.objects.filter(id__in=payload.label_ids))
    return api_response(data=TaskOut.model_validate(task), message="Task created")

@projects_api.get("/board/{board_id}/task/", auth=auth)
@require_project_permission("view_task", resolve_from="board_id")
def list_tasks(request, board_id: int, page: int = Query(1), limit: int = Query(20)):
    tasks = Task.objects.filter(board_id=board_id, is_deleted=False, tenant=request.user.tenant).order_by("-created_at")
    result, meta = paginate_queryset(tasks, page, limit)
    return api_response(data=[TaskOut.model_validate(t) for t in result], message="Tasks fetched", meta=meta)

@projects_api.get("/board/{board_id}/task/{task_id}/", auth=auth)
@require_project_permission("view_task", resolve_from="task_id")
def get_task(request, board_id: int, task_id: int):
    task = get_object_or_404(Task, id=task_id, board_id=board_id, tenant=request.user.tenant)
    return api_response(data=TaskOut.model_validate(task), message="Task fetched")

@projects_api.put("/board/{board_id}/task/{task_id}/", auth=auth)
@require_project_permission("change_task", resolve_from="task_id")
def update_task(request, board_id: int, task_id: int, payload: TaskIn):
    task = get_object_or_404(Task, id=task_id, board_id=board_id, tenant=request.user.tenant)
    for attr, value in payload.model_dump(exclude={"label_ids"}).items():
        setattr(task, attr, value)
    task.updated_by = request.user
    task.save()
    if payload.label_ids is not None:
        task.labels.set(Label.objects.filter(id__in=payload.label_ids))
    return api_response(data=TaskOut.model_validate(task), message="Task updated")

@projects_api.patch("/board/{board_id}/task/{task_id}/", auth=auth)
@require_project_permission("change_task", resolve_from="task_id")
def patch_task(request, board_id: int, task_id: int, payload: TaskPatchIn):
    task = get_object_or_404(Task, id=task_id, board_id=board_id, tenant=request.user.tenant)
    update_data = payload.model_dump(exclude_unset=True, exclude={"label_ids"})
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_by = request.user
    task.save(update_fields=list(update_data.keys()))
    return api_response(data=TaskOut.model_validate(task), message="Task updated")

@projects_api.delete("/board/{board_id}/task/{task_id}/", auth=auth)
@require_project_permission("delete_task", resolve_from="task_id")
def delete_task(request, board_id: int, task_id: int):
    task = get_object_or_404(Task, id=task_id, board_id=board_id, tenant=request.user.tenant)
    task.is_deleted = True
    task.updated_by = request.user
    task.save(update_fields=["is_deleted", "updated_by"])
    return api_response(message="Task deleted")

# -------------------- LABELS --------------------

@projects_api.post("{project_id}/label/", response=LabelOut, auth=auth)
@require_project_permission("add_label", project_kwarg="project_id")
def create_label(request, project_id: int, payload: LabelIn):
    label = Label.objects.create(
        tenant=request.user.tenant,
        project_id=project_id,
        name=payload.name,
        color=payload.color
    )
    return label

@projects_api.get("{project_id}/label/", response=list[LabelOut], auth=auth)
@require_project_permission("view_label", project_kwarg="project_id")
def list_labels(request, project_id: int):
    labels = Label.objects.filter(tenant=request.user.tenant,project_id=project_id)
    return list(labels)

@projects_api.get("{project_id}/label/{label_id}/", response=LabelOut, auth=auth)
@require_project_permission("view_label", project_kwarg="project_id")
def get_label(request, project_id: int, label_id: int):
    label = get_object_or_404(Label, project_id=project_id, id=label_id, tenant=request.user.tenant)
    return label

@projects_api.put("{project_id}/label/{label_id}/", response=LabelOut, auth=auth)
@require_project_permission("change_label", project_kwarg="project_id")
def update_label(request, project_id: int, label_id: int, payload: LabelIn):
    label = get_object_or_404(Label, project_id=project_id, id=label_id, tenant=request.user.tenant)
    label.name = payload.name
    label.color = payload.color
    label.save()
    return label

@projects_api.patch("{project_id}/label/{label_id}/", response=LabelOut, auth=auth)
@require_project_permission("change_label", project_kwarg="project_id")
def patch_label(request, project_id: int, label_id: int, payload: LabelPatchIn):
    label:Label = get_object_or_404(Label, project_id=project_id, id=label_id, tenant=request.user.tenant)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(label, field, value)
    label.save(update_fields=list(update_data.keys()))

    return api_response(data=LabelOut.model_validate(label), message="Label updated")

@projects_api.delete("{project_id}/label/{label_id}/", auth=auth)
@require_project_permission("delete_label", project_kwarg="project_id")
def delete_label(request, project_id: int, label_id: int):
    label = get_object_or_404(Label, project_id=project_id, id=label_id, tenant=request.user.tenant)
    label.delete()
    return api_response(message="Label deleted")

# ---------------------------------------
# -------------------- COMMENTS ---------
# ---------------------------------------

@projects_api.post("task/{task_id}/comment/", response=CommentOut, auth=auth)
@require_project_permission("add_comment", resolve_from="task_id")
def create_comment(request, task_id: int, payload: CommentIn):
    task = get_object_or_404(Task, id=task_id, tenant=request.user.tenant)
    comment = Comment.objects.create(
        tenant=request.user.tenant,
        project=task.project,
        task=task,
        user=request.user,
        content=payload.content,
        parent_id=payload.parent_id
    )
    return api_response(
        data=CommentOut.model_validate(comment),
        message="Comment created"
    )

@projects_api.get("task/{task_id}/comment/", response=list[CommentOut], auth=auth)
@require_project_permission("view_comment", resolve_from="task_id")
def list_comments(request, task_id: int):
    comments = Comment.objects.filter(
        tenant=request.user.tenant,
        task_id=task_id
    )
    return api_response(
        data=[CommentOut.model_validate(c) for c in comments],
        message="Comments fetched"
    )

@projects_api.get("task/{task_id}/comment/{comment_id}/", response=CommentOut, auth=auth)
@require_project_permission("view_comment", resolve_from="task_id")
def get_comment(request, task_id:int, comment_id: int):
    comment = get_object_or_404(Comment, task_id = task_id, id=comment_id, tenant=request.user.tenant)
    return comment

@projects_api.put("task/{task_id}/comment/{comment_id}/", response=CommentOut, auth=auth)
@require_project_permission("change_comment", resolve_from="task_id")
def update_comment(request, task_id: int, comment_id: int, payload: CommentIn):
    comment = get_object_or_404(Comment, task_id=task_id, id=comment_id, tenant=request.user.tenant)
    comment.content = payload.content
    comment.is_edited = True
    comment.save(update_fields=["content", "is_edited"])
    return comment

@projects_api.patch("task/{task_id}/comment/{comment_id}/", response=CommentOut, auth=auth)
@require_project_permission("change_comment", resolve_from="task_id")
def patch_comment(request, task_id: int, comment_id: int, payload: CommentPatchIn):
    comment:Comment = get_object_or_404(Comment, task_id=task_id, id=comment_id, tenant=request.user.tenant)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    comment.save(update_fields=list(update_data.keys()))
    return api_response(data=CommentOut.model_validate(comment), message="Comment updated")

@projects_api.delete("task/{task_id}/comment/{comment_id}/", auth=auth)
@require_project_permission("delete_comment", resolve_from="task_id")
def delete_comment(request, task_id: int, comment_id: int):
    comment = get_object_or_404(Comment, task_id=task_id, id=comment_id, tenant=request.user.tenant)
    comment.delete()
    return api_response(message="Comment deleted")