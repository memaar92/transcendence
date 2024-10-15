import logging
from typing import Dict, Optional, Callable
from .match_session import MatchSession
from channels.layers import get_channel_layer
from ..data_managment.matchmaking_queue import MatchmakingQueue
from ..data_managment.matches import Matches
from ..data_managment.user import User
from ..data_managment.tournaments import Tournaments

logger = logging.getLogger("match")

class MatchSessionHandler:

    @classmethod
    async def create_match(
        cls,
        user1: str,
        user2: Optional[str] = None,
        on_match_finished: Optional[Callable[[str, str], None]] = None # on_match_finished(match_id: str, winner(user_id): str) -> None
    ) -> 'MatchSession':
        
        match = MatchSession(user1, user2, on_match_finished)

        Matches.add_match(match)

        logger.info(f"Match created with id {match.get_id()}")

        return match

    @classmethod
    async def create_local_match(cls, user_id: int) -> None:
        '''Create a local match'''
        if MatchmakingQueue.is_user_registered(user_id):
            raise ValueError(f"registered to queue")
        elif Tournaments.is_user_registered(user_id):
            raise ValueError(f"registered to tournament")
        elif Matches.is_user_registered(user_id):
            raise ValueError(f"registered to match")
        match = await cls.create_match(user_id, None, cls.remove_match)
        match_id = match.get_id()
        await cls.send_match_ready_message(match_id, user_id, None)

        logger.debug(f"Local match created: {user_id}")

    @classmethod
    async def remove_match(cls, match_id: str, winner: int) -> None:
        '''Remove a match reference'''
        Matches.remove_match(match_id)
    
    ##############################
    # Matchmaking Queue Methods #
    ##############################

    @classmethod
    async def add_to_matchmaking_queue(cls, user_id: int) -> None:
        '''Add a user to the matchmaking queue'''
        if MatchmakingQueue.is_user_registered(user_id):
            raise ValueError(f"registered to queue")
        elif Tournaments.is_user_registered(user_id):
            raise ValueError(f"registered to tournament")
        elif Matches.is_user_registered(user_id):
            raise ValueError(f"registered to match")
        MatchmakingQueue.add_to_queue(user_id)
        if MatchmakingQueue.get_queue_length() >= 2:
            user_id_1 = MatchmakingQueue.pop_next_user()
            user_id_2 = MatchmakingQueue.pop_next_user()
            if user_id_1 and user_id_2:
                match = await cls.create_match(user_id_1, user_id_2, cls.remove_match)

                # Send a message to both users
                match_id = match.get_id()
                await cls.send_match_ready_message(match_id, user_id_1, user_id_2)

                logger.debug(f"Match found: {user_id_1} vs {user_id_2}")

    @classmethod
    async def send_match_ready_message(cls, match_id: str, user1: str, user2: str) -> None:
        '''Send a match ready message to both users'''
        match = Matches.get_match(match_id)
        if match:
            print (f"Match found: {user1} vs {user2}")
            if user1:
                await cls._send_remote_match_ready_message(match_id, user1, user2)
            if user2:
                await cls._send_remote_match_ready_message(match_id, user2, user1)

    @classmethod
    def remove_from_matchmaking_queue(cls, user_id: int) -> None:
        '''Remove a user from the matchmaking queue'''
        is_removed = MatchmakingQueue.remove_from_queue(user_id)
        if not is_removed:
            raise ValueError(f"not in queue")
        
    @classmethod
    async def _send_remote_match_ready_message(cls, match_id: str, user_id: int, opponent_id: int) -> None:
        '''Send a match ready message to a user'''
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"mm_{user_id}",
            {
                'type': 'remote_match_ready',
                'match_id': match_id,
                'opponent_id': opponent_id
            }
        )
