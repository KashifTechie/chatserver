from .base_oauth import BaseOAuth
from .abstract_oauth import OAuthContract
from django.conf import settings
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class LinkedInOAuth(BaseOAuth, OAuthContract):
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USER_INFO_URL = "https://api.linkedin.com/v2/me"
    EMAIL_URL = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"

    HEADERS = {
        "X-Restli-Version": "2.0.0"
    }

    @classmethod
    def get_auth_url(cls):
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "scope": "r_liteprofile r_emailaddress",
        }
        return f"{cls.AUTH_URL}?{urlencode(params)}"

    @classmethod
    def exchange_code(cls, code):
        response = cls.post(cls.TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        })

        data = response.json()
        if "access_token" not in data:
            logger.error(f"LinkedIn token exchange failed: {data}")

        return data

    @classmethod
    def get_user_info(cls, access_token):
        headers = {
            "Authorization": f"Bearer {access_token}",
            **cls.HEADERS
        }

        profile_response = cls.get(cls.USER_INFO_URL, headers=headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        email_response = cls.get(cls.EMAIL_URL, headers=headers)
        email_response.raise_for_status()
        email_data = email_response.json()

        email = None
        try:
            elements = email_data.get("elements") or []
            if elements:
                email = (elements[0].get("handle~") or {}).get("emailAddress")
        except Exception:
            logger.exception("Email parsing failed")

        name = " ".join(filter(None, [
            profile_data.get("localizedFirstName"),
            profile_data.get("localizedLastName")
        ]))

        return {
            "email": email,
            "name": name
        }