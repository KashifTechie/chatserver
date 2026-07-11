from django.urls import path
from .social_media_auth.google.google import (
    GoogleLoginURLView,
    GoogleCallbackView
)
from .social_media_auth.github.github import (
    GitHubLoginURLView,
    GitHubCallbackView
)

from .social_media_auth.X.x import (
    XLoginURLView,
    XCallbackView
)

from .social_media_auth.facebook.facebook import (
    FacebookLoginURLView,
    FacebookCallbackView
)

from .social_media_auth.linkedin.linkedin import (
    LinkedInLoginURLView,
    LinkedInCallbackView
)

from rest_framework_simplejwt.views import TokenRefreshView
from .jwt_auth import CustomTokenObtainPairView

urlpatterns = [
    path("/auth/google",            GoogleLoginURLView.as_view()),
    path("/google/login/callback",   GoogleCallbackView.as_view()),
    path("/auth/github",            GitHubLoginURLView.as_view()),
    path("/github/login/callback",   GitHubCallbackView.as_view()),
    path("/auth/x",                 XLoginURLView.as_view()),
    path("/x/login/callback",        XCallbackView.as_view()),
    path("/auth/facebook",                 FacebookLoginURLView.as_view()),
    path("/facebook/login/callback",        FacebookCallbackView.as_view()),
    path("/auth/linkedin",                 LinkedInLoginURLView.as_view()),
    path("/linkedin/login/callback",        LinkedInCallbackView.as_view()),

    # JWT authentication endpoints
    path("/auth/login",              CustomTokenObtainPairView.as_view()),
    path("/auth/login/refresh",      TokenRefreshView.as_view()),
    # path(),
]