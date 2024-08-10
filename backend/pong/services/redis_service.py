import logging
from asgiref.sync import sync_to_async
from django.core.exceptions import SuspiciousOperation
import json
import time
from enum import Enum
import redis
from ..consumers.gamesession_consumer import GameState as GameSessionState

redis_instance = redis.StrictRedis(host='redis', port=6379, db=0)

logger = logging.getLogger("PongConsumer")


class RedisKeys:
    USER_SESSION = "user:session"
    MATCHES_OPEN = "matches:open"

class MatchSessionFields:
    CONNECTED_USERS = "connected_users"
    STATE = "state"

class UserSessionFields:
    LAST_MATCH_ID = "last_match_id"
    ONLINE_STATUS = "online_status"
    LAST_LOGIN = "last_login"

class UserOnlineStatus:
    ONLINE = "online"
    IN_QUEUE = "in_queue"
    PLAYING = "playing"
    OFFLINE = "offline"

####################################################################################################
#                                   GAME SESSION FUNCTIONS                                         #
####################################################################################################

###########
# GETTERS #
###########

async def get_match_connected_users(match_id):
    '''Get the connected users for the match'''
    # Retrieve the match data from the Redis hash
    match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
    
    if match_data_json:
        # Decode the JSON string back to a Python dictionary
        match_data = json.loads(match_data_json)
        return match_data.get(MatchSessionFields.CONNECTED_USERS, [])
    return []

###########
# SETTERS #
###########

async def set_match_info(match_id: str, connected_users: list, state: str):
    '''Set the connected users and state for the match in Redis'''
    # Prepare the match data as a JSON string
    match_data = {
        MatchSessionFields.STATE: state,
        MatchSessionFields.CONNECTED_USERS: connected_users,
    }

    # Store the match data in the MATCHES_OPEN hash
    await sync_to_async(redis_instance.hset)(RedisKeys.MATCHES_OPEN, match_id, json.dumps(match_data))


###########
#   BOOL  #
###########

###########
# DELETE  #
###########

###########
#  MISC   #
###########


async def increment_connection_count(match_id):
    '''Increment the connection count for the game'''
    await sync_to_async(redis_instance.incr)(f"game:{match_id}:connections")


async def decrement_connection_count(match_id):
    '''Decrement the connection count for the game'''
    await sync_to_async(redis_instance.decr)(f"game:{match_id}:connections")

####################################################################################################
#                                   PUBLISH & SUBSCRIPTION FUNCTIONS                               #
####################################################################################################

async def publish_match_state_channel(match_id, state):
    '''Publish the game state to the Redis channel'''
    await sync_to_async(redis_instance.publish)(f"game:{match_id}:channel", state)


async def subscribe_to_match_state_channel(pubsub, match_id):
    '''Subscribe to the game state channel'''
    await sync_to_async(pubsub.subscribe)(f"game:{match_id}:channel")


async def unsubscribe_from_match_state_channel(pubsub, match_id):
    '''Unsubscribe from the game state channel'''
    await sync_to_async(pubsub.unsubscribe)(f"game:{match_id}:channel")


####################################################################################################
#                                   USER SESSION FUNCTIONS                                         #
####################################################################################################3

###########
# GETTERS #
###########

from asgiref.sync import sync_to_async

async def get_user_last_login(user_id):
    '''Get the last login time of the user'''
    last_login = await sync_to_async(redis_instance.hget)(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.LAST_LOGIN)
    if last_login:
        return int(last_login)  # Convert bytes to integer
    return None


async def get_user_match_id(user_id):
    '''Get the last match ID of the user'''
    last_match_id = await sync_to_async(redis_instance.hget)(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.LAST_MATCH_ID)
    if last_match_id:
        return last_match_id.decode('utf-8')  # Convert bytes to string
    return None


async def get_user_online_status(user_id):
    '''Get the online status of the user'''
    online_status = await sync_to_async(redis_instance.hget)(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.ONLINE_STATUS)
    if online_status:
        return online_status.decode('utf-8')  # Convert bytes to string
    return None


###########
# SETTERS #
###########

async def set_user_session_info(user_id, online_status, last_match_id, ttl=3600):
    '''Set user session information in Redis using a hash'''
    user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
    
    # Prepare the user information dictionary
    user_info = {
        UserSessionFields.ONLINE_STATUS: online_status,  # online, in_queue, playing, offline
        UserSessionFields.LAST_LOGIN: int(time.time())   # Timestamp of the last login
    }
    
    # Add last_match_id only if it's not None
    if last_match_id is not None:
        user_info['last_match_id'] = last_match_id
    
    # Store each field in the Redis hash
    await sync_to_async(redis_instance.hset)(user_key, mapping=user_info)
    
    # Set an expiration time for the hash
    await sync_to_async(redis_instance.expire)(user_key, ttl)


async def set_user_match_id(user_id, match_id):
    '''Set the last match ID for the user within the user session hash'''
    try:
        # Define the key for the user session hash
        user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
        
        # Store the match_id in the hash
        await sync_to_async(redis_instance.hset)(
            user_key, UserSessionFields.LAST_MATCH_ID, match_id
        )
    except Exception as e:
        logger.error(f"Error setting match ID for user {user_id}: {e}")
        raise SuspiciousOperation("Error updating user match ID in Redis.")


async def set_user_online_status(user_id, online_status):
    '''Set the online status of the user'''
    try:
        # Define the key for the user session hash
        user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
        
        # Store the online_status in the hash
        await sync_to_async(redis_instance.hset)(
            user_key, UserSessionFields.ONLINE_STATUS, online_status
        )
    except Exception as e:
        logger.error(f"Error setting online status for user {user_id}: {e}")
        raise SuspiciousOperation("Error updating user online status in Redis.")


async def set_user_last_login(user_id):
    '''Set the last login time of the user'''
    try:
        # Define the key for the user session hash
        user_key = f"{RedisKeys.USER_SESSION}:{user_id}"
        
        # Store the current timestamp in the hash
        await sync_to_async(redis_instance.hset)(
            user_key, UserSessionFields.LAST_LOGIN, int(time.time())
        )
    except Exception as e:
        logger.error(f"Error setting last login for user {user_id}: {e}")
        raise SuspiciousOperation("Error updating user last login time in Redis.")


###########
#   BOOL  #
###########

async def is_user_playing(user_id):
    '''Check if the user is currently playing a game'''
    return await get_user_online_status(user_id) == UserOnlineStatus.PLAYING


###########
# DELETE  #
###########

###########
#  MISC   #
###########
