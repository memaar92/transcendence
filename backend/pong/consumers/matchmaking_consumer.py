import json
import logging
import redis
from ..services import redis_service as rs
from ..utils.states import UserOnlineStatus
from enum import Enum, auto
from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import AsyncWebsocketConsumer


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

        # Set user default values in redis if not already set
        logger.info(f"User {self.user_id} exists: {await rs.User.exists(self.user_id)}")
        if not await rs.User.exists(self.user_id):
            await rs.User.set_session_info(self.user_id, UserOnlineStatus.ONLINE, None)

        if not await rs.User.is_playing(self.user_id):
            await self.reconnect_to_match()

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
            await self.check_queue()


    async def remove_from_queue(self):
        '''Remove user from the matchmaking queue'''
        await rs.MatchmakingQueue.remove_user(self.user_id)


    async def join_queue(self):
        '''Add user to the matchmaking queue'''
        logger.info(f"User {self.user_id} online status: {await rs.User.get_online_status(self.user_id)}")
        if await rs.User.get_online_status(self.user_id) == UserOnlineStatus.ONLINE:
            await rs.MatchmakingQueue.add_user(self.user_id)
        

    async def check_queue(self) -> None:
        '''Check the matchmaking queue for available players'''
        queue_length = await rs.MatchmakingQueue.get_queue_length()
        logger.info(f"Queue length: {queue_length}")
        if queue_length >= 2:
            player1_id = await rs.MatchmakingQueue.pop_next_user()
            player2_id = await rs.MatchmakingQueue.pop_next_user()
            if player1_id and player2_id:
                player1_id = player1_id
                player2_id = player2_id
                logger.info(f"Match found: {player1_id} vs {player2_id}")
                match_id = await self.create_match(player1_id, player2_id)
                await self.notify_players(match_id, player1_id, player2_id)

    async def create_match(self, player1_id, player2_id):
        match_id = f"match_{player1_id}_{player2_id}" # TODO: Change this to a unique id
        logger.info(f"Creating match: {match_id}")
        await rs.Match.initialize(match_id, [player1_id, player2_id])
        return match_id

    async def notify_players(self, match_id, player1_id, player2_id):
        logger.info(f"Notifying players: {player1_id} and {player2_id}")
        await self.channel_layer.group_send(
            f"user_{player1_id}",
            {
                'type': 'match_assigned',
                'match_id': match_id
            }
        )
        await self.channel_layer.group_send(
            f"user_{player2_id}",
            {
                'type': 'match_assigned',
                'match_id': match_id
            }
        )

    async def match_assigned(self, event):
        logger.info(f"Match assigned: {event['match_id']}")
        await self.send(text_data=json.dumps({
            'state': 'match_assigned',
            'match_id': event['match_id']
        }))

    # TEST FUNCTION FOR RECONNECTING TO MATCH
    async def reconnect_to_match(self):
        current_match = await rs.User.get_match_id(self.user_id)
        logger.info(f"Reconnecting to match: {current_match}")
        if current_match:
            logger.info(f"Current match: {current_match}")
            does_match_exist = await rs.Match.is_alive(current_match)
            logger.info(f"Match exists: {does_match_exist}")
            if does_match_exist:
                await self.send(text_data=json.dumps({
                    'state': 'reconnect',
                    'match_id': current_match
                }))
