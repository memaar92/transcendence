import logging
import time
import json
from typing import List, Any, Optional
from django.core.exceptions import SuspiciousOperation
from ...services.redis_service.constants import UserGameStatus
from .constants import RedisKeys, UserSessionFields, REDIS_INSTANCE
from .match import Match

logger = logging.getLogger("PongConsumer")

class User:

    ###########
    # GETTERS #
    ###########

    @staticmethod
    async def get_last_login(user_id: str) -> Optional[int]:
        '''Get the last login time of the user'''
        last_login = await REDIS_INSTANCE.hget(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.LAST_LOGIN)
        if last_login:
            return int(last_login)  # Convert bytes to integer
        return None

    @staticmethod
    async def get_match_id(user_id: str) -> Optional[str]:
        '''Get the last match ID of the user'''
        last_match_id = await REDIS_INSTANCE.hget(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.LAST_MATCH_ID)
        if last_match_id:
            return last_match_id.decode('utf-8')  # Convert bytes to string
        return None

    @staticmethod
    async def get_online_status(user_id: str) -> Optional[str]:
        '''Get the online status of the user'''
        online_status = await REDIS_INSTANCE.hget(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.ONLINE_STATUS)
        if online_status:
            return online_status.decode('utf-8')  # Convert bytes to string
        return None

    ###########
    # SETTERS #
    ###########

    @staticmethod
    async def set_session_info(user_id: str, online_status: str, last_match_id: Optional[str], ttl: int = 3600) -> None:
        '''Set user session information in Redis using a hash'''
        user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
        
        # Prepare the user information dictionary
        user_info = {
            UserSessionFields.ONLINE_STATUS: online_status,  # online, in_queue, playing, offline
            UserSessionFields.LAST_LOGIN: int(time.time())   # Timestamp of the last login
        }
        
        # Add last_match_id only if it's not None
        if last_match_id is not None:
            user_info[UserSessionFields.LAST_MATCH_ID] = last_match_id
        
        # Store each field in the Redis hash
        await REDIS_INSTANCE.hset(user_key, mapping=user_info)
        
        # Set an expiration time for the hash
        await REDIS_INSTANCE.expire(user_key, ttl)

    @staticmethod
    async def set_match_id(user_id: str, match_id: str) -> None:
        '''Set the last match ID for the user within the user session hash'''
        try:
            # Define the key for the user session hash
            user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
            
            # Store the match_id in the hash
            await REDIS_INSTANCE.hset(user_key, UserSessionFields.LAST_MATCH_ID, match_id)
        except Exception as e:
            logger.error(f"Error setting match ID for user {user_id}: {e}")
            raise SuspiciousOperation("Error updating user match ID in Redis.")

    @staticmethod
    async def set_online_status(user_id: str, online_status: str) -> None:
        '''Set the online status of the user'''
        try:
            # Define the key for the user session hash
            user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
            
            # Store the online_status in the hash
            await REDIS_INSTANCE.hset(user_key, UserSessionFields.ONLINE_STATUS, online_status)
        except Exception as e:
            logger.error(f"Error setting online status for user {user_id}: {e}")
            raise SuspiciousOperation("Error updating user online status in Redis.")

    @staticmethod
    async def set_last_login(user_id: str) -> None:
        '''Set the last login time of the user'''
        try:
            # Define the key for the user session hash
            user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
            
            # Store the current timestamp in the hash
            await REDIS_INSTANCE.hset(user_key, UserSessionFields.LAST_LOGIN, int(time.time()))
        except Exception as e:
            logger.error(f"Error setting last login for user {user_id}: {e}")
            raise SuspiciousOperation("Error updating user last login time in Redis.")
        
    @staticmethod
    async def connect_to_match(user_id: str, match_id: str) -> None:
        '''Connect the user to the match'''
        if not await Match.exists(match_id):
            raise SuspiciousOperation("Match does not exist.")
        if await Match.is_user_connected(match_id, user_id):
            raise SuspiciousOperation("User is already connected to the match.")
        if not await Match.is_user_assigned(match_id, user_id):
            raise SuspiciousOperation("User is not assigned to this match.")
        await Match.connect_user(match_id, user_id)
        await User.set_online_status(user_id, UserGameStatus.PLAYING)
        await User.set_match_id(user_id, match_id)
    
    @staticmethod
    async def disconnect_from_match(user_id: str, match_id: str) -> None:
        '''Disconnect the user from the match'''
        if not await Match.exists(match_id):
            raise SuspiciousOperation("Match does not exist.")
        if not await Match.is_user_connected(match_id, user_id):
            raise SuspiciousOperation("User is not connected to the match.")
        await Match.disconnect_user(match_id, user_id)
        await User.set_online_status(user_id, UserGameStatus.AVAILABLE)
        await User.set_match_id(user_id, None)

    ###########
    #   BOOL  #
    ###########

    @staticmethod
    async def is_playing(user_id: str) -> bool:
        '''Check if the user is currently playing a match'''
        return await User.get_online_status(user_id) == UserGameStatus.PLAYING
    
    @staticmethod
    async def exists(user_id: str) -> bool:
        '''Check if the user exists in the Redis database'''
        return await REDIS_INSTANCE.exists(f"{RedisKeys.USER_SESSION}:{user_id}") == 1

    ###########
    # DELETE  #
    ###########

    ###########
    #  MISC   #
    ###########