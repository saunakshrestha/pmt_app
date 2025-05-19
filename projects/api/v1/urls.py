# projects/api/v1/urls.py

from django.urls import path
from ninja import NinjaAPI
from accounts.api.v1.utils.exceptions import register_custom_exception_handlers
from projects.api.v1.views.projects import projects_api
from projects.api.v1.views.roles import role_api

from accounts.api.v1.services.auth import JWTAuth


api = NinjaAPI(title="Project Management Tool API", version="1.0")
api.add_router("project/", projects_api)
api.add_router("roles/", role_api)

register_custom_exception_handlers(api)
urlpatterns = [
    path("v1/", api.urls),  # ✅ Correct way: wrap api.urls in a path()
]