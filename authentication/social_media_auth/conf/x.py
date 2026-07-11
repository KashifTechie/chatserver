from asyncio.log import logger
import base64
import requests
import secrets
import hashlib
from django.conf import settings
from urllib.parse import urlencode
from .abstract_oauth import OAuthContract
from .base_oauth import BaseOAuth


class XOAuth(BaseOAuth, OAuthContract):
    TOKEN_URL = "https://api.x.com/2/oauth2/token"
    USER_INFO_URL = "https://api.x.com/2/users/me"
    AUTH_URL = "https://x.com/i/oauth2/authorize"

    @classmethod
    def generate_code_challenge(cls):
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).rstrip(b'=').decode('ascii')
        return code_verifier, code_challenge

    @classmethod
    def get_auth_url(cls, code_challenge, state):
        query_params = {
            "client_id": settings.X_OAUTH_CLIENT_ID,
            "redirect_uri": settings.X_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "tweet.read users.read offline.access",
            "state": state,  # CSRF protection
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{cls.AUTH_URL}?{urlencode(query_params)}"
    
    @classmethod
    def exchange_code(cls, code, code_verifier):
        response = cls.post(
            cls.TOKEN_URL,
            data={
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.X_OAUTH_REDIRECT_URI,
                "code_verifier": code_verifier,  # send original — X verifies against hash
            },
            headers={   
                        "authorization": f"Basic {base64.b64encode(f'{settings.X_OAUTH_CLIENT_ID}:{settings.X_OAUTH_CLIENT_SECRET}'.encode()).decode()}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
        )
        logger.info(f"X response: {response}")
        logger.info(f"type of response: {type(response)}")
        if type(response) == dict:
            logger.info("Response is already a dict")
            return response
        return response.json()
    
    @classmethod
    def get_user_info(cls, access_token):
        logger.info("Fetching user info from X")
        response = cls.get(
            cls.USER_INFO_URL,
            params={"user.fields": "id,name,username"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json().get("data", {})