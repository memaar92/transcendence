from ..services.redis_service.constants import REDIS_INSTANCE
from ..services.redis_service.constants import MatchState, UserGameStatus, MatchOutcome
from ..services.redis_service.user import User as rsUser
from ..services.redis_service.match import Match as rsMatch
from ..services.redis_service.pub_sub_manager import PubSubManager as rsPubSub
import time
import logging
import asyncio

logger = logging.getLogger("PongConsumer")

match_handlers = {}

class MatchHandler:

    FIRST_CONNECTION_TIMEOUT = 10

    def __init__(self, user_ids: list, match_id: str):
        self.user_ids = user_ids
        self.match_id = match_id
        match_handlers[match_id] = self

    async def start(self):
        '''Start the match'''
        await self._monitor_first_connection_timeout()


    async def _monitor_first_connection_timeout(self):
        '''Monitor the first connection timeout for a match'''
        start_time = time.time()
        while True:
            if time.time() - start_time > self.FIRST_CONNECTION_TIMEOUT:
                logger.info(f"Match {self.match_id} did not connect in time")
                await self._handle_timeout()
                break
            if await self._one_connected():
                break
            await asyncio.sleep(1)

    async def _one_connected(self):
        '''Check if at least one user is connected'''
        if rsMatch.Users.Connected.get(self.match_id):
            return True
        return False
    
    async def _handle_timeout(self):
        '''Handle the timeout for the match'''
        await rsMatch.set_state(self.match_id, MatchState.CANCELLED)
        await rsMatch.set_outcome(self.match_id, MatchOutcome.DRAW)
        for user_id in self.user_ids:
            await rsUser.set_online_status(user_id, UserGameStatus.AVAILABLE)
        await rsPubSub.publish_match_state_channel(self.match_id, MatchState.FINISHED)
        logger.info(f"Match {self.match_id} cancelled due to timeout")
        return