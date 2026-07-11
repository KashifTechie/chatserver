from .base_oauth import BaseOAuth
from .abstract_oauth import OAuthContract
from django.conf import settings
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class FacebookOAuth(BaseOAuth, OAuthContract):
    TOKEN_URL = "https://graph.facebook.com/v12.0/oauth/access_token"
    USER_INFO_URL = "https://graph.facebook.com/me"
    AUTH_URL = "https://www.facebook.com/v12.0/dialog/oauth"

    @classmethod
    def get_auth_url(cls):
        params = {
            'client_id': settings.FACEBOOK_CLIENT_ID,
            'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
            'scope': 'email',
        }
        login_url = f"{cls.AUTH_URL}?{urlencode(params)}"
        logger.info(f"Generated Facebook OAuth URL: {login_url}")
        return login_url

    @classmethod
    def exchange_code(cls, code):
        response = cls.get(cls.TOKEN_URL, params={
            'client_id': settings.FACEBOOK_CLIENT_ID,
            'client_secret': settings.FACEBOOK_CLIENT_SECRET,
            'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
            'code': code,
        })
        return response.json()
    
    @classmethod
    def get_user_info(cls, access_token):
        response = cls.get(
            cls.USER_INFO_URL,
            params={'fields': 'id,name,email'},
            headers={'Authorization': f'Bearer {access_token}'}
        )
        return response.json()