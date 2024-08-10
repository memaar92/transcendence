from django.urls import re_path
from .consumers.consumers import MatchmakingConsumer, GameSessionConsumer

websocket_urlpatterns = [
    re_path(r"ws/pong/matchmaking/$", MatchmakingConsumer.as_asgi()),
    re_path(r"ws/pong/game/(?P<game_id>[^/]+)/$", GameSessionConsumer.as_asgi()),
]
