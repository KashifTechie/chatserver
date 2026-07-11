from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from account.models import AccountUser
from rest_framework_simplejwt.tokens import RefreshToken
from ...utils import get_tokens_for_user
from ..conf.github import GitHubOAuth
from django.conf import settings
from account.models import AccountUser


class GitHubLoginURLView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        github_oauth = GitHubOAuth()
        return Response({"url": github_oauth.get_auth_url()})


class GitHubCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        
        code = request.GET.get("code")

        if not code:
            return redirect(f"{settings.FRONTEND_URL}/login?error=github_failed")

        github_oauth = GitHubOAuth()

        token_data = github_oauth.exchange_code(code)
        access_token = token_data.get("access_token")

        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/login?error=github_failed")

        user_info = github_oauth.get_user_info(access_token)
        email = user_info.get("email")

        if not email:
            return redirect(f"{settings.FRONTEND_URL}/login?error=no_github_email")

        user, _ = AccountUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "is_active": True,
                "is_verified": True, 
                "registration_method": AccountUser.RegistrationMethod.GITHUB  # GitHub already verified email
            }
        )

        # refresh = RefreshToken.for_user(user)

        # return redirect(
        #     f"{settings.FRONTEND_URL}/auth/success"
        #     f"?access={str(refresh.access_token)}&refresh={str(refresh)}"
        # )

        tokens = get_tokens_for_user(user)
        access_token = tokens.get('access')
        refresh_token = tokens.get('refresh')
        return redirect(
            f"{settings.FRONTEND_URL}/auth/success"
            f"?access={str(access_token)}&refresh={str(refresh_token)}"
        )