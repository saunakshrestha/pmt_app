# projects/urls.py

from django.urls import path, include

urlpatterns = [
    path("api/", include("projects.api.v1.urls")),  # Versioned API under /api/v1/
]