import logging
import asyncio
from channels.layers import get_channel_layer
from typing import Set, List, Tuple, Optional, Callable
from pong.match_tournament.match_session import MatchSession
from pong.match_tournament.data_managment.matches import Matches
from uuid import uuid4

logger = logging.getLogger("tournament")

class TournamentSession:
    def __init__(self, owner_user_id, name: str, size: int, on_finished: Callable[[str], None]):
        self._id = uuid4().hex
        self._name = name
        self._owner_user_id = owner_user_id
        self._max_players = size
        self._assigned_users: Set[str] = set() # Users that are assigned to the tournament
        self._active_users: Set[str] = set() # Users that are still in the tournament
        self._matches: List[Tuple[str, str]] = []
        self._results: List[Optional[str]] = []
        self._winner: Optional[str] = None
        self._running = False
        self._condition = asyncio.Condition()
        self._on_finished = on_finished

        self._assigned_users.add(owner_user_id)
        self._channel_layer = get_channel_layer()
        logger.debug(f"Created tournament session {self}")

    def __del__(self):
        logger.debug(f"Deleted tournament session {self}")

    async def start(self) -> None:
        self._running = True
        self._active_users = self._assigned_users.copy()
        while self._running:
            self._reset_tracking_variables()
            self._generate_round_robin_schedule()
            await self._start_matches()
            self._determine_winner()
            
            if self._winner is not None:
                logger.info(f"Tournament {self._id} finished with winner {self._winner}")
                self._running = False
        self._on_finished(self._id)

    def _generate_round_robin_schedule(self) -> None:
        users = list(self._active_users)
        n = len(users)
        for i in range(n):
            for j in range(i + 1, n):
                self._matches.append((users[i], users[j]))

    def _determine_winner(self) -> None:
        # Initialize the score dictionary
        score = {user: 0 for user in self._active_users}

        # Calculate the scores based on the results
        for result in self._results:
            if result is not None:
                score[result] += 1

        # Print the number of wins for each user
        for user, points in score.items():
            print(f"User {user} has {points} wins.")

        # Determine the maximum score
        max_score = max(score.values())

        # If no matches were played, there is no winner
        if max_score == 0:
            self._winner = None
            self._running = False
            logger.info("No winner found, maybe no matches were played")
            return

        # Find the users with the maximum score
        winners = [user for user, points in score.items() if points == max_score]

        # Determine the winner or if it's a draw
        if len(winners) == 1:
            self._winner = winners[0]
            return  # Early return if a winner is found
        else:
            self._winner = None  # It's a draw

        # Filter users with the maximum score
        self._active_users = {user for user in self._active_users if score[user] == max_score}

    def _reset_tracking_variables(self) -> None:
        '''Reset the tracking variables for a new round'''
        self._matches = []
        self._results = []
        self._winner = None

    async def _start_matches(self) -> None:
        for match in self._matches:
            async with self._condition:
                # Create a new match session
                await self._create_match(match[0], match[1])
                # Wait until the match is finished
                await self._condition.wait()

    async def match_finished_callback(self, match_id: str, winner: str) -> None:
        self._results.append(winner)
        Matches.remove_match(match_id)
        # Notify the condition variable that the match is finished
        async with self._condition:
            self._condition.notify_all()


    async def _create_match(self, user1: str, user2: str) -> None:
        # Create match
        # Send ready message
        # remove after match is finished
        match_session = MatchSession(user1, user2, self.match_finished_callback)
        Matches.add_match(match_session)
        await self._send_match_ready_message(match_session.get_id(), user1, user2)

    async def _send_match_ready_message(self, match_id: str, user1: str, user2: str) -> None:
        '''Send a match ready message to both users'''
        match = Matches.get_match(match_id)
        if match:
            await self._channel_layer.group_send(
                f"user_{user1}",
                {
                    'type': 'match_ready',
                    'match_id': match_id
                }
            )
            await self._channel_layer.group_send(
                f"user_{user2}",
                {
                    'type': 'match_ready',
                    'match_id': match_id
                }
            )


    def add_user(self, user_id: str):
        '''Add a user to the tournament set'''
        self._assigned_users.add(user_id)

    def remove_user(self, user_id: str):
        self._assigned_users.remove(user_id)

    def get_id(self) -> str:
        return self._id
    
    def get_owner_user_id(self) -> str:
        return self._owner_user_id

    def get_name(self) -> str:
        return self._name

    def get_max_players(self) -> int:
        return self._max_players

    def get_users(self) -> Set[str]:
        return self._assigned_users

    def get_matches(self) -> list:
        return self._matches

    def get_winner(self) -> str:
        return self._winner

    def set_winner(self, winner) -> None:
        self._winner = winner

    def add_match(self, match) -> None:
        self._matches.append(match)

    def remove_match(self, match) -> None:
        self._matches.remove(match)

    def is_full(self) -> bool:
        return len(self._assigned_users) == self._max_players
    
    def is_running(self) -> bool:
        return self._running

    def is_ready(self) -> bool:
        return len(self._matches) == self._max_players

    def is_finished(self) -> bool:
        return self._winner is not None
    
    def has_user(self, user_id: str) -> bool:
        return user_id in self._assigned_users

    def __str__(self) -> str:
        return f': {self._name} - {self._max_players} players'

    def __repr__(self) -> str:
        return f': {self._name} - {self._max_players} players'