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
from jsonschema import ValidationError
from django.conf import settings
from pong.schemas.matchmaking_schema import (
    ActiveConnection,
    QueueRegister,
    QueueUnregister,
    QueueIsRegistered,
    LocalMatchCreate,
    TournamentCreate,
    TournamentRegister,
    TournamentUnregister,
    TournamentStart,
    TournamentCancel,
    TournamentGetOpen
)

logger = logging.getLogger("matchmaking_consumer")

RATE_LIMIT_GET_REQUESTS = 0.4 # Rate limit for get requests in seconds

class MatchmakingConsumer(AsyncWebsocketConsumer):
    _user_connections = {} # Keep track of user connections the active connection(browser tab) for each user
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

        await self._update_active_connection()

        # Check if the user is already connected to a match and offer to reconnect
        current_match_id = User.get_user_match_id(self.user_id)
        if current_match_id and not User.is_user_connected_to_match(self.user_id, current_match_id):
            opponent = User.get_opponent_user_id(self.user_id, current_match_id)
            await self.send(text_data=json.dumps({
                'type': 'match_in_progress',
                'match_id': current_match_id,
                'opponent': opponent
            }))
    
    async def disconnect(self, close_code):
        if self.user_id is None:
            return
        
        # Remove the connection from the user's active connections
        await self._remove_connection()

        if self.user_id in self._user_connections and len(self._user_connections[self.user_id]["connections"]) == 0:
            logger.info(f"User {self.user_id} has no open connections")
            try:
                MatchSessionHandler.remove_from_matchmaking_queue(self.user_id)
            except ValueError as e:
                pass # Ignore errors when removing user from matchmaking queue
            try:
                await TournamentSessionHandler.remove_user_from_all_inactive_tournaments(self.user_id)
            except ValueError as e:
                pass # Ignore errors when removing user from tournaments

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
        
        message_type = data.get("type")

        try:
            if message_type == await ActiveConnection.get_type():
                ActiveConnection(**data)
                await self._update_active_connection()
            elif message_type == await QueueRegister.get_type():
                QueueRegister(**data)
                await self._queue_register()
            elif message_type == await QueueUnregister.get_type():
                QueueUnregister(**data)
                await self._queue_unregister()
            elif message_type == await QueueIsRegistered.get_type():
                QueueIsRegistered(**data)
                await self._queue_is_registered()
            elif message_type == await LocalMatchCreate.get_type():
                LocalMatchCreate(**data)
                await self._local_match_create()
            elif message_type == await TournamentCreate.get_type():
                msg = TournamentCreate(**data)
                await self._tournament_create(msg)
            elif message_type == await TournamentRegister.get_type():
                msg = TournamentRegister(**data)
                await self._tournament_register(msg)
            elif message_type == await TournamentUnregister.get_type():
                msg = TournamentUnregister(**data)
                await self._tournament_unregister(msg)
            elif message_type == await TournamentStart.get_type():
                msg = TournamentStart(**data)
                await self._tournament_start(msg)
            elif message_type == await TournamentCancel.get_type():
                msg = TournamentCancel(**data)
                await self._tournament_cancel(msg)
            elif message_type == await TournamentGetOpen.get_type():
                msg = TournamentGetOpen(**data)
                await self._tournament_get_open(msg)
            else:
                logger.error(f"Invalid message type: {message_type}")
        except ValidationError as e:
            logger.error(f"Invalid message data: {e}")
        except Exception as e:
            logger.error(f"Error processing message of type {message_type}: {e}")

    ###################################################################
    #   Functions to handle and track active connections for a user   #
    ###################################################################

    async def _update_active_connection(self) -> None:
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

    def _is_active_connection(self) -> bool:
        '''Check if the current connection is the active connection (Current tab in the browser)'''
        return self._user_connections[self.user_id]["active"] == self.channel_name

    async def remote_match_ready(self, event):
        '''Handle the remote_match_ready message'''

        # Check if the current connection is the active connection (Current tab in the browser)
        if not self._is_active_connection():
            return

        match_id = event['match_id']
        await self.send(text_data=json.dumps({
            'type': 'remote_match_ready',
            'match_id': match_id
        }))

    async def tournament_cancelled(self, event):
        '''Handle the tournament_cancelled message'''
        logger.debug(f"Received tournament_cancelled event: {event}")
        await self.send(text_data=json.dumps({
            'type': 'tournament_cancelled'
        }))

    async def tournament_starting(self, event):
        '''Handle the tournament_starting message'''

        # Check if the current connection is the active connection (Current tab in the browser)
        if not self._is_active_connection():
            return

        logger.debug(f"Received tournament_starting event: {event}")
        await self.send(text_data=json.dumps({
            'type': 'tournament_starting'
        }))

    async def tournament_canceled(self, event):
        '''Handle the tournament_canceled message'''

        # Check if the current connection is the active connection (Current tab in the browser)
        if not self._is_active_connection():
            return

        logger.debug(f"Received tournament_canceled event: {event}")
        await self.send(text_data=json.dumps({
            'type': 'tournament_canceled'
        }))

    async def tournament_finished(self, event):
        '''Handle the tournament_finished message'''

        # Check if the current connection is the active connection (Current tab in the browser)
        if not self._is_active_connection():
            return

        logger.debug(f"Received tournament_finished event: {event}")
        await self.send(text_data=json.dumps(event))

    ###################################
    #    Matchmaking message handlers #
    ###################################

    async def _queue_register(self) -> None:
        '''Register user for matchmaking'''
        try:
            await MatchSessionHandler.add_to_matchmaking_queue(self.user_id)
            await self._send_success_message('queue_registered')
        except ValueError as e:
            logger.error(f"Failed to register for matchmaking: {e}")
            await self._send_failure_message('queue_registered', str(e))

    async def _queue_unregister(self) -> None:
        '''Unregister user from matchmaking'''
        try:
            MatchSessionHandler.remove_from_matchmaking_queue(self.user_id)
            await self._send_success_message('queue_unregistered')
        except ValueError as e:
            logger.error(f"Failed to unregister from matchmaking: {e}")
            await self._send_failure_message('queue_unregistered', str(e))

    async def _queue_is_registered(self) -> None:
        '''Check if user is registered for matchmaking'''
        is_registered = MatchmakingQueue.is_user_registered(self.user_id)
        if is_registered:
            await self._send_success_message('queue_is_registered')
        else:
            await self._send_failure_message('queue_is_registered', None)

    async def _local_match_create(self) -> None:
        '''Create a local match'''
        try:
            await MatchSessionHandler.create_local_match(self.user_id)
            await self._send_success_message('local_match_created')
        except ValueError as e:
            logger.debug(f"Failed to create local match: {e}")
            await self._send_failure_message('local_match_created', str(e))


    ###################################
    #   Tournament message handlers   #
    ###################################

    async def _tournament_create(self, msg: TournamentCreate) -> None:
        '''Create a tournament'''
        try:
            tournament_id = TournamentSessionHandler.create_online_tournament_session(self.user_id, msg.name, msg.max_players)
            self.send(text_data=json.dumps({
                'tournament_created': True,
                'tournament_id': tournament_id.get_id()
            }))
        except ValueError as e:
            logger.error(f"Failed to create tournament: {e}")
            await self._send_failure_message('tournament_created', str(e))

    async def _tournament_register(self, msg: TournamentRegister) -> None:
        '''Register for a tournament'''
        try:
            TournamentSessionHandler.add_user_to_tournament(msg.tournament_id, self.user_id)
            await self._send_success_message('tournament_registered')
        except ValueError as e:
            logger.error(f"Failed to register for tournament: {e}")
            await self._send_failure_message('tournament_registered', str(e))

    async def _tournament_unregister(self, msg: TournamentUnregister) -> None:
        '''Unregister from a tournament'''
        try:
            await TournamentSessionHandler.remove_user_from_tournament(msg.tournament_id, self.user_id)
            await self._send_success_message('tournament_unregistered')
        except ValueError as e:
            logger.error(f"Failed to unregister from tournament: {e}")
            await self._send_failure_message('tournament_unregistered', str(e))
    
    async def _tournament_start(self, msg: TournamentStart) -> None:
        '''Start a tournament'''
        try:
            # Run the start_tournament method in its own asyncio task
            asyncio.create_task(self._start_tournament_task(msg.tournament_id))
            await self._send_success_message('tournament_started')
        except ValueError as e:
            logger.error(f"Failed to start tournament: {e}")
            await self._send_failure_message('tournament_started', str(e))

    async def _start_tournament_task(self, tournament_id: str) -> None:
        '''Start a tournament in a separate task'''
        await TournamentSessionHandler.start_tournament(self.user_id, tournament_id)


    async def _tournament_cancel(self, msg: TournamentCancel) -> None:
        '''Cancel a tournament'''
        try:
            await TournamentSessionHandler.request_cancel_tournament(self.user_id, msg.tournament_id)
            await self._send_success_message('tournament_cancelled')
        except ValueError as e:
            logger.error(f"Failed to cancel tournament: {e}")
            await self._send_failure_message('tournament_cancelled', str(e))

    async def _tournament_get_open(self, msg: TournamentGetOpen) -> None:
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
            'type': 'open_tournaments_list',
            'tournaments': tournament_data
        }))

    ###################################
    #      Helper functions           #
    ###################################

    async def _send_success_message(self, type: str) -> None:
        '''Send a success message to the user'''
        await self.send(text_data=json.dumps({
            f'{type}': True
        }))

    async def _send_failure_message(self, type: str, message: str) -> None:
        '''Send a failure message to the user'''
        response = {f'{type}': False}
        if message is not None:
            response['message'] = message
        await self.send(text_data=json.dumps(response))