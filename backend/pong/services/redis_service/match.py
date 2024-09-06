import json
import logging
import time
from typing import Any, Callable, List, Optional, Union
from .constants import RedisKeys, MatchSessionFields, MatchState, MatchOutcome, REDIS_INSTANCE, GeneralChannels
from .pub_sub_manager import PubSubManager as rsPubSub
from redis.asyncio import WatchError

logger = logging.getLogger("PongConsumer")

class Match:

    class Users:

        class Connected:

            @staticmethod
            async def get(match_id: str) -> List[str]:
                '''Get the connected users for the match'''
                try:
                    # Retrieve the match data from the Redis hash
                    match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
                    
                    if match_data_json:
                        # Decode the JSON string back to a Python dictionary
                        match_data = json.loads(match_data_json)
                        if match_data is None:
                            return []
                        connected_user_ids = match_data.get(MatchSessionFields.CONNECTED_USERS, [])
                        
                        return connected_user_ids
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error decoding match data: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                
                return []

            @staticmethod
            async def count(match_id: str) -> int:
                '''Get the connected users count for the match'''
                return len(await Match.Users.Connected.get(match_id))
            
            @staticmethod
            async def is_user_connected(match_id: str, user_id: str) -> bool:
                '''Check if the user is connected to the match'''
                return user_id in await Match.Users.Connected.get(match_id)
                        
        class Assigned:

            @staticmethod
            async def get(match_id: str) -> List[str]:
                '''Get the assigned users for the match'''
                try:
                    # Retrieve the match data from the Redis hash
                    match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
                    
                    if match_data_json:
                        # Decode the JSON string back to a Python dictionary
                        match_data = json.loads(match_data_json)
                        return match_data.get(MatchSessionFields.ASSIGNED_USERS, [])
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error decoding match data: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                
                return []

            @staticmethod        
            async def count(match_id: str) -> int:
                '''Get the assigned users count for the match'''
                return len(await Match.Users.Assigned.get(match_id))
        
            @staticmethod
            async def is_user_assigned(match_id: str, user_id: str) -> bool:
                '''Check if the user is assigned to the match'''
                return user_id in await Match.Users.Assigned.get(match_id)
            
        class Registered:
            
            @staticmethod
            async def get(match_id: str) -> List[str]:
                '''Get the registered users for the match'''
                try:
                    # Retrieve the match data from the Redis hash
                    match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
                    
                    if match_data_json:
                        # Decode the JSON string back to a Python dictionary
                        match_data = json.loads(match_data_json)
                        return match_data.get(MatchSessionFields.REGISTERED_USERS, [])
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error decoding match data: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                
                return []

            @staticmethod
            async def count(match_id: str) -> int:
                '''Get the registered users count for the match'''
                return len(await Match.Users.Registered.get(match_id))
            
            @staticmethod
            async def is_user_registered(match_id: str, user_id: str) -> bool:
                '''Check if the user is registered for the match'''
                return user_id in await Match.Users.Registered.get(match_id)
            
            @staticmethod
            async def registration_complete(match_id: str) -> bool:
                '''Check if all assigned users have registered for the match'''
                assigned_users = await Match.Users.Assigned.get(match_id)
                registered_users = await Match.Users.Registered.get(match_id)
                
                return len(assigned_users) == len(registered_users)

    ###########
    # GETTERS #
    ###########

    @staticmethod
    async def get_state(match_id: str) -> Union[str, None]:
        '''Get the state of the match, FINISHED by default'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                return match_data.get(MatchSessionFields.STATE, MatchState.FINISHED)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        return MatchState.FINISHED

    @staticmethod
    async def get_creation_time(match_id: str) -> Optional[int]:
        '''Get the creation time of the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            logger.info(f"Match data get_creation_time: {match_data_json}")
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                return match_data.get(MatchSessionFields.CREATION_TIME)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        return None

    @staticmethod
    async def get_reconnect_attempts(match_id: str, user_id: str) -> Optional[int]:
        '''Retrieve the number of reconnection attempts for a user in a match'''
        try:
            # Retrieve the match data from the MATCHES hash
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json is None:
                return None
            
            # Parse the JSON string to a dictionary
            match_data = json.loads(match_data_json)
            
            # Ensure match_data is a dictionary
            if not isinstance(match_data, dict):
                logger.error(f"Invalid match data format for match_id: {match_id}")
                return None
            
            # Get the user data
            user_data = match_data.get(user_id)
            
            # Ensure user_data is a dictionary
            if not isinstance(user_data, dict):
                return None
            
            # Get the reconnection attempts for the user
            return user_data.get(MatchSessionFields.RECONNECTION_ATTEMPTS, 0)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    @staticmethod
    async def get_outcome(match_id: str) -> Optional[str]:
        '''Get the outcome of the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                return match_data.get(MatchSessionFields.OUTCOME)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        return None

    ###########
    # SETTERS #
    ###########

    @staticmethod
    async def create(match_id: str, assigned_users: List[str]) -> None:
        '''Create a match in Redis'''
        try:
            # Prepare the match data as a JSON string
            match_data = {
                MatchSessionFields.STATE: MatchState.INITIALIZING,
                MatchSessionFields.CREATION_TIME: int(time.time()),
                MatchSessionFields.OUTCOME: None,
                MatchSessionFields.ASSIGNED_USERS: assigned_users,
                MatchSessionFields.REGISTERED_USERS: [],
                MatchSessionFields.CONNECTED_USERS: [],
            }

            # Serialize match_data to JSON string
            match_data_json = json.dumps(match_data)
    
            # Add reconnection_attempts for each connected user
            for user in assigned_users:
                match_data[user] = {MatchSessionFields.RECONNECTION_ATTEMPTS: -1} # -1 indicates the user is not reconnected
    
            # Store the match data in the MATCHES hash
            await REDIS_INSTANCE.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))

            # Publish the match data to the NEW_MATCH channel
            await rsPubSub.publish_to_channel(GeneralChannels.NEW_MATCH, match_data_json)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


    @staticmethod
    async def delete(match_id: str) -> None:
        '''Delete the match from Redis'''
        await REDIS_INSTANCE.hdel(RedisKeys.MATCHES, match_id)

    @staticmethod
    async def set_state(match_id: str, state: str) -> None:
        '''Set the state of the match'''
        try:
            # Retrieve the match data from the Redis hash
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json:
                # Decode the JSON string back to a Python dictionary
                match_data = json.loads(match_data_json)
                match_data[MatchSessionFields.STATE] = state
                
                # Store the updated match data in the Redis hash
                await REDIS_INSTANCE.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))

                # Publish the updated match state to the MATCH_STATE channel
                await rsPubSub.publish_match_state_channel(match_id, state)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    
    @staticmethod
    async def set_creation_time(match_id: str, creation_time: int) -> None:
        '''Set the creation time of the match'''
        try:
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json:
                match_data = json.loads(match_data_json)
                match_data[MatchSessionFields.CREATION_TIME] = creation_time
                
                await REDIS_INSTANCE.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    @staticmethod
    async def set_outcome(match_id: str, outcome: MatchOutcome) -> None:
        '''Set the outcome of the match'''
        try:
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json:
                match_data = json.loads(match_data_json)
                match_data[MatchSessionFields.OUTCOME] = outcome
                
                await REDIS_INSTANCE.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    @staticmethod
    async def connect_user(match_id: str, user_id: str) -> None:
        '''Add the user to the match'''
        try:
            async with REDIS_INSTANCE.pipeline(transaction=True) as pipe:
                while True:
                    try:
                        # Watch the match data for changes
                        await pipe.watch(RedisKeys.MATCHES)
                        
                        # Retrieve the match data
                        match_data_json = await pipe.hget(RedisKeys.MATCHES, match_id)
                        
                        if match_data_json:
                            match_data = json.loads(match_data_json)
                            connected_users = match_data.get(MatchSessionFields.CONNECTED_USERS, [])
                            
                            logger.info(f"CONNECTED USERS BEFORE: {connected_users}")
                            
                            if user_id in connected_users:
                                logger.info(f"User {user_id} is already connected to match {match_id}")
                                return
                            
                            connected_users.append(user_id)
                            match_data[MatchSessionFields.CONNECTED_USERS] = connected_users
                            
                            # Start a transaction
                            pipe.multi()
                            pipe.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))
                            
                            # Execute the transaction
                            await pipe.execute()
                            logger.info(f"CONNECTED USERS AFTER: {connected_users}")
                            break
                        else:
                            logger.warning(f"No match data found for match_id: {match_id}")
                            break
                    except WatchError:
                        # If the watched key changed, retry the transaction
                        continue
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    
    @staticmethod
    async def disconnect_user(match_id: str, user_id: str) -> None:
        '''Remove the user from the match'''
        try:
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json:
                match_data = json.loads(match_data_json)
                connected_users = match_data.get(MatchSessionFields.CONNECTED_USERS, [])
                
                connected_users.remove(user_id)
                match_data[MatchSessionFields.CONNECTED_USERS] = connected_users
                
                await REDIS_INSTANCE.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    
    @staticmethod
    async def register_user(match_id: str, user_id: str) -> None:
        '''Add the user to the match'''
        logger.info(f"Registering user {user_id} for match {match_id}")
        try:
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json:
                match_data = json.loads(match_data_json)
                registered_users = match_data.get(MatchSessionFields.REGISTERED_USERS, [])
                
                if user_id in registered_users:
                    return

                registered_users.append(user_id)
                match_data[MatchSessionFields.REGISTERED_USERS] = registered_users

                logger.info(f"Registered users: {registered_users}")
                
                await REDIS_INSTANCE.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding match data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    ###########
    #   BOOL  #
    ###########

    @staticmethod
    async def is_alive(match_id: str) -> bool:
        '''Check if the match is still alive'''
        return await Match.Users.Connected.count(match_id) > 0 and await Match.get_state(match_id) != MatchState.FINISHED
    
    @staticmethod
    async def exists(match_id: str) -> bool:
        '''Check if the match exists in the Redis database'''
        return await REDIS_INSTANCE.hexists(RedisKeys.MATCHES, match_id) == 1
    
    @staticmethod
    async def is_user_assigned(match_id: str, user_id: str) -> bool:
        '''Check if the user is part of the match'''
        return user_id in await Match.Users.Assigned.get(match_id)
    
    @staticmethod
    async def is_user_registered(match_id: str, user_id: str) -> bool:
        '''Check if the user is registered for the match'''
        return user_id in await Match.Users.Registered.get(match_id)
    
    @staticmethod
    async def is_user_connected(match_id: str, user_id: str) -> bool:
        '''Check if the user is connected to the match'''
        return user_id in await Match.Users.Connected.get(match_id)
    
    @staticmethod
    async def is_in_progress(match_id: str) -> bool:
        '''Check if the match is in progress, i.e. RUNNING, PAUSED, or INITIALIZING'''
        state = await Match.get_state(match_id)
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
            match_data_json = await REDIS_INSTANCE.hget(RedisKeys.MATCHES, match_id)
            
            if match_data_json is None:
                return False
            
            match_data = json.loads(match_data_json)
            
            if not isinstance(match_data, dict):
                logger.error(f"Invalid match data format for match_id: {match_id}")
                return False
            
            if user_id in match_data:
                if MatchSessionFields.RECONNECTION_ATTEMPTS in match_data[user_id]:
                    match_data[user_id][MatchSessionFields.RECONNECTION_ATTEMPTS] += 1
                else:
                    match_data[user_id][MatchSessionFields.RECONNECTION_ATTEMPTS] = 1
            else:
                match_data[user_id] = {MatchSessionFields.RECONNECTION_ATTEMPTS: 1}
            
            await REDIS_INSTANCE.hset(RedisKeys.MATCHES, match_id, json.dumps(match_data))
            
            return True
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False