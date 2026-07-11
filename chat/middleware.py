# chat/middleware.py

from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner
        self.jwt_auth = JWTAuthentication()

    @database_sync_to_async
    def get_user(self, token):
        validated_token = self.jwt_auth.get_validated_token(token)
        return self.jwt_auth.get_user(validated_token)

    async def __call__(self, scope, receive, send):
        logger.info("The socket request is received")

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        scope["user"] = AnonymousUser()

        if token:
            try:
                user = await self.get_user(token)
                logger.info("Authenticated user: %s", user.id)
                scope["user"] = user
            except Exception as e:
                logger.warning("JWT auth failed: %s", str(e))
                scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)