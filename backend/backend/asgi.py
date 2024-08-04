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

import pong.routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from pong.middleware import jwt_auth_middleware_stack


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": jwt_auth_middleware_stack(
        AuthMiddlewareStack(
            URLRouter(
                pong.routing.websocket_urlpatterns
            )
        ),
    )
})
