import asyncio
import logging
from typing import Dict, Optional, Callable
from .match_session import MatchSession
from channels.layers import get_channel_layer

logger = logging.getLogger("PongConsumer")

class MatchSessionHandler:
    # Class variables
    _matches: Dict[str, 'MatchSession'] = {}
    _matchmaking_queue: set = set()

    @classmethod
    async def create_match(
        cls,
        user1: str,
        user2: Optional[str] = None,
        on_match_finished: Optional[Callable[[str], None]] = None
    ) -> 'MatchSession':
        '''Create a match between two users'''
        match = MatchSession(user1, user2, on_match_finished)
        cls._matches[match.get_id()] = match

        logger.info(f"Match created with id {match.get_id()}")
        
        # Run the match asynchronously in the background
        # asyncio.create_task(match.start())
        
        return match

    @classmethod
    def create_local_match(cls, user1: str, on_match_finished: Optional[Callable[[str], None]] = None) -> 'MatchSession':
        '''Create a local match'''
        return cls.create_match(user1, None, on_match_finished)

    @classmethod
    def get_match(cls, match_id: str) -> Optional['MatchSession']:
        '''Get a match by id'''
        return cls._matches.get(match_id)
    
    @classmethod
    def get_matches(cls) -> Dict[str, 'MatchSession']:
        '''Get all matches'''
        return cls._matches
    
    @classmethod
    async def get_user_match_id(cls, user_id: str) -> Optional[str]:
        '''Get the match id of a user'''
        for match in cls._matches.values():
            if match.is_user_assigned(user_id):
                return match.get_id()
        return None
    
    @classmethod
    async def connect_user(cls, match_id: str, user_id: str, on_match_finished: Callable[[], None]) -> None:
        '''Connect a user to a match'''
        match = cls._matches.get(match_id)
        logger.debug(f"Match id: {match_id}")
        if match:
            logger.debug(f"User {user_id} connected to match {match_id}")
            await match.connect_user(user_id, on_match_finished)
        else:
            logger.error(f"Match with id {match_id} not found")

    @classmethod
    async def disconnect_user(cls, user_id: str) -> None:
        '''Disconnect a user from a match and remove them from the matchmaking queue'''
        if user_id in cls._matchmaking_queue:
            cls.remove_from_matchmaking_queue(user_id)
            logger.info(f"User {user_id} disconnected and removed from matchmaking queue")

    @classmethod
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered to a match or the matchmaking queue'''
        for match in cls._matches.values():
            if match.is_user_assigned(user_id):
                return True
        if user_id in cls._matchmaking_queue:
            return True
        return False
    
    @classmethod
    async def is_user_connected(cls, user_id: str) -> bool:
        '''Check if a user is connected to a match'''
        for match in cls._matches.values():
            if match.is_user_connected(user_id):
                return True
        return False

    @classmethod
    async def remove_match(cls, match_id: str) -> None:
        '''Remove a match reference'''
        if match_id in cls._matches:
            del cls._matches[match_id]
    
    ##############################
    # Matchmaking Queue Methods #
    ##############################

    @classmethod
    async def add_to_matchmaking_queue(cls, user_id: str) -> None:
        '''Add a user to the matchmaking queue'''
        if cls.is_user_registered(user_id):
            logger.error(f"Cannot add user {user_id} to matchmaking queue as they are already registered to a match")
            return
        cls._matchmaking_queue.add(user_id)
        logger.info(f"User {user_id} added to matchmaking queue")
        if len(cls._matchmaking_queue) >= 2:
            user_id_1 = cls.pop_next_user_from_matchmaking_queue()
            user_id_2 = cls.pop_next_user_from_matchmaking_queue()
            if user_id_1 and user_id_2:
                match = await cls.create_match(user_id_1, user_id_2, cls.remove_match)
                match_id = match.get_id()
                logger.debug(f"Match found: {user_id_1} vs {user_id_2}")
                cls._matches[match_id] = match

                # Send a message to both users
                channel_layer = get_channel_layer()
                await channel_layer.group_send(
                    f"user_{user_id_1}",
                    {
                        'type': 'match_assigned',
                        'match_id': match_id
                    }
                )
                await channel_layer.group_send(
                    f"user_{user_id_2}",
                    {
                        'type': 'match_assigned',
                        'match_id': match_id
                    }
                )

    @classmethod
    def remove_from_matchmaking_queue(cls, user_id: str) -> None:
        '''Remove a user from the matchmaking queue'''
        if user_id in cls._matchmaking_queue:
            cls._matchmaking_queue.remove(user_id)

    @classmethod
    def get_matchmaking_queue(cls) -> set:
        '''Get the matchmaking queue'''
        return cls._matchmaking_queue
    
    @classmethod
    def get_matchmaking_queue_length(cls) -> int:
        '''Get the length of the matchmaking queue'''
        return len(cls._matchmaking_queue)
    
    @classmethod
    def pop_next_user_from_matchmaking_queue(cls) -> Optional[str]:
        '''Pop the next user from the matchmaking queue'''
        if len(cls._matchmaking_queue) > 0:
            return cls._matchmaking_queue.pop()
        return None