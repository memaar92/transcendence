from .constants import QueueFields, REDIS_INSTANCE
from asgiref.sync import sync_to_async
from typing import Optional
from ...utils.states import UserOnlineStatus
from .user import User

class MatchmakingQueue:

    @staticmethod
    async def remove_user(user_id: str) -> None:
        '''Remove the user from the matchmaking queue'''
        if user_id:
            await sync_to_async(REDIS_INSTANCE.lrem)(QueueFields.MATCHMAKING_QUEUE, 0, user_id)
            await User.set_online_status(user_id, UserOnlineStatus.ONLINE)
    
    @staticmethod
    async def add_user(user_id: str) -> None:
        '''Add the user to the matchmaking queue'''
        if user_id:
            await sync_to_async(REDIS_INSTANCE.rpush)(QueueFields.MATCHMAKING_QUEUE, user_id)
            await User.set_online_status(user_id, UserOnlineStatus.IN_QUEUE)
    
    @staticmethod
    async def get_queue_length() -> int:
        '''Get the length of the matchmaking queue'''
        return await sync_to_async(REDIS_INSTANCE.llen)(QueueFields.MATCHMAKING_QUEUE)
    
    @staticmethod
    async def pop_next_user() -> Optional[str]:
        '''Pop the next user from the matchmaking queue'''
        user_id = await sync_to_async(REDIS_INSTANCE.lpop)(QueueFields.MATCHMAKING_QUEUE)
        if user_id:
            return user_id.decode('utf-8')
        return None
    
    @staticmethod
    async def is_user_id_in_queue(user_id: str) -> bool:
        '''Check if the user_id is in the matchmaking queue'''
        return await sync_to_async(REDIS_INSTANCE.lpos)(QueueFields.MATCHMAKING_QUEUE, user_id) is not None