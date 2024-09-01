from .constants import QueueFields, REDIS_INSTANCE
from typing import Optional
from ...services.redis_service.constants import UserGameStatus
from .user import User

class MatchmakingQueue:

    @staticmethod
    async def remove_user(user_id: str) -> None:
        '''Remove the user from the matchmaking queue'''
        if user_id:
            await REDIS_INSTANCE.lrem(QueueFields.MATCHMAKING_QUEUE, 0, user_id)
            await User.set_online_status(user_id, UserGameStatus.AVAILABLE)
    
    @staticmethod
    async def add_user(user_id: str) -> None:
        '''Add the user to the matchmaking queue'''
        if user_id:
            await REDIS_INSTANCE.rpush(QueueFields.MATCHMAKING_QUEUE, user_id)
            await User.set_online_status(user_id, UserGameStatus.IN_QUEUE)
    
    @staticmethod
    async def get_queue_length() -> int:
        '''Get the length of the matchmaking queue'''
        return await REDIS_INSTANCE.llen(QueueFields.MATCHMAKING_QUEUE)
    
    @staticmethod
    async def pop_next_user() -> Optional[str]:
        '''Pop the next user from the matchmaking queue'''
        user_id = await REDIS_INSTANCE.lpop(QueueFields.MATCHMAKING_QUEUE)
        if user_id:
            return user_id.decode('utf-8')
        return None
    
    @staticmethod
    async def is_user_id_in_queue(user_id: str) -> bool:
        '''Check if the user_id is in the matchmaking queue'''
        return await REDIS_INSTANCE.lpos(QueueFields.MATCHMAKING_QUEUE, user_id) is not None