from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from account.models import AccountUser
from rest_framework_simplejwt.tokens import RefreshToken
from ..conf.x import XOAuth
from django.conf import settings
from taskmanagers.redis.redis_keys import x_oauth_code_verifier_key
from django.core.cache import cache
import secrets
from ...utils import get_tokens_for_user
import logging

logger = logging.getLogger(__name__)    


class XLoginURLView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info("Received request for X login URL")
        x_oauth = XOAuth()
        code_verifier, code_challenge = x_oauth.generate_code_challenge()
        state = secrets.token_urlsafe(16)
        logger.info(f"Generated code_verifier: {code_verifier}, code_challenge: {code_challenge}, state: {state}")
        # ✅ Store using state as key
        cache.set(x_oauth_code_verifier_key(state), code_verifier, timeout=300)
        return Response({"url": x_oauth.get_auth_url(code_challenge, state)})
    

class XCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info("The redirect from X is received")
        code = request.GET.get("code")
        state = request.GET.get("state")
        logger.info(f"Received code: {code}, state: {state} from X callback")
         # ✅ Retrieve using state as key
        code_verifier = cache.get(x_oauth_code_verifier_key(state))
        logger.info(f"Retrieved code_verifier from cache: {code_verifier} for state: {state}")
        x_oauth = XOAuth()

        if not code:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=x_failed")

        token_data = x_oauth.exchange_code(code, code_verifier)
        logger.info(f"Token data received from X: {token_data}")
        access_token = token_data.get("access_token")

        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/auth/success?error=x_failed")

        userinfo_response = x_oauth.get_user_info(access_token)

        userinfo   = userinfo_response
        x_id = userinfo.get("id")
        email      = userinfo.get("username")
        name       = userinfo.get("name", "")
        logger.info(f"x id returned {x_id} email returned {email} name returned {name}")
        # if not email:
        #     return redirect(f"{settings.FRONTEND_URL}/auth/success?error=no_x_email")

        user, _ = AccountUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": name,
                "is_active": True,
                "is_verified": True, 
                "registration_method": AccountUser.RegistrationMethod.X  # X already verified email
            }
        )
        logger.info(f"User {user.email} authenticated via X")

        tokens = get_tokens_for_user(user)
        access_token = tokens.get('access')
        refresh_token = tokens.get('refresh')
        return redirect(
            f"{settings.FRONTEND_URL}/auth/success"
            f"?access={str(access_token)}&refresh={str(refresh_token)}"
        )