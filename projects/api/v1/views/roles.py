from ninja import Router
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404

from accounts.api.v1.services.auth import JWTAuth
from projects.models import ProjectMember, Project, CustomUser
from projects.api.v1.schemas.projects import *
from accounts.api.v1.utils.response import api_response

role_api = Router(tags=["Roles"])
auth = JWTAuth()

class PermissionOut(Schema):
    id: int
    codename: str
    name: str
    content_type: str

@role_api.get("/permissions/", response=List[PermissionOut])
def list_permissions(request):
    permissions = Permission.objects.select_related("content_type").all()
    return api_response(data=[
        PermissionOut(
            id=p.id,
            codename=p.codename,
            name=p.name,
            content_type=f"{p.content_type.app_label}.{p.content_type.model}"
        )
        for p in permissions
    ], message="Permissions fetched")

@role_api.post("/create/")
def create_role(request, payload: RoleCreateIn):
    if Group.objects.filter(name=payload.name).exists():
        return api_response(status_code=400, message="Role already exists")
    group = Group.objects.create(name=payload.name)
    perms = Permission.objects.filter(codename__in=payload.permission_codenames)
    group.permissions.set(perms)
    return api_response(message="Role created", data={"id": group.id, "name": group.name, "permissions": [{
        "id": perm.id,
        "name": perm.name,
        "codename": perm.codename
    } for perm in perms]})

# Get all existing roles with their permissions
@role_api.get("/groups/", response=List[RoleOut])
def list_roles_groups(request):
    roles = Group.objects.prefetch_related("permissions").all()
    return [
        RoleOut(
            id=role.id,
            name=role.name,
            permission_codenames=[p.codename for p in role.permissions.all()]
        )
        for role in roles
    ]

# Assign role (Group) to a user for a project
@role_api.post("/group/assign/")
def assign_project_role(request, payload: AssignProjectRoleIn):
    user = get_object_or_404(CustomUser, id=payload.user_id)
    project = get_object_or_404(Project, id=payload.project_id)
    role = get_object_or_404(Group, id=payload.role_id)

    member, created = ProjectMember.objects.get_or_create(
        user=user,
        project=project,
        defaults={"role": role}
    )
    if not created:
        member.role = role
        member.save()

    return api_response(
        message="Role assigned to user for the project",
        data={
            "user_id": user.id,
            "project_id": project.id,
            "role_id": role.id,
            "role_name": role.name
        }
    )
