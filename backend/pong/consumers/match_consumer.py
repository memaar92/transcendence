import json
import redis
import asyncio
from ..services import redis_service as rs
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from ..utils.states import MatchState, UserOnlineStatus

import logging
logger = logging.getLogger("PongConsumer")

redis_instance = redis.StrictRedis(host='redis', port=6379, db=0)

class MatchConsumer(AsyncWebsocketConsumer):

    broadcast_tasks = {}
    broadcast_locks = {}
    match_states = {}

    def __init__(self):
        super().__init__()
        self.groups = []
        self.match_id = None
        self.user_id = None
        self.pubsub = None
        self.current_state = None
        self.disconnect_timer_task = None

    async def connect(self):
        # Extracting the match_id from the URL route parameters
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.user_id = self.scope["user"].id

        # Disconnect if user is not authenticated
        if self.user_id is None:
            await self.close()
            logger.info("User not authenticated")
            return
        
        # Convert user_id to string for use in Redis
        self.user_id = str(self.user_id)
        
        # Disconnect if user is already connected to a match
        if await rs.User.is_playing(self.user_id):
            await self.close()
            logger.info(f"User {self.user_id} is already connected to a match")
            return

        # Initialize pubsub connection
        self.pubsub = redis_instance.pubsub()
        
        # Subscribe to the match state channel
        await rs.PubSub.subscribe_to_match_state_channel(self.pubsub, self.match_id)

        # Add the connection to the channel group for this match
        await self.channel_layer.group_add(self.match_id, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()
        logger.info(f"User {self.user_id} connected to match {self.match_id}")

        # Set user_id, match_id and online status in Redis
        await rs.User.set_online_status(self.user_id, UserOnlineStatus.PLAYING)
        await rs.User.set_match_id(self.user_id, self.match_id)

        # Initialize lock for the match_id if not already present
        if self.match_id not in MatchConsumer.broadcast_locks:
            MatchConsumer.broadcast_locks[self.match_id] = asyncio.Lock()

        # Create a broadcast task for the match if not already present
        async with MatchConsumer.broadcast_locks[self.match_id]:
            if self.match_id not in MatchConsumer.broadcast_tasks:
                MatchConsumer.broadcast_tasks[self.match_id] = asyncio.create_task(self.broadcast_match_data())
                MatchConsumer.match_states[self.match_id] = asyncio.create_task(self.state_change_listener())
            else:
                await rs.PubSub.publish_match_state_channel(self.match_id, MatchState.RUNNING)

    async def disconnect(self, close_code):

        # Handle user disconnecting from the match
        await rs.User.set_online_status(self.user_id, UserOnlineStatus.ONLINE)
        logger.info(f"User {self.user_id} disconnected from match {self.match_id}")
        await self.channel_layer.group_discard(self.match_id, self.channel_name)
    
        # Check if there are any listeners left
        if await rs.Match.get_connected_users_count(self.match_id) == 0:
            # Perform necessary cleanup
            logger.info(f"No connected Users left for match {self.match_id}")
            if self.match_id in MatchConsumer.broadcast_locks:
                async with MatchConsumer.broadcast_locks[self.match_id]:
                    if self.match_id in MatchConsumer.broadcast_tasks:
                        MatchConsumer.broadcast_tasks[self.match_id].cancel()
                        del MatchConsumer.broadcast_tasks[self.match_id]
                        del MatchConsumer.match_states[self.match_id]
                    # Delete the lock for the match_id
                    del MatchConsumer.broadcast_locks[self.match_id]
        else:
            await rs.PubSub.publish_match_state_channel(self.match_id, MatchState.PAUSED)
            logger.info(f"Match {self.match_id} is paused")

    async def receive(self, text_data):
        # data = json.loads(text_data)
        
        # # Update match state in Redis
        # redis_instance.set(f"match:{self.match_id}:state", text_data)
        
        # # Broadcast match state to all players
        # await self.channel_layer.group_send(
        #     self.match_id,
        #     {
        #         'type': 'match_update',
        #         'data': data
        #     }
        # )
        pass

    async def match_update(self, event):
        # Send match update to WebSocket
        await self.send(text_data=json.dumps(event['data']))

    async def broadcast_match_data(self):
        previous_state = None
        while True:
            if self.current_state == MatchState.RUNNING:
                if previous_state != MatchState.RUNNING:
                    if previous_state == MatchState.PAUSED and self.disconnect_timer_task:
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



    async def state_change_listener(self):
        loop = asyncio.get_event_loop()
        while True:
            message = await loop.run_in_executor(None, self.pubsub.get_message, True, 0.1)
            if message:
                logger.info(f"Received message: {message}")
                if message['type'] == 'message':
                    self.current_state = message['data'].decode('utf-8')
                        
    async def handle_player_disconnect(self):
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
        await rs.PubSub.publish_match_state_channel(self.match_id, MatchState.FINISHED)
        await self.disconnect(1000)

    # async def has_listeners(self, match_id):
    #     # Check the connection count in Redis
    #     connection_count = int(redis_instance.get(f"match:{match_id}:connections") or 0)
    #     return connection_count > 0