from channels.generic.websocket import AsyncWebsocketConsumer
from pong.match_tournament.match_session_handler import MatchSessionHandler
from pong.match_tournament.data_managment import User
import json
import logging

logger = logging.getLogger("PongConsumer")

class MatchmakingConsumer(AsyncWebsocketConsumer):
    _user_connections = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.group_name = None

    async def connect(self):
        self.user_id = self.scope['user'].id

        if self.user_id is None:
            await self.close()
            logger.error("User not authenticated")
            return

        self.group_name = f"user_{self.user_id}"

        # Add user to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Increment the connection count for the user
        if self.user_id in self._user_connections:
            self._user_connections[self.user_id] += 1
        else:
            self._user_connections[self.user_id] = 1

        await self.accept()

        current_match_id = User.get_user_match_id(self.user_id)
        if current_match_id and not User.is_user_connected_to_match(self.user_id, current_match_id):
            await self.send(text_data=json.dumps({
                'type': 'match_assigned',
                'match_id': current_match_id
            }))
    
    async def disconnect(self, close_code):
        if self.user_id is None:
            return
        
        # Decrement the connection count for the user
        if self.user_id in self._user_connections:
            self._user_connections[self.user_id] -= 1
            if self._user_connections[self.user_id] == 0:
                del self._user_connections[self.user_id]
                MatchSessionHandler.remove_from_matchmaking_queue(self.user_id)

                # Remove user from the group only when all connections are closed
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
            else:
                logger.info(f"User {self.user_id} still has {self._user_connections[self.user_id]} open connections")
        else:
            logger.error("User not found in user_connections")

    async def receive(self, text_data: str):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON")
            return

        if data.get("type") == "matchmaking":
            await self._handle_matchmaking_request(data)
        elif data.get("type") == "tournament":
            await self._handle_tournament_request(data)
        else:
            logger.error("Invalid request type")
            

    async def _handle_matchmaking_request(self, data: dict) -> None:
        if data.get("request") == "match":
            if data.get("match_type") == "online":
                await MatchSessionHandler.add_to_matchmaking_queue(self.user_id)
            elif data.get("match_type") == "local":
                await MatchSessionHandler.create_local_match(self.user_id)
            else:
                logger.error("Invalid match type")

    async def _handle_tournament_request(self, data: dict) -> None:
        if data.get("request") == "create":
            await self._create_tournament(data)
        elif data.get("request") == "register":
            await self._register_for_tournament(data)
        elif data.get("request") == "unregister":
            await self._unregister_from_tournament(data)
        elif data.get("request") == "start":
            await self._start_tournament(data)

    async def _send_connect_to_match_message(self, match_id: str) -> None:
        logger.debug(f"Sending connect to match message for match {match_id}")
        await self.send(text_data=json.dumps({
            'type': 'match_assigned',
            'match_id': match_id
        }))


    async def match_assigned(self, event):
        '''Handle the match_assigned message'''
        logger.debug(f"Received match_assigned event: {event}")
        match_id = event['match_id']
        await self.send(text_data=json.dumps({
            'type': 'match_assigned',
            'match_id': match_id
        }))