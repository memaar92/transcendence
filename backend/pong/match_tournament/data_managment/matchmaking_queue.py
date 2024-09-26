from typing import Optional, Set
import logging

logger = logging.getLogger("data_managment")

class MatchmakingQueue:
    queue: Set[str] = set()

    @classmethod
    def add_to_queue(cls, user_id: str) -> None:
        '''Add a user to the matchmaking queue'''
        cls.queue.add(user_id)
        logger.info(f"User {user_id} added to matchmaking queue")

    @classmethod
    def remove_from_queue(cls, user_id: str) -> None:
        '''Remove a user from the matchmaking queue'''
        if user_id in cls.queue:
            cls.queue.remove(user_id)
            logger.info(f"User {user_id} removed from matchmaking queue")

    @classmethod
    def get_queue(cls) -> set:
        '''Get the matchmaking queue'''
        return cls.queue
    
    @classmethod
    def get_queue_length(cls) -> int:
        '''Get the length of the matchmaking queue'''
        return len(cls.queue)
    
    @classmethod
    def is_user_registered(cls, user_id: str) -> bool:
        '''Check if a user is registered for the matchmaking queue'''
        return user_id in cls.queue
    
    @classmethod
    def pop_next_user(cls) -> Optional[str]:
        '''Pop the next user from the queue'''
        if cls.queue:
            return cls.queue.pop()
        return None