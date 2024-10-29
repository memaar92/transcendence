from typing import Optional, Callable
from ..game_logic.game_session import GameSession
from channels.layers import get_channel_layer
from usermanagement.models import CustomUser, Games
from asgiref.sync import sync_to_async
import asyncio
import logging
import time
from enum import Enum, auto
from uuid import uuid4
from django.conf import settings

logger = logging.getLogger("match")

MAX_RECONNECTIONS = settings.MATCH_CONFIG['max_reconnections']
MATCH_CONNECT_TIMEOUT = settings.MATCH_CONFIG['match_connect_timeout']
RECONNECT_TIMEOUT = settings.MATCH_CONFIG['reconnect_timeout']
MATCH_START_TIMER = settings.MATCH_CONFIG['match_start_timer']

TICK_RATE = settings.MATCH_CONFIG['tick_rate']

SCORE_LIMIT = settings.MATCH_CONFIG['score_limit']

class EndReason(Enum):
    DISCONNECT_TIMEOUT = auto()
    DISCONNECTED_TOO_MANY_TIMES = auto()
    MATCH_CONNECT_TIMEOUT = auto()
    DRAW = auto()
    SCORE = auto()
    LOCAL_MATCH_ABORTED = auto()

class MatchSession:
    def __init__(self, user_id_1: int, user_id_2: Optional[int], on_match_finished: Optional[Callable[[int, int], None]] = None):
        '''Initialize and start a match between two users'''
        self._match_id = str(uuid4())
        self._assigned_users = [user_id_1, user_id_2] if user_id_2 is not None else [user_id_1]
        self._blocked_users = set()
        self._connected_users = set()
        self._disconnect_count = {user_id_1: 0, user_id_2: 0} if user_id_2 is not None else {user_id_1: 0}
        self._player_mapping = {user_id_1: 0, user_id_2: 1} if user_id_2 is not None else {user_id_1: 0}
        self._is_local_match = user_id_2 is None
        self._score = {0: 0, 1: 0}
        self._game_session = GameSession(self._user_scored)
        self._main_loop_task: Optional[asyncio.Task] = asyncio.create_task(self._main_loop())
        self._on_match_finished = on_match_finished
        self._on_match_finished_user_callbacks = {user_id_1: None, user_id_2: None} if user_id_2 is not None else {user_id_1: None}
        self._tick_speed = 1 / TICK_RATE
        self._is_match_running = False
        self._stop_requested = False
        self._channel_layer = get_channel_layer()
        self._is_game_stopped = True

    def __del__(self):
        '''Destructor'''
        logger.debug(f"Deleted match session {self._match_id}")

    async def _main_loop(self) -> None:
        '''Main loop of the match'''
        last_time = time.time()
        while not self._stop_requested:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            if not self._is_match_running:
                await self._monitor_match_start()
                self._is_match_running = True
            if self._is_game_stopped:
                await self._start_timer()
                self._is_game_stopped = False
                # Reset last_time after the timer to avoid large delta_time
                last_time = time.time()
            if self.is_every_user_connected() and not self._stop_requested:
                await self._game_session.calculate_game_state(delta_time)
                await self._send_position_update()
            if not self._stop_requested:
                await asyncio.sleep(self._tick_speed)

    async def _end_match(self, reason: EndReason) -> None:
        '''End the match'''
        self._stop_requested = True
        
        # Add a small delay to ensure all messages before the end message are sent
        await asyncio.sleep(0.1)

        logger.debug(f"Ending match {self._match_id}")
        winner = None
        if reason == EndReason.DISCONNECT_TIMEOUT:
            winner = self._connected_users.pop()
            self._score[self._player_mapping[winner]] = SCORE_LIMIT
            await self._match_finished(self._match_id, winner)
            winner = self._player_mapping[winner]
            logger.debug("Match ended due to disconnect timeout")
        elif reason == EndReason.MATCH_CONNECT_TIMEOUT:
            await self._match_finished(self._match_id, None)
            logger.debug("Match ended due to timeout")
        elif reason == EndReason.DRAW:
            self._score[0] = 0
            self._score[1] = 0
            await self._match_finished(self._match_id, None)
            logger.debug("Match ended due to timeout and draw")
        elif reason == EndReason.DISCONNECTED_TOO_MANY_TIMES:
            logger.debug("Match ended due to too many disconnects")
            logger.debug(f"Connected users: {self._connected_users}")
            winner = self._connected_users.pop()
            self._score[self._player_mapping[winner]] = SCORE_LIMIT
            await self._match_finished(self._match_id, winner)
            winner = self._player_mapping[winner]
        elif reason == EndReason.SCORE:
            winner = max(self._score, key=self._score.get)
            await self._match_finished(self._match_id, winner)
            logger.debug("Match ended due to score")
        elif reason == EndReason.LOCAL_MATCH_ABORTED:
            await self._match_finished(self._match_id, None, False)
            logger.debug("Match ended due to local match abort")
        else:
            logger.error("Invalid end reason")

        if winner is not None:
            if self._is_local_match:
                if winner == 1:
                    loser = 0
                else:
                    loser = 1
            else:
                loser = self._userID_to_playerID(self.get_opponent_user_id(self._playerID_to_userID(winner)))
        else:
            loser = None

        # Call the MatchConsumer to disconnect the users
        for user_id, callback in self._on_match_finished_user_callbacks.items():
            if callback is not None:
                await callback(winner, loser)

        # Stop the main loop
        self._main_loop_task.cancel()
        try:
            await self._main_loop_task
        except asyncio.CancelledError:
            pass

        # Delete itself
        del self

    async def _match_finished(self, match_id: str, winner: Optional[int], write_to_db: bool = True) -> None:
        '''Callback when the match is finished'''
        logger.info(f"Match {match_id} finished, winner: {winner}")
        if write_to_db and not self._is_local_match:
            try:
                assigned_users = self._assigned_users
                home_user = await sync_to_async(CustomUser.objects.get)(id=assigned_users[0])
                visitor_user = await sync_to_async(CustomUser.objects.get)(id=assigned_users[1])

                game = Games(
                    home_id=home_user,
                    visitor_id=visitor_user,
                    home_score=self._score[0],
                    visitor_score=self._score[1]
                )

                await sync_to_async(game.save)()
                logger.info(f"Game saved with ID: {game.id}")
            except Exception as e:
                logger.error(f"Error saving game to database: {e}")

        if self._on_match_finished is not None:
            if winner is not None:
                winner_user_id = self._playerID_to_userID(winner)
            else:
                winner_user_id = None
            if asyncio.iscoroutinefunction(self._on_match_finished):
                await self._on_match_finished(match_id, winner_user_id)
            else:
                self._on_match_finished(match_id, winner_user_id)

    #############################
    #      Timer functions      #
    #############################

    async def _monitor_disconnect_timeout(self, user_id: int) -> None:
        '''Monitor the disconnect timeout'''
        try:
            await asyncio.wait_for(self._wait_for_user_reconnect(user_id), timeout=RECONNECT_TIMEOUT)
            logger.debug(f"User {user_id} reconnected")
        except asyncio.TimeoutError:
            logger.debug(f"User {user_id} did not reconnect in time")
            self._blocked_users.add(user_id)
            if not self._is_local_match:
                if self._connected_users: # If there is still a user connected he wins
                    await self._end_match(EndReason.DISCONNECT_TIMEOUT)
                elif len(self._assigned_users) == len(self._blocked_users): # If all users are blocked (Did not reconnect in time) it's a draw
                    await self._end_match(EndReason.DRAW)
            else:
                await self._end_match(EndReason.LOCAL_MATCH_ABORTED) # If it's a local match, end it

    async def _wait_for_user_reconnect(self, user_id: int) -> None:
        '''Wait for a user to reconnect'''
        while user_id not in self._connected_users:
            await asyncio.sleep(0.1)

    async def _monitor_match_start(self) -> None:
        '''Monitor the start of the match, will end the match if not all users connect in time'''
        if self._stop_requested:
            return
        try:
            await asyncio.wait_for(self._wait_for_users_to_connect(), timeout=MATCH_CONNECT_TIMEOUT)
            logger.debug("All users connected, match starting.")
        except asyncio.TimeoutError:
            logger.debug("Match start timeout, not all users connected.")
            await self._end_match(EndReason.MATCH_CONNECT_TIMEOUT)

    async def _wait_for_users_to_connect(self) -> None:
        '''Wait until both users are connected'''
        while len(self._connected_users) < len(self._assigned_users):
            await asyncio.sleep(0.1)

    async def _send_initialisation_messages(self) -> None:
        '''Send the necessary messages to the users'''
        await self._send_user_mapping()
        await self._send_position_update()
        await self._send_player_scores_message(self._score[0], self._score[1])

    #############################
    #    Connection functions   #
    #############################

    async def connect_user(self, user_id: int, on_match_finished: Callable[[], None] = None) -> None:
        '''Connect a user to the match'''
        if self._stop_requested:
            logger.error(f"Match {self._match_id} has already ended")
            return
        if user_id not in self._assigned_users:
            logger.error(f"User {user_id} not assigned to the match")
            return
        self._connected_users.add(user_id)
        self._on_match_finished_user_callbacks[user_id] = on_match_finished
        logger.debug(f"User {user_id} connected to match {self._match_id}")

        await self._send_initialisation_messages()

        # Check if a blocked user exists and end the match if only one user is left
        if len(self._blocked_users) == 1:
            await self._end_match(EndReason.DISCONNECT_TIMEOUT)
        
        # Restart the game start timer
        self._is_game_stopped = True

    async def disconnect_user(self, user_id: int) -> bool:
        '''Disconnect a user from the match'''
        logger.debug(f"Disconnecting user {user_id} from match {self._match_id}")
        try:
            self._connected_users.remove(user_id)
            self._on_match_finished_user_callbacks[user_id] = None
            logger.debug(f"Removed user {user_id} from connected users")
        except KeyError:
            logger.error(f"Cannot disconnect user {user_id} from match {self._match_id} as they are not connected to it")
            return False
        if self._is_local_match:
            await self._end_match(EndReason.LOCAL_MATCH_ABORTED)
            return True
        await self._send_user_disconnected_message(user_id)
        self._disconnect_count[user_id] += 1
        if self._disconnect_count[user_id] >= MAX_RECONNECTIONS:
            await self._end_match(EndReason.DISCONNECTED_TOO_MANY_TIMES)
            return True
        logger.debug(f"Disconnect count: {self._disconnect_count[user_id]}")
        await self._monitor_disconnect_timeout(user_id)
        return True

    #############################
    #    Game control functions #
    #############################

    async def update_player_direction(self, user_id: int, direction: str, player_id: int) -> None:
        '''Update the direction of a player'''
        if user_id not in self._assigned_users:
            logger.error(f"User {user_id} not assigned to the match")
            return
        if user_id not in self._connected_users:
            logger.error(f"User {user_id} not connected to the match")
            return
        
        # Update the direction of the player, depending on the match type
        if self._is_local_match:
            self._game_session.update_player_direction(player_id, direction)
        else:
            self._game_session.update_player_direction(self._player_mapping[user_id], direction)


    async def _start_timer(self) -> None:
        '''Start the timer before the game starts'''
        if self._stop_requested:
            return
        for seconds in range(MATCH_START_TIMER, -1, -1):
            await self._send_start_timer_update_message(seconds)
            await asyncio.sleep(1)
        logger.debug("Game timer ended, starting game")

    #############################
    # Callbacks from the game   #
    #############################

    async def _user_scored(self, player_id: int) -> None:
        '''Callback when a player scores'''
        logger.debug(f"Player {player_id} scored")
        self._score[player_id] += 1
        await self._send_player_scores_message(self._score[0], self._score[1])
        
        if self._score[player_id] >= SCORE_LIMIT:
            await self._end_match(EndReason.SCORE)

    #############################
    #    Message sending        #
    #############################

    async def _send_user_mapping(self) -> None:
        '''Send the user mapping to the users'''
        if self._stop_requested:
            return
        try:
            user_id_1 = self._assigned_users[0]
            user_id_2 = self._assigned_users[1] if not self._is_local_match else None
        except IndexError as e:
            # Handle the case where there are not enough users assigned
            logger.error(f"Error in _send_user_mapping: {e}")
            return
    
        message = {
            "type": "user_mapping",
            "is_local_match": self._is_local_match,
            "player1": user_id_1,
        }
    
        if not self._is_local_match:
            message["player2"] = user_id_2
    
        await self._channel_layer.group_send(self._match_id, message)

    async def _send_position_update(self) -> None:
        '''Send the position update to the users'''
        current_positions = self._game_session.to_bytearray()
        await self._channel_layer.group_send(self._match_id, {
            "type": "position_update",
            "data": current_positions
        })

    async def _send_user_disconnected_message(self, user_id: int) -> None:
        '''Send a disconnect message to the users'''
        await self._channel_layer.group_send(self._match_id, {
            "type": "user_disconnected",
            "user_id": user_id
        })

    async def _send_start_timer_update_message(self, time: int) -> None:
        '''Send a start timer update message to the users'''
        await self._channel_layer.group_send(self._match_id, {
            "type": "start_timer_update",
            "start_timer": time
        })

    async def _send_game_over_message(self, winner: int) -> None:
        '''Send a game over message to the users'''
        await self._channel_layer.group_send(self._match_id, {
            "type": "game_over",
            "data": winner
        })
    
    async def _send_player_scores_message(self, player1: int, player2: int) -> None:
        '''Send a player scores message to the users'''
        await self._channel_layer.group_send(self._match_id, {
            "type": "player_scores",
            "player1": player1,
            "player2": player2
        })

    #############################
    #    Utility functions      #
    #############################

    def is_user_assigned(self, user_id: int) -> bool:
        '''Check if a user is assigned to the match'''
        return user_id in self._assigned_users
    
    def is_user_connected(self, user_id: int) -> bool:
        '''Check if a user is connected to the match'''
        return user_id in self._connected_users
    
    def get_id(self) -> str:
        '''Get the match id'''
        return self._match_id
    
    def is_user_blocked(self, user_id: int) -> bool:
        '''Check if a user is blocked from the match'''
        return user_id in self._blocked_users
    
    def is_every_user_connected(self) -> bool:
        '''Check if all users are connected'''
        return len(self._assigned_users) == len(self._connected_users)
    
    def _playerID_to_userID(self, player_id: int) -> str:
        '''Convert a player id to a user id'''
        for user_id, p_id in self._player_mapping.items():
            if p_id == player_id:
                return user_id
        return None
    
    def _userID_to_playerID(self, user_id: int) -> str:
        '''Convert a user id to a player id'''
        return self._player_mapping[user_id]
    
    def get_opponent_user_id(self, user_id: int) -> str:
        '''Get the opponent user id'''
        for user in self._assigned_users:
            if user != user_id:
                return user
        return None