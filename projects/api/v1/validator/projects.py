from projects.models import Project
from accounts.api.v1.utils.exceptions import ApiValidationError

def validate_project_unique_name(name, tenant, project:Project=None):
    if project:
        if Project.objects.filter(tenant=tenant, name=name).exclude(id=project.id).exists():
            raise ApiValidationError(
                details={"name": ["Project with this name already exists"]},
                message="Project with this name already exists"
            )
    else:
        if Project.objects.filter(tenant=tenant, name=name).exists():
            raise ApiValidationError(
                details={"name": ["Project with this name already exists"]},
                message="Project with this name already exists"
            )