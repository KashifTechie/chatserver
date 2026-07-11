"""
ASGI config for websockets project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""
import logging
logger = logging.getLogger(__name__)
import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
from chat.middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatserver.settings')
from chat.routing import websocket_urlpatterns
# application = get_asgi_application()

application = ProtocolTypeRouter({
    "http":get_asgi_application(),
    "websocket" : JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    )
})
logger.info("ASGI application configured successfully")