from authentication.utils import get_tokens_for_user
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from account.models import AccountUser
from rest_framework_simplejwt.tokens import RefreshToken
from ..conf.google import GoogleOAuth
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GoogleLoginURLView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        google_ = GoogleOAuth()
        return Response({"url": google_.get_auth_url()})
    
class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info("The redirect from google is recieved")
        code = request.GET.get("code")

        google_ = GoogleOAuth()

        if not code:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=google_failed")

        token_data = google_.exchange_code(code)
        access_token = token_data.get("access_token")

        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=google_failed")

        userinfo_response = google_.get_user_info(access_token)

        userinfo   = userinfo_response
        email      = userinfo.get("email")
        first_name = userinfo.get("given_name", "")
        last_name  = userinfo.get("family_name", "")


        if not email:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=no_email")

        user, _ = AccountUser.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": email.split("@")[0],
                        "first_name":first_name,
                        "last_name":last_name,
                        "is_active": True,
                        "is_verified": True,    # Google already verified email
                        "registration_method": AccountUser.RegistrationMethod.GOOGLE
                    }
                )
        logger.info("the user is created %s", user.id)
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
            f"?access={str(access_token)}"
            f"&refresh={str(refresh_token)}"
            f"&user_id={str(user.id)}"
        )