from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/live_chat/$", consumers.ChatConsumer.as_asgi()),
]
