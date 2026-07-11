from django.conf import settings
from django.shortcuts import redirect
from authentication.social_media_auth.conf.facebook import FacebookOAuth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from account.models import AccountUser
from ...utils import get_tokens_for_user
import logging

logger = logging.getLogger(__name__)


class FacebookLoginURLView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        facebook_oauth = FacebookOAuth()
        auth_url = facebook_oauth.get_auth_url()
        return Response({"auth_url": auth_url})
    

class FacebookCallbackView(APIView):

    permission_classes = [AllowAny]
    
    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=facebook_failed")

        facebook_oauth = FacebookOAuth()
        token_data = facebook_oauth.exchange_code(code)
        access_token = token_data.get("access_token")

        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=facebook_failed")

        user_info = facebook_oauth.get_user_info(access_token)
        email = user_info.get("email")
        name = user_info.get("name", "")

        if not email:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=no_facebook_email")

        user, _ = AccountUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": name.split()[0] if name else "",
                "last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                "is_active": True,
                "is_verified": True, 
                "registration_method": AccountUser.RegistrationMethod.Facebook
            }
        )

        tokens = get_tokens_for_user(user)
        access_token = tokens.get('access')
        refresh_token = tokens.get('refresh')
        
        return redirect(
            f"{settings.FRONTEND_URL}/auth/success"
            f"?access={str(access_token)}&refresh={str(refresh_token)}"
        )