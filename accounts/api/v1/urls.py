

from django.urls import path
from ninja import NinjaAPI
from accounts.api.v1.utils.exceptions import register_custom_exception_handlers
from accounts.api.v1.views.login import router as login_api

api = NinjaAPI(title="Accounts Main API", version="1.0", urls_namespace="accounts_api")

api.add_router("/login/", login_api)

register_custom_exception_handlers(api)
urlpatterns = [
    path("v1/", api.urls),  # ✅ Correct way: wrap api.urls in a path()
]
