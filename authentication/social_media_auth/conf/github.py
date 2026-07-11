from .base_oauth import BaseOAuth
from .abstract_oauth import OAuthContract
from django.conf import settings
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class GitHubOAuth(BaseOAuth, OAuthContract):
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"
    USER_EMAILS_URL = "https://api.github.com/user/emails"
    AUTH_URL = "https://github.com/login/oauth/authorize"

    @classmethod
    def get_auth_url(cls):
        params = {
            'client_id': settings.GITHUB_OAUTH_CLIENT_ID,
            'redirect_uri': settings.GITHUB_OAUTH_REDIRECT_URI,
            'scope': 'user:email',

        }
        login_url = f"{cls.AUTH_URL}?{urlencode(params)}"
        logger.info(f"Generated GitHub OAuth URL: {login_url}")
        return login_url

    @classmethod
    def exchange_code(cls, code):
        response = cls.post(cls.TOKEN_URL, data={
            'code': code,
            'client_id': settings.GITHUB_OAUTH_CLIENT_ID,
            'client_secret': settings.GITHUB_OAUTH_CLIENT_SECRET,
            'redirect_uri': settings.GITHUB_OAUTH_REDIRECT_URI,
        }, headers={'Accept': 'application/json'})
        return response.json()
    
    
    @classmethod
    def get_user_info(cls, access_token):
        profile_response = cls.get(
            cls.USER_INFO_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        profile = profile_response.json()
        logger.info(f"GitHub profile response: {profile}")

        emails_response = cls.get(
            cls.USER_EMAILS_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        logger.info(f"GitHub emails response: {emails_response.json()}")

        emails = emails_response.json()
        primary_email = next(
            (e['email'] for e in emails if e.get('primary') and e.get('verified')),
            None
        )
        return {
            'email': primary_email,
            'name': profile.get('name') or profile.get('login'),
        }

