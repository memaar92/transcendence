from channels.generic.websocket import AsyncWebsocketConsumer
from pong.match_tournament.match_session_handler import MatchSessionHandler
from pong.match_tournament.tournament_session_handler import TournamentSessionHandler
from pong.match_tournament.data_managment.tournaments import Tournaments
from pong.match_tournament.data_managment.user import User
from pong.match_tournament.data_managment.matchmaking_queue import MatchmakingQueue
import asyncio
import json
import logging
import time

logger = logging.getLogger("matchmaking_consumer")

RATE_LIMIT_GET_REQUESTS = 1.9 # Rate limit for get requests in seconds

class MatchmakingConsumer(AsyncWebsocketConsumer):
    _user_connections = {} # Keep track of user connections and active the active tab
    _last_request_time = {} # Keep track of the last request time for each user

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
            await TournamentSessionHandler.remove_user_from_all_inactive_tournaments(self.user_id)

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
        '''Handle matchmaking requests'''
        if data.get("request") == "register":
            if data.get("match_type") == "online":
                await MatchSessionHandler.add_to_matchmaking_queue(self.user_id)
            elif data.get("match_type") == "local":
                await MatchSessionHandler.create_local_match(self.user_id)
            else:
                logger.error("Invalid match type")
        elif data.get("request") == "unregister":
            MatchSessionHandler.remove_from_matchmaking_queue(self.user_id)
        elif data.get("request") == "is_registered":
            is_registered = MatchmakingQueue.is_user_registered(self.user_id)
            await self.send(text_data=json.dumps({
                'type': 'queue_status',
                'is_registered': is_registered
            }))

    async def _handle_tournament_request(self, data: dict) -> None:
        '''Handle tournament requests'''
        if data.get("request") == "create":
            await self._create_tournament(data)
        elif data.get("request") == "register":
            await self._register_for_tournament(data)
        elif data.get("request") == "unregister":
            await self._unregister_from_tournament(data)
        elif data.get("request") == "start":
            await self._start_tournament(data)
        elif data.get("request") == "get_open_tournaments":
            await self._get_open_tournaments(data)
        elif data.get("request") == "is_registered":
            is_registered = Tournaments.is_user_registered(self.user_id)
            tournament_id = Tournaments.get_user_tournament_id(self.user_id)
            tournament_name = Tournaments.get_name_by_id(tournament_id)
            await self.send(text_data=json.dumps({
                'type': 'tournament_status',
                'is_registered': is_registered,
                'tournament_id': tournament_id,
                'tournament_name': tournament_name
            }))


    ###################################################################
    #   Functions to handle and track active connections for a user   #
    ###################################################################

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
    #    (Event Handlers)        #
    #    Handle messages from    #
    #    the channel layer       #
    ##############################

    async def match_ready(self, event):
        '''Handle the match_ready message'''

        # Check if the user is in the _user_connections dictionary (Should always be the case)
        if self.user_id not in self._user_connections:
            logger.warning(f"User {self.user_id} not found in _user_connections")
            return

        # Check if the current connection is the active connection (Current tab in the browser)
        if self._user_connections[self.user_id]["active"] != self.channel_name:
            return

        logger.debug(f"Received match_ready event: {event}")
        match_id = event['match_id']
        await self.send(text_data=json.dumps({
            'type': 'match_ready',
            'match_id': match_id
        }))

    async def tournament_cancelled(self, event):
        '''Handle the tournament_cancelled message'''
        logger.debug(f"Received tournament_cancelled event: {event}")
        await self.send(text_data=json.dumps({
            'type': 'tournament_cancelled'
        }))

    ##############################
    #    Tournament Handlers     #
    ##############################

    async def _create_tournament(self, data: dict) -> None:
        '''Create a tournament'''
        try:
            name = data.get("name")
            max_players = data.get("max_players")
            tournament_id = TournamentSessionHandler.create_online_tournament_session(self.user_id, name, max_players)
        except ValueError as e:
            logger.error(f"Failed to create tournament: {e}")
            self._send_error_message(str(e))
            return
        
        await self.send(text_data=json.dumps({
            'type': 'tournament_created',
            'tournament_id': tournament_id.get_id()
        }))

    async def _register_for_tournament(self, data: dict) -> None:
        '''Register for a tournament'''
        try:
            tournament_id = data.get("tournament_id")
            TournamentSessionHandler.add_user_to_tournament(tournament_id, self.user_id)
        except ValueError as e:
            logger.error(f"Failed to register for tournament: {e}")
            self._send_error_message(str(e))
            return
        
        await self.send(text_data=json.dumps({
            'type': 'registered_for_tournament',
            'tournament_id': data.get("tournament_id")
        }))

    async def _unregister_from_tournament(self, data: dict) -> None:
        '''Unregister from a tournament'''
        tournament_id = data.get("tournament_id")
        if not tournament_id:
            self._send_error_message("Tournament id is required")
            return
        try:
            tournament = Tournaments.get(tournament_id)
            if tournament:
                await TournamentSessionHandler.remove_user_from_tournament(tournament_id, self.user_id)
            else:
                self._send_error_message(f"Tournament {tournament_id} not found")
        except ValueError as e:
            logger.error(f"Failed to unregister from tournament: {e}")
            self._send_error_message(str(e))
            return
        
        await self.send(text_data=json.dumps({
            'type': 'unregistered_from_tournament',
            'tournament_id': data.get("tournament_id")
        }))


    async def _start_tournament(self, data: dict) -> None:
        '''Start a tournament'''
        try:
            tournament_id = data.get("tournament_id")
            # Run the start_tournament method in its own asyncio task
            asyncio.create_task(self._start_tournament_task(tournament_id))
        except ValueError as e:
            logger.error(f"Failed to start tournament: {e}")
            await self._send_error_message(str(e))

    async def _start_tournament_task(self, tournament_id: str) -> None:
        '''Task to start a tournament'''
        try:
            await TournamentSessionHandler.start_tournament(self.user_id, tournament_id)
        except ValueError as e:
            logger.error(f"Failed to start tournament: {e}")
            await self._send_error_message(str(e))

    async def _get_open_tournaments(self, data: dict) -> None:
        '''Get all open tournaments'''
        current_time = time.time()
        last_request_time = self._last_request_time.get(self.user_id, 0)

        # Check if the user is rate limited
        if current_time - last_request_time < RATE_LIMIT_GET_REQUESTS:
            logger.info(f"Rate limit exceeded for user {self.user_id}")
            return

        # Update the last request time
        self._last_request_time[self.user_id] = current_time

        tournaments = Tournaments.get_open_tournaments()
        tournament_data = []
        for tournament in tournaments.values():
            tournament_data.append({
                'id': tournament.get_id(),
                'name': tournament.get_name(),
                'max_players': tournament.get_max_players(),
                'owner': tournament.get_owner_user_id(),
                'users': list(tournament.get_users()),
                'is_owner': self.user_id == tournament.get_owner_user_id()
            })
        
        await self.send(text_data=json.dumps({
            'type': 'tournaments',
            'tournaments': tournament_data
        }))

    async def _send_error_message(self, message: str) -> None:
        '''Send an error message to the user'''
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))