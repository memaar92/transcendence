import logging
from asgiref.sync import sync_to_async
from django.core.exceptions import SuspiciousOperation
import json
import time
from typing import List, Any, Union, Optional
import redis
from ..utils.states import UserOnlineStatus, MatchState

redis_instance = redis.StrictRedis(host='redis', port=6379, db=0)

logger = logging.getLogger("PongConsumer")


class RedisKeys:
    USER_SESSION = "user:session"
    MATCHES_OPEN = "matches:open"

class QueueFields:
    MATCHMAKING_QUEUE = "matchmaking_queue"

class MatchSessionFields:
    CONNECTED_USERS = "connected_users"
    STATE = "state"
    RECONNECTION_ATTEMPTS = "reconnection_attempts"

class UserSessionFields:
    LAST_MATCH_ID = "last_match_id"
    ONLINE_STATUS = "online_status"
    LAST_LOGIN = "last_login"



class Match:

    ###########
    # GETTERS #
    ###########

    @staticmethod
    async def get_connected_users(match_id: str) -> List[str]:
        '''Get the connected users for the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                user_ids = match_data.get(MatchSessionFields.CONNECTED_USERS, [])
                
                # Check the online status of each user
                # and add them to the connected_users list if they are playing
                connected_users = [
                    user_id for user_id in user_ids
                    if await User.get_online_status(user_id) == UserOnlineStatus.PLAYING and await User.get_match_id(user_id) == match_id
                ]
                return connected_users
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error decoding match data: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        return []

    @staticmethod
    async def get_connected_users_count(match_id: str) -> int:
        '''Get the connected users count for the match'''
        return len(await Match.get_connected_users(match_id))

    @staticmethod
    async def get_user_ids(match_id: str) -> List[str]:
        '''Get the connected users for the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                return match_data.get(MatchSessionFields.CONNECTED_USERS, [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error decoding match data: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        return []

    @staticmethod
    async def get_match_state(match_id: str) -> Union[str, None]:
        '''Get the state of the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                return match_data.get(MatchSessionFields.STATE, MatchState.FINISHED)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error decoding match data: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        return MatchState.FINISHED

    @staticmethod
    async def get_reconnect_attempts(match_id: str, user_id: str) -> Optional[int]:
        '''Retrieve the number of reconnection attempts for a user in a match'''
        try:
            # Retrieve the match data from the MATCHES_OPEN hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json is None:
                return None
            
            # Parse the JSON string to a dictionary
            match_data = json.loads(match_data_json)
            
            # Get the reconnection attempts for the user
            user_data = match_data.get(user_id)
            if user_data is None:
                return None
            
            return user_data.get(MatchSessionFields.RECONNECTION_ATTEMPTS, 0)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    ###########
    # SETTERS #
    ###########

    @staticmethod
    async def initialize(match_id: str, connected_users: List[str]) -> None:
        '''Set the connected users and state for the match in Redis'''
        try:
            # Prepare the match data as a JSON string
            match_data = {
                MatchSessionFields.STATE: MatchState.INITIALIZING,
                MatchSessionFields.CONNECTED_USERS: connected_users,
            }

            # Add reconnection_attempts for each connected user
            for user in connected_users:
                match_data[user] = {MatchSessionFields.RECONNECTION_ATTEMPTS: -1} # -1 indicates the user is not reconnected

            # Store the match data in the MATCHES_OPEN hash
            await sync_to_async(redis_instance.hset)(RedisKeys.MATCHES_OPEN, match_id, json.dumps(match_data))
        except Exception as e:
            print(f"Unexpected error: {e}")

    @staticmethod
    async def set_state(match_id: str, state: str) -> None:
        '''Set the state of the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                match_data[MatchSessionFields.STATE] = state
                
                # Store the updated match data in the Redis hash
                await sync_to_async(redis_instance.hset)(RedisKeys.MATCHES_OPEN, match_id, json.dumps(match_data))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error decoding match data: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    @staticmethod
    async def add_user(match_id: str, user_id: str) -> None:
        '''Add the user to the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                connected_users = match_data.get(MatchSessionFields.CONNECTED_USERS, [])
                
                # Add the user to the connected_users list
                connected_users.append(user_id)
                match_data[MatchSessionFields.CONNECTED_USERS] = connected_users
                
                # Store the updated match data in the Redis hash
                await sync_to_async(redis_instance.hset)(RedisKeys.MATCHES_OPEN, match_id, json.dumps(match_data))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error decoding match data: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    @staticmethod
    async def remove_user(match_id: str, user_id: str) -> None:
        '''Remove the user from the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                connected_users = match_data.get(MatchSessionFields.CONNECTED_USERS, [])
                
                # Remove the user from the connected_users list
                connected_users.remove(user_id)
                match_data[MatchSessionFields.CONNECTED_USERS] = connected_users
                
                # Store the updated match data in the Redis hash
                await sync_to_async(redis_instance.hset)(RedisKeys.MATCHES_OPEN, match_id, json.dumps(match_data))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error decoding match data: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    

    ###########
    #   BOOL  #
    ###########

    @staticmethod
    async def is_alive(match_id: str) -> bool:
        '''Check if the match is still alive'''
        return await Match.get_connected_users_count(match_id) > 0 and await Match.get_match_state(match_id) != MatchState.FINISHED
    
    @staticmethod
    async def exists(match_id: str) -> bool:
        '''Check if the match exists in the Redis database'''
        return await sync_to_async(redis_instance.hexists)(RedisKeys.MATCHES_OPEN, match_id) == 1
    
    @staticmethod
    async def is_user_part_of_match(match_id: str, user_id: str) -> bool:
        '''Check if the user is part of the match'''
        return user_id in await Match.get_user_ids(match_id)
    
    @staticmethod
    async def is_user_connected(match_id: str, user_id: str) -> bool:
        '''Check if the user is connected to the match'''
        return user_id in await Match.get_connected_users(match_id)
    
    @staticmethod
    async def is_match_in_progress(match_id: str) -> bool:
        '''Check if the match is in progress'''
        state = await Match.get_match_state(match_id)
        return state == MatchState.RUNNING or state == MatchState.PAUSED or state == MatchState.INITIALIZING

    ###########
    # DELETE  #
    ###########

    ###########
    #  MISC   #
    ###########

    @staticmethod
    async def increment_reconnection_attempts(match_id: str, user_id: str) -> bool:
        '''Increment the number of reconnection attempts for a user in a match'''
        try:
            # Retrieve the match data from the MATCHES_OPEN hash
            match_data_json = await sync_to_async(redis_instance.hget)(RedisKeys.MATCHES_OPEN, match_id)
            
            if match_data_json is None:
                return False
            
            # Parse the JSON string to a dictionary
            match_data = json.loads(match_data_json)
            
            # Increment the reconnection attempts for the user
            if user_id in match_data:
                match_data[user_id][MatchSessionFields.RECONNECTION_ATTEMPTS] += 1
            else:
                match_data[user_id] = {MatchSessionFields.RECONNECTION_ATTEMPTS: 1}
            
            # Store the updated match data back in the MATCHES_OPEN hash
            await sync_to_async(redis_instance.hset)(RedisKeys.MATCHES_OPEN, match_id, json.dumps(match_data))
            
            return True
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

class PubSub:

    @staticmethod
    async def publish_match_state_channel(match_id: str, state: str) -> None:
        '''Publish the match state to the Redis channel'''
        try:
            channel = f"{RedisKeys.MATCHES_OPEN}:{match_id}:{MatchSessionFields.STATE}"
            await sync_to_async(redis_instance.publish)(channel, state)
        except Exception as e:
            print(f"Error publishing to channel: {e}")

    @staticmethod
    async def subscribe_to_match_state_channel(pubsub: Any, match_id: str) -> None:
        '''Subscribe to the match state channel'''
        try:
            channel = f"{RedisKeys.MATCHES_OPEN}:{match_id}:{MatchSessionFields.STATE}"
            await sync_to_async(pubsub.subscribe)(channel)
        except Exception as e:
            print(f"Error subscribing to channel: {e}")

    @staticmethod
    async def unsubscribe_from_match_state_channel(pubsub: Any, match_id: str) -> None:
        '''Unsubscribe from the match state channel'''
        try:
            channel = f"{RedisKeys.MATCHES_OPEN}:{match_id}:{MatchSessionFields.STATE}"
            await sync_to_async(pubsub.unsubscribe)(channel)
        except Exception as e:
            print(f"Error unsubscribing from channel: {e}")



class User:

    ###########
    # GETTERS #
    ###########

    @staticmethod
    async def get_last_login(user_id: str) -> Optional[int]:
        '''Get the last login time of the user'''
        last_login = await sync_to_async(redis_instance.hget)(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.LAST_LOGIN)
        if last_login:
            return int(last_login)  # Convert bytes to integer
        return None

    @staticmethod
    async def get_match_id(user_id: str) -> Optional[str]:
        '''Get the last match ID of the user'''
        last_match_id = await sync_to_async(redis_instance.hget)(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.LAST_MATCH_ID)
        if last_match_id:
            return last_match_id.decode('utf-8')  # Convert bytes to string
        return None

    @staticmethod
    async def get_online_status(user_id: str) -> Optional[str]:
        '''Get the online status of the user'''
        online_status = await sync_to_async(redis_instance.hget)(f"{RedisKeys.USER_SESSION}:{user_id}", UserSessionFields.ONLINE_STATUS)
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
        await sync_to_async(redis_instance.hset)(user_key, mapping=user_info)
        
        # Set an expiration time for the hash
        await sync_to_async(redis_instance.expire)(user_key, ttl)

    @staticmethod
    async def set_match_id(user_id: str, match_id: str) -> None:
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

    @staticmethod
    async def set_online_status(user_id: str, online_status: str) -> None:
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

    @staticmethod
    async def set_last_login(user_id: str) -> None:
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

    @staticmethod
    async def is_playing(user_id: str) -> bool:
        '''Check if the user is currently playing a match'''
        return await User.get_online_status(user_id) == UserOnlineStatus.PLAYING
    
    @staticmethod
    async def exists(user_id: str) -> bool:
        '''Check if the user exists in the Redis database'''
        return await sync_to_async(redis_instance.exists)(f"{RedisKeys.USER_SESSION}:{user_id}") == 1

    ###########
    # DELETE  #
    ###########

    ###########
    #  MISC   #
    ###########

class MatchmakingQueue:

    @staticmethod
    async def remove_user(user_id: str) -> None:
        '''Remove the user from the matchmaking queue'''
        if user_id:
            await sync_to_async(redis_instance.lrem)(QueueFields.MATCHMAKING_QUEUE, 0, user_id)
            await User.set_online_status(user_id, UserOnlineStatus.ONLINE)
    
    @staticmethod
    async def add_user(user_id: str) -> None:
        '''Add the user to the matchmaking queue'''
        if user_id:
            await sync_to_async(redis_instance.rpush)(QueueFields.MATCHMAKING_QUEUE, user_id)
            await User.set_online_status(user_id, UserOnlineStatus.IN_QUEUE)
    
    @staticmethod
    async def get_queue_length() -> int:
        '''Get the length of the matchmaking queue'''
        return await sync_to_async(redis_instance.llen)(QueueFields.MATCHMAKING_QUEUE)
    
    @staticmethod
    async def pop_next_user() -> Optional[str]:
        '''Pop the next user from the matchmaking queue'''
        user_id = await sync_to_async(redis_instance.lpop)(QueueFields.MATCHMAKING_QUEUE)
        if user_id:
            return user_id.decode('utf-8')
        return None
    
    @staticmethod
    async def is_user_id_in_queue(user_id: str) -> bool:
        '''Check if the user_id is in the matchmaking queue'''
        return await sync_to_async(redis_instance.lpos)(QueueFields.MATCHMAKING_QUEUE, user_id) is not None