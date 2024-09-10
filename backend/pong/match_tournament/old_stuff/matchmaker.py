from ..services.redis_service.match import Match as rsMatch
from ..services.redis_service.user import User as rsUser
from ..services.redis_service.pub_sub_manager import PubSubManager as rsPubSub
from ..services.redis_service.constants import REDIS_INSTANCE
from ..services.redis_service.constants import MatchState, UserGameStatus, MatchOutcome
from uuid import uuid4
from threading import Thread
import time
import logging
import asyncio

logger = logging.getLogger("PongConsumer")


def run_async_in_thread(async_func, *args):
    '''Helper function to run an async function in a new event loop in a separate thread'''
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_func(*args))
    loop.close()

class MatchMaker:

    REGISTRATION_TIMEOUT = 5 # seconds, time to wait for both users to register for a match
    GAMESTART_TIMEOUT = 2 # seconds, time to wait for the game to start after registration
    pubsub = REDIS_INSTANCE.pubsub()

    def __init__(self):
        pass

    class MatchError(Exception):
        '''Base class for all match-related exceptions'''
        pass

    class UserAlreadyInGameError(MatchError):
        def __init__(self, user_id: str):
            self.user_id = user_id
            self.message = f"User(s) {user_id} is already in a game"
        
        def __str__(self):
            return self.message
            
    @classmethod
    async def _monitor_registration_timeout(cls, match_id: str) -> None:
        '''Monitor the registration timeout for a match'''
        if not await rsMatch.exists(match_id):
            logger.info(f"Match {match_id} does not exist")
            return
        creation_time = await rsMatch.get_creation_time(match_id)
        assigned_users = await rsMatch.Users.Assigned.get(match_id)
        if len(assigned_users) != 2:
            logger.info(f"Match {match_id} does not have exactly 2 assigned users")
            return
        if not creation_time:
            logger.info(f"Match {match_id} between {assigned_users[0]} and {assigned_users[1]} no creation time found")
            return
        
        while True:
            current_time = time.time()
            if current_time - creation_time > cls.REGISTRATION_TIMEOUT:
                logger.info(f"Match {match_id} between {assigned_users[0]} and {assigned_users[1]} did not register in time and will be deleted")
                await rsPubSub.publish_to_channel(f"{match_id}:registration", "registration_timeout")
                await rsMatch.delete(match_id)
                break
            if await rsMatch.Users.Registered.registration_complete(match_id):
                break
            await asyncio.sleep(1)

    @classmethod
    async def _monitor_gamestart_timeout(cls, match_id: str) -> None:
        '''Monitor the game start timeout for a match'''
        creation_time = await rsMatch.get_creation_time(match_id)
        if not creation_time:
            raise cls.MatchError("No creation time found for match")
        
        assigned_users = await rsMatch.Users.Assigned.get(match_id)
        if len(assigned_users) != 2:
            logger.info(f"Match {match_id} does not have exactly 2 assigned users")
            return
        while True:
            current_time = time.time()
            if current_time - creation_time > cls.GAMESTART_TIMEOUT:
                logger.info(f"Match {match_id} between {assigned_users[0]} and {assigned_users[1]} did not start in time and will be deleted")
                await rsPubSub.publish_to_channel(f"{match_id}:registration", "registration_timeout")
                await rsMatch.delete(match_id)
                break
            if await rsMatch.get_state(match_id) != MatchState.INITIALIZING:
                break
            await asyncio.sleep(1)

    @classmethod
    async def _monitor_game_connections(cls, match_id: str) -> None:
        '''Monitor the game connections for a match'''
        creation_time = await rsMatch.get_creation_time(match_id)
        if not creation_time:
            raise cls.MatchError("No creation time found for match")
        
        assigned_users = await rsMatch.Users.Assigned.get(match_id)
        if len(assigned_users) != 2:
            logger.info(f"Match {match_id} does not have exactly 2 assigned users")
            return
        while True:
            current_time = time.time()
            if current_time - creation_time > cls.GAMESTART_TIMEOUT:
                logger.info(f"Match {match_id} between {assigned_users[0]} and {assigned_users[1]} did not start in time: DRAW")
                await rsPubSub.publish_to_channel(f"MatchOutcome:{match_id}", MatchOutcome.DRAW)
                break
            if await rsMatch.Users.Connected.count(match_id) > 0:
                break
            await asyncio.sleep(1)
    
    @classmethod
    async def generate_match(cls, user_id_1: str, user_id_2: str) -> str:
        '''Request a match between two users, returns match_id'''

        # Create a match
        match_id = str(uuid4())
        await rsMatch.create(match_id, [user_id_1, user_id_2])

        # Schedule the _monitor_game_connections coroutine in the event loop
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(cls._monitor_game_connections(match_id), loop)

        return match_id

    @classmethod
    async def register_user(cls, match_id: str, user_id: str) -> None:
        logger.info(f"Registering user {user_id} for match {match_id} in MatchMaker")
        '''Register a user for a match, can raise MatchError'''
        if not await rsMatch.exists(match_id):
            raise cls.MatchError("Match does not exist")
        if await rsMatch.is_user_connected(match_id, user_id):
            raise cls.MatchError("User is already connected to the match")
        if not await rsMatch.is_user_assigned(match_id, user_id):
            raise cls.MatchError("User is not assigned to this match")
        await rsMatch.register_user(match_id, user_id)
        if await rsMatch.Users.Registered.registration_complete(match_id):
            logger.info(f"Match {match_id} is ready to start")
            await rsMatch.set_state(match_id, MatchState.INITIALIZING)
            await rsMatch.set_creation_time(match_id, time.time())
            game_start_thread = Thread(target=run_async_in_thread, args=(cls._monitor_gamestart_timeout, match_id,))
            game_start_thread.start()

    @classmethod
    async def is_registration_complete(cls, match_id: str) -> bool:
        '''Check if the registration for a match is complete'''
        return await rsMatch.Users.Registered.registration_complete(match_id)
    
    @classmethod
    async def is_user_available(cls, user_id: str) -> bool:
        '''Check if a user is available for matchmaking'''
        return not await rsUser.is_playing(user_id)
    
    @classmethod
    async def lock_user(cls, user_id: str) -> None:
        '''Lock a user for matchmaking'''
        await rsUser.set_online_status(user_id, UserGameStatus.IN_QUEUE)

    @classmethod
    async def unlock_user(cls, user_id: str) -> None:
        '''Remove a user from the matchmaking queue'''
        await rsUser.set_online_status(user_id, UserGameStatus.AVAILABLE)