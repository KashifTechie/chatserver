"""
Authentication URLs - organized by feature.

Endpoints:
- POST   /auth/register/
- POST   /auth/login/
- POST   /auth/logout/
- POST   /auth/refresh/
- GET    /auth/me/
- PATCH  /auth/profile/
"""

from django.urls import path
from authentication.views import (
    RegisterView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    CurrentUserView,
    ProfileUpdateView,
)

urlpatterns = [
    # Core authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh"),
    
    # User profile
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("profile/", ProfileUpdateView.as_view(), name="profile_update"),
]
