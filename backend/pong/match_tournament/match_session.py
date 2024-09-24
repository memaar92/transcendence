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
    DRAW = auto()
    SCORE = auto()
    LOCAL_MATCH_ABORTED = auto()

class MatchSession:
    def __init__(self, user_id_1: str, user_id_2: Optional[str], on_match_finished: Optional[Callable[[str, str], None]] = None):
        '''Initialize and start a match between two users'''
        self._match_id = str(id(self))  # Generating a unique id
        self._assigned_users = {user_id_1, user_id_2} if user_id_2 is not None else {user_id_1}
        self._blocked_users = set()
        self._connected_users = set()
        self._disconnect_count = {user_id_1: 0, user_id_2: 0} if user_id_2 is not None else {user_id_1: 0}
        self._player_mapping = {user_id_1: "p1", user_id_2: "p2"} if user_id_2 is not None else {user_id_1: "p1"}
        self._is_local_match = user_id_2 is None
        self._score = {user_id_1: 0, user_id_1: 0}
        self._gamehandler = None
        self._main_loop_task: Optional[asyncio.Task] = asyncio.create_task(self._main_loop())
        self._on_match_finished = on_match_finished
        self._on_match_finished_user_callbacks = {user_id_1: None, user_id_2: None} if user_id_2 is not None else {user_id_1: None}
        self._tick_speed = 1 / TICK_RATE
        self._is_match_running = False
        self._stop_requested = False

    async def _main_loop(self) -> None:
        '''Main loop of the match'''
        while not self._stop_requested:
            if not self._is_match_running:
                await self._monitor_match_start()
                self._is_match_running = True
            # self._gamehandler.update()
            await self._send_game_state()
            await asyncio.sleep(self._tick_speed)

    async def _end_match(self, reason: EndReason) -> None:
        '''End the match'''
        self._stop_requested = True
        logger.info(f"Ending match {self._match_id}")
        if reason == EndReason.DISCONNECT_TIMEOUT:
            await self._match_finished(self._match_id, self._connected_users.pop())
            logger.info("Match ended due to disconnect timeout")
        elif reason == EndReason.MATCH_START_TIMEOUT:
            await self._match_finished(self._match_id, None)
            logger.info("Match ended due to timeout")
        elif reason == EndReason.DRAW:
            await self._match_finished(self._match_id, None)
            logger.info("Match ended due to timeout and draw")
        elif reason == EndReason.DISCONNECTED_TOO_MANY_TIMES:
            logger.info("Match ended due to too many disconnects")
            await self._match_finished(self._match_id, self._connected_users.pop())
        elif reason == EndReason.SCORE:
            winner = max(self._score, key=self._score.get)
            await self._match_finished(self._match_id, winner)
            logger.info("Match ended due to score")
        elif reason == EndReason.LOCAL_MATCH_ABORTED:
            await self._match_finished(self._match_id, None, False)
            logger.info("Match ended due to local match abort")


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

    async def _match_finished(self, match_id: str, winner: str, write_to_db: bool = True) -> None:
        '''Callback when the match is finished'''
        logger.info(f"Match {match_id} finished, winner: {winner}")
        # if write_to_db:
            # await self._write_score_to_database() # TODO: Implement this
        if self._on_match_finished is not None:
            await self._on_match_finished(match_id, winner)

    #############################
    #      Timer functions      #
    #############################

    async def _monitor_disconnect_timeout(self, user_id: str) -> None:
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

    async def _wait_for_user_reconnect(self, user_id: str) -> None:
        '''Wait for a user to reconnect'''
        while user_id not in self._connected_users:
            await asyncio.sleep(0.1)

    async def _monitor_match_start(self) -> None:
        '''Monitor the start of the match, will end the match if not all users connect in time'''
        try:
            await asyncio.wait_for(self._wait_for_users_to_connect(), timeout=MATCH_START_TIMEOUT)
            logger.debug("Both users connected, match starting.")
        except asyncio.TimeoutError:
            logger.debug("Match start timeout, not all users connected.")
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
        if self._stop_requested:
            logger.error(f"Match {self._match_id} has already ended")
            return
        if user_id not in self._assigned_users:
            logger.error(f"User {user_id} not assigned to the match")
            return
        self._connected_users.add(user_id)
        self._on_match_finished_user_callbacks[user_id] = on_match_finished
        logger.debug(f"User {user_id} connected to match {self._match_id}")

        # Check if a blocked user exists and end the match if only one user is left
        if len(self._blocked_users) == 1:
            await self._end_match(EndReason.DISCONNECT_TIMEOUT)

    async def disconnect_user(self, user_id: str) -> bool:
        '''Disconnect a user from the match'''
        logger.debug(f"Disconnecting user {user_id} from match {self._match_id}")
        try:
            self._connected_users.remove(user_id)
            self._on_match_finished_user_callbacks[user_id] = None
            logger.debug(f"Removed user {user_id} from connected users")
        except KeyError:
            logger.error(f"Cannot disconnect user {user_id} from match {self._match_id} as they are not connected to it")
            return False
        await self._send_player_disconnected_message(user_id)
        self._disconnect_count[user_id] += 1
        if self._disconnect_count[user_id] >= DISCONNECT_THRESHOLD:
            await self._end_match(EndReason.DISCONNECTED_TOO_MANY_TIMES)
            return True
        logger.debug(f"Disconnect count: {self._disconnect_count[user_id]}")
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
        return self._match_id