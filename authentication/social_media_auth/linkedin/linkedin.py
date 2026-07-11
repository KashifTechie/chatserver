from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from account.models import AccountUser
from ..conf.linkedin import LinkedInOAuth
from authentication.utils import get_tokens_for_user
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class LinkedInLoginURLView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        linkedin_oauth = LinkedInOAuth()
        auth_url = linkedin_oauth.get_auth_url()
        logger.info("The linkedin login auth URL is generated %s", auth_url)
        return Response({"auth_url": auth_url})
    
class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=linkedin_failed")

        linkedin_oauth = LinkedInOAuth()
        token_data = linkedin_oauth.exchange_code(code)
        access_token = token_data.get("access_token")

        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=linkedin_failed")

        user_info = linkedin_oauth.get_user_info(access_token)
        email = user_info.get("email")
        name = user_info.get("name", "")

        if not email:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=no_linkedin_email")

        user, _ = AccountUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": name.split()[0] if name else "",
                "last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                "is_active": True,
                "is_verified": True, 
                "registration_method": AccountUser.RegistrationMethod.LinkedIn
            }
        )

        tokens = get_tokens_for_user(user)
        access_token = tokens.get('access')
        refresh_token = tokens.get('refresh')
        return redirect(
            f"{settings.FRONTEND_URL}/auth/success?access_token={access_token}&refresh_token={refresh_token}"
        )