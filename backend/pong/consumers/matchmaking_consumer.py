from channels.generic.websocket import AsyncWebsocketConsumer
from pong.match_tournament.match_session_handler import MatchSessionHandler
from pong.match_tournament.tournament_session_handler import TournamentSessionHandler
from pong.match_tournament.data_managment import User
import json
import logging

logger = logging.getLogger("PongConsumer")

class MatchmakingConsumer(AsyncWebsocketConsumer):
    _user_connections = {} # Keep track of user connections and active the active tab

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

        await self.accept()

        await self._add_active_connection()

        # Check if the user is already connected to a match and offer to reconnect
        current_match_id = User.get_user_match_id(self.user_id)
        if current_match_id and not User.is_user_connected_to_match(self.user_id, current_match_id):
            await self.send(text_data=json.dumps({
                'type': 'match_in_progress',
                'match_id': current_match_id
            }))
    
    async def disconnect(self, close_code):
        if self.user_id is None:
            return
        
        # Remove the connection from the user's active connections
        await self._remove_connection()

        if self.user_id in self._user_connections and len(self._user_connections[self.user_id]["connections"]) == 0:
            logger.info(f"User {self.user_id} has no open connections")
            MatchSessionHandler.remove_from_matchmaking_queue(self.user_id)
            TournamentSessionHandler.remove_user_from_all_inactive_tournaments(self.user_id)

            # Remove user from the group only when all connections are closed
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        else:
            logger.info(f"User {self.user_id} has {self._user_connections[self.user_id]} open connections")


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
        elif data.get("active") == True:
            await self._add_active_connection()
            logger.info(f"User {self.user_id} set active connection to {self.channel_name}")
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

    async def _add_active_connection(self) -> None:
        '''Add a connection to the user's active connections'''
        # Create a new entry for the user if it does not exist yet
        if self.user_id not in self._user_connections:
            self._user_connections[self.user_id] = {
                "connections": set(),  # To store all connections
                "active": None         # To store the active connection
            }

        # Add this connection to the set of connections
        self._user_connections[self.user_id]["connections"].add(self.channel_name)
        self._user_connections[self.user_id]["active"] = self.channel_name
    
    async def _remove_connection(self) -> None:
        '''Remove a connection from the user's active connections'''

        # Remove this connection from the set of connections
        self._user_connections[self.user_id]["connections"].discard(self.channel_name)

        # Set the active connection to None if it is the active connection
        if self._user_connections[self.user_id]["active"] == self.channel_name:
            # Set the active connection to an arbitrary connection in the set if there are any connections left
            if len(self._user_connections[self.user_id]["connections"]) > 0:
                self._user_connections[self.user_id]["active"] = next(iter(self._user_connections[self.user_id]["connections"]))
            else:
                self._user_connections[self.user_id]["active"] = None

    ##############################
    #    Message Handlers        #
    ##############################

    async def match_assigned(self, event):
        '''Handle the match_assigned message'''

        # Check if the user is in the _user_connections dictionary (Should always be the case)
        if self.user_id not in self._user_connections:
            logger.warning(f"User {self.user_id} not found in _user_connections")
            return

        # Check if the current connection is the active connection (Current tab in the browser)
        if self._user_connections[self.user_id]["active"] != self.channel_name:
            return

        logger.debug(f"Received match_assigned event: {event}")
        match_id = event['match_id']
        await self.send(text_data=json.dumps({
            'type': 'match_assigned',
            'match_id': match_id
        }))
