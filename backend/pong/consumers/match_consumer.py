import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from pong.match_tournament.match_session_handler import MatchSessionHandler
from pong.match_tournament.match_session import MatchSession

import logging
logger = logging.getLogger("PongConsumer")

class MatchConsumer(AsyncWebsocketConsumer):

    def __init__(self):
        super().__init__()
        self._match_id = None
        self._user_id = None
        self._group_name = None
        self._match_session = None
        self._connection_established = False

    async def connect(self):
        # Extracting the match_id from the URL route parameters
        self._match_id = self.scope['url_route']['kwargs']['match_id']

        # Extracting the user_id from the scope
        self._user_id = self.scope["user"].id

        # Group name for the match
        self._group_name = f"match_{self._match_id}"

        # Check if the connection is valid
        if not self.is_valid_connection(self._match_id, self._user_id):
            await self.close()
            logger.info(f"User {self._user_id} is not allowed to connect to match {self._match_id}")
            return

        # Add the connection to the channel group for this match
        await self.channel_layer.group_add(self._match_id, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()
        self._connection_established = True

        self._match_session = MatchSessionHandler.get_match(self._match_id)
        await self._match_session.connect_user(self._user_id, self._match_session_is_finished_callback)

    async def disconnect(self, close_code):
        logger.debug(f"Disconnect called for user {self._user_id} with close code {close_code}")


        # Run the disconnect logic only if the connection was established
        if not self._connection_established:
            logger.info(f"Connection not established for user {self._user_id}, so not disconnecting")
            return

        await self._match_session.disconnect_user(self._user_id)

        await self.channel_layer.group_discard(self._match_id, self.channel_name)


    async def receive(self, text_data): # TODO: Implement this
        pass

    async def is_valid_connection(self, match_id, user_id):

        # User is not authenticated
        if self._user_id is None:
            logger.info("User not authenticated")
            return False
        
        # # Convert user_id to string for use in Redis
        # self._user_id = str(self._user_id)

        # No Match ID provided
        if self._match_id is None:
            logger.info("Match ID not provided")
            return False
        
        # # Match ID is not a string
        # if not isinstance(self._match_id, str):
        #     logger.info("Match ID is not a string")
        #     return False
        
        # Match ID does not exist
        if not MatchSessionHandler.get_match(self._match_id):
            logger.info(f"Match {self._match_id} not found")
            return False
        
        # User is already connected to a match or tournament
        if MatchSessionHandler.is_user_registered(self._user_id): # TODO: Add tournament check
            logger.info(f"User {self._user_id} is already connected to a match")
            return False

        # User is not part of the match
        if not MatchSessionHandler.get_match(self._match_id).is_user_assigned(self._user_id):
            logger.info(f"User {self._user_id} is not part of match {self._match_id}")
            return False

        # # Match is not in progress
        # if not MatchSessionHandler.get_match(self._match_id).is_in_progress():
        #     logger.info(f"Match {self._match_id} is not in progress")
        #     return False
        
        # # User has exceeded the maximum reconnect attempts
        # if await rsMatch.get_reconnect_attempts(self._match_id, self._user_id) >= MatchConsumer.MAX_RECONNECT_ATTEMPTS:
        #     logger.info(f"User {self._user_id} has exceeded the maximum reconnect attempts")
        #     return False

        return True
    
    async def _match_session_is_finished_callback(self):
        self._connection_established = False
        self.close()
        logger.info(f"Match {self._match_id} finished for user {self._user_id}")