import logging
import asyncio
from typing import Set, List, Tuple, Optional, Callable
from pong.match_tournament.match_session import MatchSession
from uuid import uuid4

logger = logging.getLogger("PongConsumer")
logger.setLevel(logging.DEBUG)

class TournamentSession:
    def __init__(self, owner_user_id, name: str, size: int, on_finished: Callable[[str], None]):
        self._id = uuid4().hex
        self._name = name
        self._owner_user_id = owner_user_id
        self._max_players = size
        self._users: Set[str] = set()
        self._matches: List[Tuple[str, str]] = []
        self._results: List[Optional[str]] = []
        self._winner: Optional[str] = None
        self._running = False
        self._condition = asyncio.Condition()
        self._on_finished = on_finished

        self._users.add(owner_user_id)
        logger.debug(f"Created tournament session {self}")

    async def start(self) -> None:
        self._running = True
        
        while self._running:
            self._reset_tracking_variables()
            self._generate_round_robin_schedule()
            await self._start_matches()
            self._determine_winner()
            
            if self._winner is not None: # TODO: Notify the winner
                self._running = False
                self._on_finished(self._id)

    def _generate_round_robin_schedule(self) -> None:
        users = list(self._users)
        n = len(users)
        for i in range(n):
            for j in range(i + 1, n):
                self._matches.append((users[i], users[j]))

    def _determine_winner(self) -> None:
        # Initialize the score dictionary
        score = {user: 0 for user in self._users}

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
        self._users = {user for user in self._users if score[user] == max_score}

    def _reset_tracking_variables(self) -> None:
        '''Reset the tracking variables for a new round'''
        self._matches = []
        self._results = []
        self._winner = None

    async def _start_matches(self) -> None:
        for match in self._matches:
            async with self._condition:
                # Create a new match session
                MatchSession(match[0], match[1], self._on_match_finished)
                # Wait until the match is finished
                await self._condition.wait()

    def _on_match_finished(self, match_id: str, winner: str) -> None:
        self._results.append(winner)
        # Notify the condition variable that the match is finished
        async def notify():
            async with self._condition:
                self._condition.notify()
        asyncio.create_task(notify())

    def add_user(self, user_id: str):
        '''Add a user to the tournament set'''
        self._users.add(user_id)

    def remove_user(self, user_id: str):
        self._users.remove(user_id)

    def get_id(self) -> str:
        return self._id
    
    def get_owner_user_id(self) -> str:
        return self._owner_user_id

    def get_name(self) -> str:
        return self._name

    def get_max_players(self) -> int:
        return self._max_players

    def get_users(self) -> Set[str]:
        return self._users

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
        return len(self._users) == self._max_players
    
    def is_running(self) -> bool:
        return self._running

    def is_ready(self) -> bool:
        return len(self._matches) == self._max_players

    def is_finished(self) -> bool:
        return self._winner is not None
    
    def has_user(self, user_id: str) -> bool:
        return user_id in self._users

    def __str__(self) -> str:
        return f': {self._name} - {self._max_players} players'

    def __repr__(self) -> str:
        return f': {self._name} - {self._max_players} players'