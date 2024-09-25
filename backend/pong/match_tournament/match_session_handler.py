import logging
from typing import Dict, Optional, Callable
from .match_session import MatchSession
from channels.layers import get_channel_layer
from pong.match_tournament.data_managment import MatchmakingQueue, Matches, User

logger = logging.getLogger("PongConsumer")

class MatchSessionHandler:

    @classmethod
    async def create_match(
        cls,
        user1: str,
        user2: Optional[str] = None,
        on_match_finished: Optional[Callable[[str, str], None]] = None # on_match_finished(match_id: str, winner(user_id): str) -> None
    ) -> 'MatchSession':
        '''Create a match between two users'''
        match = MatchSession(user1, user2, on_match_finished)
        Matches.add_match(match)

        logger.info(f"Match created with id {match.get_id()}")
        
        # Run the match asynchronously in the background
        # asyncio.create_task(match.start())

        return match

    @classmethod
    def create_local_match(cls, user1: str, on_match_finished: Optional[Callable[[str], None]] = None) -> 'MatchSession':
        '''Create a local match'''
        return cls.create_match(user1, None, on_match_finished)

    @classmethod
    async def remove_match(cls, match_id: str, winner: str) -> None:
        '''Remove a match reference'''
        Matches.remove_match(match_id)
    
    ##############################
    # Matchmaking Queue Methods #
    ##############################

    @classmethod
    async def add_to_matchmaking_queue(cls, user_id: str) -> None:
        '''Add a user to the matchmaking queue'''
        if User.is_user_registered(user_id):
            logger.error(f"Cannot add user {user_id} to matchmaking queue as the user is already registered to the queue, a match or a tournament")
            return
        MatchmakingQueue.add_to_queue(user_id)
        if MatchmakingQueue.get_queue_length() >= 2:
            user_id_1 = MatchmakingQueue.pop_next_user()
            user_id_2 = MatchmakingQueue.pop_next_user()
            if user_id_1 and user_id_2:
                match = await cls.create_match(user_id_1, user_id_2, cls.remove_match)
                Matches.add_match(match)

                # Send a message to both users
                match_id = match.get_id()
                await cls.send_match_ready_message(match_id, user_id_1, user_id_2)

                logger.debug(f"Match found: {user_id_1} vs {user_id_2}")

    @classmethod
    async def send_match_ready_message(cls, match_id: str, user1: str, user2: str) -> None:
        '''Send a match ready message to both users'''
        match = Matches.get_match(match_id)
        if match:
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f"user_{user1}",
                {
                    'type': 'match_ready',
                    'match_id': match_id
                }
            )
            await channel_layer.group_send(
                f"user_{user2}",
                {
                    'type': 'match_ready',
                    'match_id': match_id
                }
            )

    @classmethod
    def remove_from_matchmaking_queue(cls, user_id: str) -> None:
        '''Remove a user from the matchmaking queue'''
        MatchmakingQueue.remove_from_queue(user_id)