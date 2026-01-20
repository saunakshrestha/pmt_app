# accounts/urls.py

from django.urls import path, include
from accounts import views

urlpatterns = [
    # Portal authentication
    path("login/", views.portal_login, name="portal_login"),
    path("logout/", views.portal_logout, name="portal_logout"),
    
    # API routes
    path("api/", include("accounts.api.v1.urls"), name="accounts")
]