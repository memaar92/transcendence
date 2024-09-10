import json
import redis
import asyncio
from ..services.redis_service.pub_sub_manager import PubSubManager as rsPubSub
from ..services.redis_service.match import Match as rsMatch
from ..services.redis_service.user import User as rsUser
from ..services.redis_service.constants import REDIS_INSTANCE
from channels.generic.websocket import AsyncWebsocketConsumer
from ..services.redis_service.constants import MatchState, UserGameStatus, MatchOutcome

import logging
logger = logging.getLogger("PongConsumer")

class MatchConsumer(AsyncWebsocketConsumer):

    broadcast_tasks = {}
    broadcast_locks = {}
    match_state_tasks = {}

    MAX_RECONNECT_ATTEMPTS = 3

    def __init__(self):
        super().__init__()
        self.groups = []
        self.match_id = None
        self.user_id = None
        self.pubsub = None
        self.current_state = None
        self.disconnect_timer_task = None
        self.connection_established = False

    async def connect(self):
        # Extracting the match_id from the URL route parameters
        self.match_id = self.scope['url_route']['kwargs']['match_id']

        # Extracting the user_id from the scope
        self.user_id = self.scope["user"].id

        # Check if the connection is valid
        if not await self.is_valid_connection(self.match_id, self.user_id):
            await self.close()
            logger.info(f"User {self.user_id} is not allowed to connect to match {self.match_id}")
            return

        # Initialize pubsub connection
        self.pubsub = REDIS_INSTANCE.pubsub()

        # Establish the connection and set up the necessary tasks
        await self._establish_connection()

    async def disconnect(self, close_code):

        await rsUser.set_online_status(self.user_id, UserGameStatus.AVAILABLE)
        
        # Run the disconnect logic only if the connection was established
        if not self.connection_established:
            return
        
        # Handle user disconnecting from the match
        logger.info(f"Users left in match {self.match_id}: {await rsMatch.Users.Connected.count(self.match_id)}")
        await rsUser.set_online_status(self.user_id, UserGameStatus.AVAILABLE)
        logger.info(f"User {self.user_id} disconnected from match {self.match_id}")
        await self.channel_layer.group_discard(self.match_id, self.channel_name)
        await rsMatch.disconnect_user(self.match_id, self.user_id)

        # Check if there are any listeners left
        if await rsMatch.Users.Connected.count(self.match_id) == 0:
            # Perform necessary cleanup
            logger.info(f"No connected Users left for match {self.match_id}")
            await rsMatch.set_state(self.match_id, MatchState.FINISHED)
            self._cleanup_match_resources()
        else:
            if self.current_state != MatchState.FINISHED:
                await self._change_match_state(MatchState.PAUSED)
                logger.info(f"Match {self.match_id} is {self.current_state}")

    async def receive(self, text_data):
        # data = json.loads(text_data)
        
        # # Update match state in Redis
        # REDIS_INSTANCE.set(f"match:{self.match_id}:state", text_data)
        
        # # Broadcast match state to all players
        # await self.channel_layer.group_send(
        #     self.match_id,
        #     {
        #         'type': 'match_update',
        #         'data': data
        #     }
        # )
        pass

    async def _establish_connection(self):
        # Add the connection to the channel group for this match
        await self.channel_layer.group_add(self.match_id, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()
        self.connection_established = True
        await rsMatch.increment_reconnection_attempts(self.match_id, self.user_id)
        logger.info(f"Reconnect attempts for user {self.user_id} in match {self.match_id}: {await rsMatch.get_reconnect_attempts(self.match_id, self.user_id)}")

        # Set user_id, match_id and online status for connected user in Redis
        await rsUser.set_online_status(self.user_id, UserGameStatus.PLAYING)
        await rsUser.set_match_id(self.user_id, self.match_id)

        # Connect the user to the match in Redis
        await rsMatch.connect_user(self.match_id, self.user_id)
        logger.info(f"User {self.user_id} connected to match {self.match_id}")

        # Initialize lock for the match_id if not already present
        if self.match_id not in MatchConsumer.broadcast_locks:
            MatchConsumer.broadcast_locks[self.match_id] = asyncio.Lock()

        # Create tasks for the match
        await self._create_tasks()

    async def _create_tasks(self):
        # Create a broadcast task for the match if not already present
        async with MatchConsumer.broadcast_locks[self.match_id]:
            if self.match_id not in MatchConsumer.broadcast_tasks:
                MatchConsumer.broadcast_tasks[self.match_id] = asyncio.create_task(self.broadcast_match_data())
                # MatchConsumer.match_state_tasks[self.match_id] = asyncio.create_task(self.state_change_listener())
                # Subscribe to the match state channel
                await rsPubSub.subscribe_to_match_state_channel(REDIS_INSTANCE, self.match_id, self.state_change_listener)
            else:
                await rsMatch.set_state(self.match_id, MatchState.RUNNING)

    async def _cleanup_match_resources(self):
        # Remove the connection from the channel group
        await self.channel_layer.group_discard(self.match_id, self.channel_name)

        # Set user_id, match_id and online status for connected user in Redis
        await rsUser.set_online_status(self.user_id, UserGameStatus.AVAILABLE)
        # await rsUser.set_match_id(self.user_id, None)

        # Unsuscribe from the match state channel
        await rsPubSub.unsubscribe_from_match_state_channel(REDIS_INSTANCE, self.match_id, self.state_change_listener)

        # Check if there are any listeners left
        if self.match_id in MatchConsumer.broadcast_locks:
                async with MatchConsumer.broadcast_locks[self.match_id]:
                    if self.match_id in MatchConsumer.broadcast_tasks:
                        MatchConsumer.broadcast_tasks[self.match_id].cancel()
                        del MatchConsumer.broadcast_tasks[self.match_id]
                        del MatchConsumer.match_state_tasks[self.match_id]
                    # Delete the lock for the match_id
                    del MatchConsumer.broadcast_locks[self.match_id]

    async def match_update(self, event):
        # Send match update to WebSocket
        await self.send(text_data=json.dumps(event['data']))

    async def broadcast_match_data(self):
        previous_state = None
        while True:
            if self.current_state == MatchState.RUNNING:
                if previous_state != MatchState.RUNNING:
                    if self.disconnect_timer_task:
                        self.disconnect_timer_task.cancel()
                        self.disconnect_timer_task = None
                    previous_state = MatchState.RUNNING
                    await self.channel_layer.group_send(
                        self.match_id,
                        {
                            'type': 'match_update',
                            'data': {'state': 'running'}
                        }
                    )
            elif self.current_state == MatchState.PAUSED:
                if previous_state != MatchState.PAUSED:
                    previous_state = MatchState.PAUSED
                    await self.channel_layer.group_send(
                        self.match_id,
                        {
                            'type': 'match_update',
                            'data': {'state': 'paused'}
                        }
                    )
                    await self.handle_player_disconnect()
            elif self.current_state == MatchState.FINISHED:
                if previous_state != MatchState.FINISHED:
                    previous_state = MatchState.FINISHED
                    await self.channel_layer.group_send(
                        self.match_id,
                        {
                            'type': 'match_update',
                            'data': {'state': 'finished'}
                        }
                    )           
            await asyncio.sleep(0.1)


    async def state_change_listener(self, message):
        logger.info(f"state_change_listener TRIGGERED: {message}")
        # await rsMatch.set_state(self.match_id, message['data'].decode('utf-8'))
        logger.info(f"State in redis: {await rsMatch.get_state(self.match_id)}")
        # loop = asyncio.get_event_loop()
        # while True:
        #     message = await loop.run_in_executor(None, self.pubsub.get_message, True, None)
        #     if message:
        #         logger.info(f"state_change_listener TRIGGERED: {message}")
        #         if message['type'] == 'message':
        #             self.current_state = message['data'].decode('utf-8')
        #     await asyncio.sleep(0.01)  # Sleep briefly to avoid busy-waiting

    async def _change_match_state(self, state: MatchState):
        self.current_state = state
        await rsMatch.set_state(self.match_id, state)
                        
    async def handle_player_disconnect(self):
        logger.info("Disconnect handler TRIGGERED")
        if self.disconnect_timer_task:
            self.disconnect_timer_task.cancel()
        
        self.disconnect_timer_task = asyncio.create_task(self.start_disconnect_timer())

    async def start_disconnect_timer(self):
        try:
            await asyncio.sleep(5)  # 30-second timer
            await self.handle_disconnect_timeout()
        except asyncio.CancelledError:
            logger.info("Disconnect timer cancelled")

    async def handle_disconnect_timeout(self):
        logger.info("Player did not reconnect in time. Declaring the other player as the winner.")
        logger.info(f"Player {self.user_id} is declared as the winner.")
        await self.channel_layer.group_send(
            self.match_id,
            {
                'type': 'match_update',
                'data': {'state': 'finished', 'winner': self.user_id}
            }
        )
        await rsMatch.set_outcome(self.match_id, MatchOutcome.NORMAL, self.user_id)
        await self._change_match_state(MatchState.FINISHED)
        await self.disconnect(1000)

    async def is_valid_connection(self, match_id, user_id):

        # User is not authenticated
        if self.user_id is None:
            logger.info("User not authenticated")
            return False
        
        # Convert user_id to string for use in Redis
        self.user_id = str(self.user_id)

        # No Match ID provided
        if self.match_id is None:
            logger.info("Match ID not provided")
            return False
        
        # Match ID is not a string
        if not isinstance(self.match_id, str):
            logger.info("Match ID is not a string")
            return False
        
        # Match ID does not exist
        if not await rsMatch.exists(self.match_id):
            logger.info(f"Match {self.match_id} not found")
            return False
        
        # User is already connected to a match
        if await rsUser.is_playing(self.user_id):
            logger.info(f"User {self.user_id} is already connected to a match")
            return False

        # User is not part of the match
        if not await rsMatch.Users.Assigned.is_user_assigned(self.match_id, self.user_id):
            logger.info(f"User {self.user_id} is not part of match {self.match_id}")
            return False

        # Match is not in progress
        if not await rsMatch.is_in_progress(self.match_id):
            logger.info(f"Match {self.match_id} is not in progress")
            return False
        
        # User has exceeded the maximum reconnect attempts
        if await rsMatch.get_reconnect_attempts(self.match_id, self.user_id) >= MatchConsumer.MAX_RECONNECT_ATTEMPTS:
            logger.info(f"User {self.user_id} has exceeded the maximum reconnect attempts")
            return False

        return True
    