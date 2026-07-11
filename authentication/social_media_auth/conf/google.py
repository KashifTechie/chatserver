from .base_oauth import BaseOAuth
from .abstract_oauth import OAuthContract
from django.conf import settings
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class GoogleOAuth(BaseOAuth, OAuthContract):
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    
    @classmethod
    def get_auth_url(cls):
        logger.info("Generating Google OAuth URL")
        params = {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "online",
        }
        return f"{cls.AUTH_URL}?{urlencode(params)}"
    
    @classmethod
    def exchange_code(cls, code):
        logger.info("Exchanging code for tokens with Google")
        response = cls.post(cls.TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        return response.json()
    
    @classmethod
    def get_user_info(cls, access_token):
        logger.info("Fetching user info from Google")
        response = cls.get(
            cls.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json()