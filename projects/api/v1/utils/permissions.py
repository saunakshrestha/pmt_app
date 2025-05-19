from functools import wraps
from ninja.errors import HttpError
from projects.models import ProjectMember, Board, Sprint, Task

import logging
logger = logging.getLogger("api")

MODEL_PROJECT_MAP = {
    "board_id": lambda pk: Board.objects.select_related("project").get(id=pk).project_id,
    "sprint_id": lambda pk: Sprint.objects.select_related("project").get(id=pk).project_id,
    "task_id": lambda pk: Task.objects.select_related("project").get(id=pk).project_id,
}

def require_project_permission(
    permission_codename: str,
    *,
    project_kwarg: str = None,
    resolve_from: str = None
):
    """
    Decorator to ensure the user has a specific permission for a project,
    resolving the project from project_id directly or via a related object.

    Args:
        permission_codename: e.g., 'view_task'
        project_kwarg: Name of the kwarg that holds the project_id
        resolve_from: Name of the kwarg to resolve the project_id indirectly
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            project_id = None

            # Case 1: Direct project ID (URL or query param)
            if project_kwarg:
                project_id = kwargs.get(project_kwarg) or request.GET.get(project_kwarg)
                if not project_id:
                    raise HttpError(400, f"Missing `{project_kwarg}` in request.")

            # Case 2: Resolve project from another object ID (board, sprint, task, etc.)
            elif resolve_from:
                related_id = kwargs.get(resolve_from) or request.GET.get(resolve_from)

                if not related_id:
                    raise HttpError(400, f"Missing `{resolve_from}` in request.")
                try:
                    project_id = MODEL_PROJECT_MAP[resolve_from](related_id)
                except KeyError:
                    raise HttpError(500, f"Unsupported lookup key: {resolve_from}")
                except Exception as e:
                    raise HttpError(404, f"Invalid ID or object not found for `{resolve_from}`: {str(e)}")

            # Ensure we have a project_id
            if not project_id:
                raise HttpError(400, "Unable to resolve project context.")

            # Membership & permission check
            member = ProjectMember.objects.filter(
                user=user,
                project_id=project_id
            ).select_related("role").first()

            if not member or not member.role:
                raise HttpError(403, "You are not a member of this project.")

            # Role permissions must be a ManyToManyField to Permission objects
            if not member.role.permissions.filter(codename=permission_codename).exists():
                raise HttpError(403, f"Missing required permission: '{permission_codename}'.")

            # Pass project_id in kwargs if not already present, for downstream logic
            if project_kwarg and project_kwarg not in kwargs:
                kwargs[project_kwarg] = project_id

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator