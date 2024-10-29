from django.urls import re_path
from .consumers.match_consumer import MatchConsumer
from .consumers.matchmaking_consumer import MatchmakingConsumer

websocket_urlpatterns = [
    re_path(r"wss/pong/matchmaking/$", MatchmakingConsumer.as_asgi()),
    re_path(r"wss/pong/match/(?P<match_id>[^/]+)/$", MatchConsumer.as_asgi()),
]
