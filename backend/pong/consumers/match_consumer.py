import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from ..match.match_session import MatchSession
from ..data_managment.matches import Matches
from ..data_managment.user import User
from jsonschema import ValidationError
from django.conf import settings
from ..schemas.match_schema import (
    PlayerInput
)

import logging
logger = logging.getLogger("match_consumer")

class MatchConsumer(AsyncWebsocketConsumer):

    def __init__(self):
        super().__init__()
        self._match_id: str = None
        self._user_id: int = None
        self._group_name: str = None
        self._match_session: MatchSession = None
        self._connection_established: bool = False

    async def connect(self) -> None:
        '''Establish the WebSocket connection'''

        # Extracting the match_id from the URL route parameters
        self._match_id = self.scope['url_route']['kwargs']['match_id']

        # Extracting the user_id from the scope
        self._user_id = self.scope["user"].id

        # Group name for the match
        self._group_name = f"match_{self._match_id}"

        # Check if the connection is valid
        if not await self.is_valid_connection(self._match_id, self._user_id):
            await self.close()
            logger.debug(f"User {self._user_id} is not allowed to connect to match {self._match_id}")
            return

        # Add the connection to the channel group for this match
        await self.channel_layer.group_add(self._match_id, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()
        self._connection_established = True

        self._match_session = Matches.get_match(self._match_id)
        await self._match_session.connect_user(self._user_id, self._match_session_is_finished_callback)


    async def disconnect(self, close_code: int) -> None:
        '''Disconnect the WebSocket connection'''

        logger.debug(f"Disconnect called for user {self._user_id} with close code {close_code}")

        # Run the disconnect logic only if the connection was established
        if not self._connection_established:
            logger.debug(f"Connection not established for user {self._user_id}, so not disconnecting")
            return
        self._connection_established = False

        await self.channel_layer.group_discard(self._match_id, self.channel_name)
        if self._match_session:
            asyncio.create_task(self._match_session.disconnect_user(self._user_id))
            self._match_session = None


    async def receive(self, text_data: str) -> None:
        '''Receive a message from the WebSocket connection'''
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON")
            return
        
        message_type = data.get("type")

        try:
            if message_type == await PlayerInput.get_type():
                try:
                    msg = PlayerInput(**data)
                    await self._match_session.update_player_direction(self._user_id, msg.direction, msg.player_id)
                except ValidationError as e:
                    logger.error(f"Invalid message data: {e}")
                except Exception as e:
                    logger.error(f"Failed to update player direction: {e}")
            else:
                logger.error(f"Invalid message type: {message_type}")
        except Exception as e:
            logger.error(f"Failed to process message: {e}")


    async def is_valid_connection(self, match_id: str, user_id: int) -> bool:
        '''Check if the connection is valid'''

        # User is not authenticated
        if self._user_id is None:
            logger.debug("User not authenticated")
            return False

        # No Match ID provided
        if self._match_id is None:
            logger.debug("Match ID not provided")
            return False
        
        # Match ID does not exist
        if not Matches.is_match_registered(self._match_id):
            logger.debug(f"Match {self._match_id} not found")
            return False

        # User is not part of the match
        if not Matches.is_user_assigned_to_match(self._match_id, self._user_id):
            logger.debug(f"User {self._user_id} is not part of match {self._match_id}")
            return False

        # # User is already connected to a match or tournament
        # if User.is_user_connected_to_match(self._user_id, self._match_id):
        #     logger.debug(f"User {self._user_id} is already connected to a match")
        #     return False
        
        # Is the user blocked to connect to the match
        if User.is_user_blocked(self._user_id, self._match_id):
            logger.debug(f"User {self._user_id} is blocked from connecting to match {self._match_id}")
            return False

        return True
    
    async def _match_session_is_finished_callback(self, winner: int, loser: int) -> None:
        '''Callback function for when the match session is finished'''
        await self._send_game_over_message(winner, loser)
        self._match_session = None
        await self.close()

    async def _send_game_over_message(self, winner: int, loser: int) -> None:
        '''Send a game over message to the users'''
        logger.debug(f"Sending game over message to users")
        await self.send(text_data=json.dumps({
            "type": "game_over",
            "winner": winner,
            "loser": loser
        }))


    ### Channel Layer Callbacks ###

    async def user_mapping(self, event) -> None:
        '''Send the user mapping to the user'''
        logger.info(f"User mapping: {event}")
        await self.safe_send(text_data=json.dumps(event))

    async def position_update(self, event) -> None:
        '''Send the position update to the user'''
        game_state_bytes = event.get("data")
        if game_state_bytes:
            await self.safe_send(bytes_data=game_state_bytes)

    async def user_connected(self, event) -> None:
        '''Send the user connected message to the user'''
        logger.debug(f"User {event} connected")
        if event.get("user_id") != self._user_id:
            return
        await self.safe_send(text_data=json.dumps(event))

    async def user_disconnected(self, event) -> None:
        '''Send the user disconnected message to the user'''
        logger.debug(f"User {event} disconnected")
        await self.safe_send(text_data=json.dumps(event))

    async def start_timer_update(self, event) -> None:
        '''Send the start timer update to the user'''
        await self.safe_send(text_data=json.dumps(event))

    async def player_scores(self, event) -> None:
        '''Send the player scores to the user'''
        await self.safe_send(text_data=json.dumps(event))

    async def safe_send(self, text_data: str = None, bytes_data: bytes = None) -> None:
        '''Send a message only if the connection is established'''
        if self._connection_established:
            try:
                if text_data is not None:
                    await self.send(text_data=text_data)
                elif bytes_data is not None:
                    await self.send(bytes_data=bytes_data)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
        else:
            logger.warning("Attempted to send message on closed connection")