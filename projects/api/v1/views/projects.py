
from ninja import Router
from django.shortcuts import get_object_or_404

from accounts.api.v1.utils.exceptions import ApiValidationError
from projects.api.v1.validator.projects import validate_project_unique_name
from projects.models import Resource, Role, Project
from accounts.api.v1.utils.response import api_response
from projects.api.v1.utils.pagination import paginate_queryset
from projects.api.v1.schemas.projects import *
from starlette import status
from accounts.api.v1.services.auth import JWTAuth

import logging
logger = logging.getLogger('api')

api = Router()
auth = JWTAuth()

# -------------------- PROJECT --------------------
# LIST
@api.get("/projects", auth=auth)
def list_projects(request, page: int = 1, limit: int = 20):
    qs = Project.objects.select_related("tenant", "created_by").all()
    # paginate_queryset is your helper
    results, meta = paginate_queryset(qs, page, limit)
    return api_response(
        data=[ProjectOut.model_validate(obj) for obj in results],
        message="Projects fetched",
        meta=meta
    )

@api.post("/projects", auth=auth)
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

@api.get("/projects/{id}", auth=auth)
def get_project(request, id: int):
    project = get_object_or_404(Project.objects.select_related("tenant", "created_by"), id=id)
    return api_response(data=ProjectOut.model_validate(project), message="Project fetched")

@api.put("/projects/{id}", auth=auth)
def update_project(request, id: int, payload: ProjectIn):
    project = get_object_or_404(Project, id=id)
    validate_project_unique_name(name=payload.name, tenant=request.user.tenant, project=project)
    for attr, value in payload.model_dump().items():
        setattr(project, attr, value)
    project.save(update_fields=list(payload.model_dump().keys()))
    return api_response(data=ProjectOut.model_validate(project), message="Project updated")

@api.patch("/projects/{id}", response=ProjectOut, auth=auth)
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
@api.delete("/projects/{id}", auth=auth)
def delete_project(request, id: int):
    project = get_object_or_404(Project, id=id)
    project.delete()
    return api_response(message="Project deleted", data=None, status_code=status.HTTP_204_NO_CONTENT)

# -------------------- ROLE --------------------
@api.get("/roles")
def list_roles(request, page: int = 1, limit: int = 20):
    queryset = Role.objects.all()
    results, meta = paginate_queryset(queryset, page, limit)
    return api_response(data=[RoleOut.model_validate(obj) for obj in results], message="Roles fetched", meta=meta)

@api.post("/roles")
def create_role(request, payload: RoleIn):
    role = Role.objects.create(**payload.dict())
    return api_response(data=RoleOut.from_orm(role), message="Role created")

@api.get("/roles/{id}")
def get_role(request, id: int):
    role = get_object_or_404(Role, id=id)
    return api_response(data=RoleOut.from_orm(role), message="Role fetched")

@api.put("/roles/{id}")
def update_role(request, id: int, payload: RoleIn):
    role = get_object_or_404(Role, id=id)
    for attr, value in payload.dict().items():
        setattr(role, attr, value)
    role.save()
    return api_response(data=RoleOut.from_orm(role), message="Role updated")

@api.delete("/roles/{id}")
def delete_role(request, id: int):
    role = get_object_or_404(Role, id=id)
    role.delete()
    return api_response(message="Role deleted")