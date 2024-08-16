"""
ASGI config for transcendence project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from pong.middleware import jwt_auth_middleware_stack

import live_chat.routing
import pong.routing

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": jwt_auth_middleware_stack(
        AuthMiddlewareStack(
            URLRouter(
                live_chat.routing.websocket_urlpatterns +
                pong.routing.websocket_urlpatterns
            )
        )
    ),
})
