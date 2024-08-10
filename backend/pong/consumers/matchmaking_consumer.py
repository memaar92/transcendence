import json
import logging
import redis
from ..services import redis_service as rs
from enum import Enum, auto
from pong.matchmaking.MatchHandler import MatchHandler
from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.exceptions import SuspiciousOperation

logger = logging.getLogger("PongConsumer")

redis_instance = redis.StrictRedis(host='redis', port=6379, db=0)

class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['user'].id
        if self.user_id is None:
            await self.close()
            logger.error("User not authenticated")
            return
        self.group_name = f"user_{self.user_id}"

        # Convert user_id to string for use in Redis
        self.user_id = str(self.user_id)

        # Add user to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.reconnect_to_game()

    async def disconnect(self, close_code):
        if self.user_id is None:
            return
        # Remove user from group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        self.remove_from_queue()

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
        if data["match_type"] == "online" and data["action"] == "join":
            await self.join_queue()

    async def remove_from_queue(self):
        redis_instance.lrem("matchmaking_queue", 0, self.user_id)

    async def join_queue(self):
        redis_instance.rpush("matchmaking_queue", self.user_id)
        await self.check_queue()

    async def check_queue(self):
        queue_length = redis_instance.llen("matchmaking_queue")
        logger.info(f"Queue length: {queue_length}")
        if queue_length >= 2:
            player1_id = redis_instance.lpop("matchmaking_queue")
            player2_id = redis_instance.lpop("matchmaking_queue")
            # Decode bytes to strings
            player1_id = player1_id.decode('utf-8')
            player2_id = player2_id.decode('utf-8')
            logger.info(f"Match found: {player1_id} vs {player2_id}")
            game_id = await self.create_game(player1_id, player2_id)
            await self.notify_players(game_id, player1_id, player2_id)
            # await self.game_assigned({'game_id': game_id})

    async def create_game(self, player1_id, player2_id):
        game_id = f"game_{player1_id}_{player2_id}"
        logger.info(f"Creating game: {game_id}")
        redis_instance.set(f"game:{game_id}:state", json.dumps({'player1': player1_id, 'player2': player2_id, 'state': 'new'}))
        return game_id

    async def notify_players(self, game_id, player1_id, player2_id):
        logger.info(f"Notifying players: {player1_id} and {player2_id}")
        await self.channel_layer.group_send(
            f"user_{player1_id}",
            {
                'type': 'match_assigned',
                'game_id': game_id
            }
        )
        await self.channel_layer.group_send(
            f"user_{player2_id}",
            {
                'type': 'match_assigned',
                'game_id': game_id
            }
        )

    async def match_assigned(self, event):
        logger.info(f"Game assigned: {event['game_id']}")
        await self.send(text_data=json.dumps({
            'state': 'match_assigned',
            'game_id': event['game_id']
        }))

    # TEST FUNCTION FOR RECONNECTING TO GAME
    async def reconnect_to_game(self):
        current_match = redis_instance.get(f"user:session:{self.user_id}:last_match_id")
        logger.info(f"Reconnecting to game: {current_match}")
        if current_match:
            current_match = current_match.decode('utf-8')
            logger.info(f"Current match: {current_match}")
            does_match_exist = redis_instance.exists(f"game:{current_match}:state")
            logger.info(f"Match exists: {does_match_exist}")
            if does_match_exist:
                await self.send(text_data=json.dumps({
                    'state': 'reconnect',
                    'game_id': current_match
                }))
