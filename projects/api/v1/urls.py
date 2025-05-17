# projects/api/v1/urls.py

from django.urls import path
from ninja import NinjaAPI
from accounts.api.v1.utils.exceptions import register_custom_exception_handlers
from projects.api.v1.views.projects import api as pmt_api
from accounts.api.v1.services.auth import JWTAuth


api = NinjaAPI(title="Project Management Tool API", version="1.0")
api.add_router("/v1/", pmt_api)

register_custom_exception_handlers(api)
urlpatterns = [
    path("", api.urls),  # ✅ Correct way: wrap api.urls in a path()
]