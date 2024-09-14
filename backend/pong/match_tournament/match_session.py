from typing import Optional, Callable
import asyncio
import logging
from enum import Enum, auto

logger = logging.getLogger("PongConsumer")

DISCONNECT_THRESHOLD = 3
MATCH_START_TIMEOUT = 10
RECONNECT_TIMEOUT = 10

TICK_RATE = 60

WINNING_SCORE = 3

class EndReason(Enum):
    DISCONNECT_TIMEOUT = auto()
    DISCONNECTED_TOO_MANY_TIMES = auto()
    MATCH_START_TIMEOUT = auto()
    SCORE = auto()

class MatchSession:
    def __init__(self, user1: str, user2: Optional[str], on_match_finished: Optional[Callable[[str], None]] = None):
        '''Initialize and start a match between two users'''
        self._id = str(id(self))  # Generating a unique id
        self._assigned_users = {user1, user2} if user2 is not None else {user1}
        self._connected_users = set()
        self._disconnect_count = {user1: 0, user2: 0} if user2 is not None else {user1: 0}
        self._player_mapping = {user1: "p1", user2: "p2"} if user2 is not None else {user1: "p1"}
        self._is_local_match = user2 is None
        self._score = {"player1": 0, "player2": 0}
        self._gamehandler = None
        self._main_loop_task: Optional[asyncio.Task] = asyncio.create_task(self._main_loop())
        self._on_match_finished = on_match_finished
        self._on_match_finished_user_callbacks = {user1: None, user2: None} if user2 is not None else {user1: None}
        self._tick_speed = 1 / TICK_RATE
        self._is_match_running = False

    async def _main_loop(self) -> None:
        '''Main loop of the match'''
        while True:
            if not self._is_match_running:
                await self._monitor_match_start()
                self._is_match_running = True
            # self._gamehandler.update()
            await self._send_game_state()
            await asyncio.sleep(self._tick_speed)

    async def _end_match(self, reason: EndReason) -> None:
        '''End the match'''
        if reason == EndReason.DISCONNECT_TIMEOUT:
            logger.info("Match ended due to disconnect")
        elif reason == EndReason.MATCH_START_TIMEOUT:
            logger.info("Match ended due to timeout")
        elif reason == EndReason.DISCONNECTED_TOO_MANY_TIMES:
            logger.info("Match ended due to too many disconnects")
        elif reason == EndReason.SCORE:
            logger.info("Match ended due to score")

        # Call the on_match_finished callback
        if self._on_match_finished is not None:
            await self._on_match_finished(self._id)

        # Call the MatchConsumer to disconnect the users
        for user_id, callback in self._on_match_finished_user_callbacks.items():
            if callback is not None:
                await callback()

        # Stop the main loop
        self._main_loop_task.cancel()
        try:
            await self._main_loop_task
        except asyncio.CancelledError:
            pass

        # Delete itself
        del self

    #############################
    #      Timer functions      #
    #############################

    async def _monitor_disconnect_timeout(self, user_id: str) -> None:
        '''Monitor the disconnect timeout'''
        try:
            await asyncio.wait_for(self._wait_for_user_reconnect(user_id), timeout=RECONNECT_TIMEOUT)
            logger.info(f"User {user_id} reconnected")
        except asyncio.TimeoutError:
            logger.error(f"User {user_id} did not reconnect in time")
            await self._end_match(EndReason.DISCONNECT_TIMEOUT)

    async def _wait_for_user_reconnect(self, user_id: str) -> None:
        '''Wait for a user to reconnect'''
        while user_id not in self._connected_users:
            await asyncio.sleep(0.1)

    async def _monitor_match_start(self) -> None:
        '''Monitor the start of the match, will end the match if not all users connect in time'''
        try:
            await asyncio.wait_for(self._wait_for_users_to_connect(), timeout=MATCH_START_TIMEOUT)
            logger.info("Both users connected, match starting.")
        except asyncio.TimeoutError:
            logger.error("Match start timeout, not all users connected.")
            await self._end_match(EndReason.MATCH_START_TIMEOUT)

    async def _wait_for_users_to_connect(self) -> None:
        '''Wait until both users are connected'''
        while len(self._connected_users) < len(self._assigned_users):
            await asyncio.sleep(0.1)

    #############################
    #    Connection functions   #
    #############################

    async def connect_user(self, user_id: str, on_match_finished: Callable[[], None]) -> None:
        '''Connect a user to the match'''
        if user_id not in self._assigned_users:
            logger.error(f"User {user_id} not assigned to the match")
            return
        self._connected_users.add(user_id)
        self._on_match_finished_user_callbacks[user_id] = on_match_finished
        logger.info(f"User {user_id} connected to match {self._id}")

    async def disconnect_user(self, user_id: str) -> bool:
        '''Disconnect a user from the match'''
        logger.info(f"Disconnecting user {user_id} from match {self._id}")
        try:
            self._connected_users.remove(user_id)
            logger.info(f"Removed user {user_id} from connected users")
        except KeyError:
            logger.error(f"Cannot disconnect user {user_id} from match {self._id} as they are not connected to it")
            return False
        await self._send_player_disconnected_message(user_id)
        self._disconnect_count[user_id] += 1
        if self._disconnect_count[user_id] >= DISCONNECT_THRESHOLD:
            await self._end_match(EndReason.DISCONNECTED_TOO_MANY_TIMES)
            return True
        logger.info(f"Disconnect count: {self._disconnect_count[user_id]}")
        await self._monitor_disconnect_timeout(user_id)
        return True

    #############################
    #    Game control functions #
    #############################

    async def update_player_direction(self, user_id: str, direction: str, player_key_id: str) -> None:
        '''Update the direction of a player'''
        if user_id not in self._assigned_users:
            logger.error(f"User {user_id} not assigned to the match")
            return
        if user_id not in self._connected_users:
            logger.error(f"User {user_id} not connected to the match")
            return
        
        # Update the direction of the player, depending on the match type
        if self._is_local_match:
            await self._gamehandler.update_player_direction(player_key_id, direction)
        else:
            await self._gamehandler.update_player_direction(self._player_mapping[user_id], direction)

    #############################
    #     Database functions    #
    #############################

    async def _write_score_to_database(self) -> None:
        '''Write the score to the database'''
        pass

    #############################
    # Callbacks from the game   #
    #############################

    async def _user_scored(self, player_id: str) -> None:
        '''Callback when a player scores'''
        self._score[player_id] += 1
        if self._score[player_id] >= WINNING_SCORE:
            await self._end_match(EndReason.SCORE)

    #############################
    #    Message sending        #
    #############################

    async def _send_game_state(self) -> None:
        '''Send the game state to the users'''
        pass

    async def _send_player_disconnected_message(self, user_id: str) -> None:
        '''Send a disconnect message to the users'''
        pass

    #############################
    #    Utility functions      #
    #############################

    def is_user_assigned(self, user_id: str) -> bool:
        '''Check if a user is assigned to the match'''
        return user_id in self._assigned_users
    
    def is_user_connected(self, user_id: str) -> bool:
        '''Check if a user is connected to the match'''
        return user_id in self._connected_users
    
    def get_id(self) -> str:
        '''Get the match id'''
        return self._id