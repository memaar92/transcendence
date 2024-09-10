import json
import logging
import redis
from ..services.redis_service.match import Match as rsMatch
from ..services.redis_service.user import User as rsUser
from ..services.redis_service.pub_sub_manager import PubSubManager as rsPubSub
from ..services.redis_service.matchmaking_queue import MatchmakingQueue as rsMatchmakingQueue
from ..services.redis_service.constants import REDIS_INSTANCE
from ..services.redis_service.constants import UserGameStatus
from ..matchmaking.matchmaker import MatchMaker
from enum import Enum, auto
from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import AsyncWebsocketConsumer


logger = logging.getLogger("PongConsumer")

class MatchmakingConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.group_name = None
        self.match_id = None
        self.pubsub = REDIS_INSTANCE.pubsub()

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
        logger.info(f"User {self.user_id} exists: {await rsUser.exists(self.user_id)}")
        if not await rsUser.exists(self.user_id):
            await rsUser.set_session_info(self.user_id, UserGameStatus.AVAILABLE, None)

        # Offers the user a reconnection to a match if they are not already in a game
        if not await rsUser.is_playing(self.user_id):
            if await self.is_match_in_progress() and await rsMatch.get_reconnect_attempts(await rsUser.get_match_id(self.user_id), self.user_id) < 3:
                await self.send_match_in_progress_message()

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
        if data.get("match_type") == "online":
            if data.get("action") == "join":
                await self.join_queue()
                await self.check_queue()
        # elif data["request"] == "reconnect":
        #     await self.reconnect_to_match()
        elif data.get("request") == "register":
            if await rsUser.is_playing(self.user_id):
                logger.info(f"User {self.user_id} is already in a game")
                await self.send(text_data=json.dumps({
                    'state': 'already_in_game'
                }))
            elif data.get("match_id"):
                try:
                    self.match_id = data.get("match_id")
                    await MatchMaker.register_user(data["match_id"], self.user_id)
                    logger.info(f"User {self.user_id} registered for match {data['match_id']}")
                    await rsPubSub.subscribe_to_channel(self.pubsub, f"{self.match_id}:registration", self.registration_handler)
                    if await rsMatch.Users.Registered.registration_complete(self.match_id):
                        await rsPubSub.publish_to_channel(f"{self.match_id}:registration", "registered")
                except MatchMaker.MatchError as e:
                    self.send(text_data=json.dumps({
                        'state': 'registration_error'
                    }))
                    logger.error(f"Error registering user: {e}")

        
    async def registration_handler(self, message):
        '''Handle messages from the registration channel'''
        print(f"Message: {message}")
        if message.get("type") != "message":
            return
        data = message.get("data")
        if not data:
            return
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        elif isinstance(data, int):
            data = str(data)
        if data == "registered":
            await self.send(text_data=json.dumps({
                'state': 'registered'
            }))
            await rsPubSub.unsubscribe_from_channel(self.pubsub, f"{self.match_id}:registration")
        elif data == "timeout":
            await self.send(text_data=json.dumps({
                'state': 'registration_timeout'
            }))
            logger.info(f"Match {self.match_id} registration timeout")
            await rsPubSub.unsubscribe_from_channel(self.pubsub, f"{self.match_id}:registration")
            await rsMatch.delete(self.match_id)
        elif data == "error":
            await self.send(text_data=json.dumps({
                'state': 'registration_error'
            }))
            await rsPubSub.unsubscribe_from_channel(self.pubsub, f"{self.match_id}:registration")
            await rsMatch.delete(self.match_id)



    async def remove_from_queue(self):
        '''Remove user from the matchmaking queue'''
        await rsMatchmakingQueue.remove_user(self.user_id)


    async def join_queue(self):
        '''Add user to the matchmaking queue'''
        logger.info(f"User {self.user_id} online status: {await rsUser.get_online_status(self.user_id)}")
        if await rsUser.get_online_status(self.user_id) == UserGameStatus.AVAILABLE:
            await rsMatchmakingQueue.add_user(self.user_id)
        

    async def check_queue(self) -> None:
        '''Check the matchmaking queue for available players'''
        queue_length = await rsMatchmakingQueue.get_queue_length()
        logger.info(f"Queue length: {queue_length}")
        if queue_length >= 2:
            player1_id = await rsMatchmakingQueue.pop_next_user()
            player2_id = await rsMatchmakingQueue.pop_next_user()
            if player1_id and player2_id:
                player1_id = player1_id
                player2_id = player2_id
                logger.info(f"Match found: {player1_id} vs {player2_id}")
                match_id = await self.create_match(player1_id, player2_id)
                await self.notify_players(match_id, player1_id, player2_id)
                await rsPubSub.subscribe_to_channel(REDIS_INSTANCE, f"MatchOutcome:{match_id}", self.match_outcome_handler)

        
    async def match_outcome_handler(self, message) -> None:
        '''Callback function to handle messages on the MatchOutcome channel'''
        print(f"Message: {message}")
        logger.info(f"Message: {message['channel'].decode('utf-8')}")
        await rsPubSub.unsubscribe_from_channel(REDIS_INSTANCE, f"{message['channel'].decode('utf-8')}", self.match_outcome_handler)
        # if message['type'] == 'message':
        #     print(f"Match outcome message: {message['data'].decode('utf-8')}")
                

    async def create_match(self, player1_id, player2_id):

        match_id = await MatchMaker.generate_match(player1_id, player2_id)
        logger.info(f"Creating match: {match_id}")
        
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
    # async def reconnect_to_match(self):
    #     current_match = await rsUser.get_match_id(self.user_id)
    #     logger.info(f"Reconnecting to match: {current_match}")
    #     if current_match:
    #         logger.info(f"Current match: {current_match}")
    #         does_match_exist = await rsMatch.is_alive(current_match)
    #         logger.info(f"Match exists: {does_match_exist}")
    #         reconnection_attempt = await rsMatch.get_reconnection_attempts(current_match, self.user_id)
    #         if does_match_exist:
    #             await self.send(text_data=json.dumps({
    #                 'state': 'reconnect',
    #                 'match_id': current_match
    #             }))

    async def is_match_in_progress(self):
        '''Check if the user is in a match that is in progress'''
        current_match = await rsUser.get_match_id(self.user_id)
        if current_match:
            return await rsMatch.is_alive(current_match)

    async def send_match_in_progress_message(self):
        '''Send a message to the user that a match is in progress, so they can reconnect'''
        await self.send(text_data=json.dumps({
            'state': 'match_in_progress',
            'match_id': await rsUser.get_match_id(self.user_id)
        }))