import json
import redis
import asyncio
from ..services import redis_service as rs
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from enum import Enum

import logging
logger = logging.getLogger("PongConsumer")

redis_instance = redis.StrictRedis(host='redis', port=6379, db=0)

class GameState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"

class GameSessionConsumer(AsyncWebsocketConsumer):

    broadcast_tasks = {}
    broadcast_locks = {}
    game_states = {}

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
        
        # Disconnect if user is already connected to a game
        if await rs.is_user_playing(self.user_id):
            await self.close()
            logger.info(f"User {self.user_id} is already connected to a game")
            return

        # Initialize pubsub connection
        self.pubsub = redis_instance.pubsub()
        
        # Subscribe to the game state channel
        await rs.subscribe_to_match_state_channel(self.pubsub, self.match_id)

        # Increment the connection count for the game
        await rs.increment_connection_count(self.match_id)

        # Add the connection to the channel group for this game
        await self.channel_layer.group_add(self.match_id, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        logger.info(f"User {self.user_id} connected to game {self.match_id}")

        # Set user_id, match_id and online status in Redis
        await rs.set_user_session_info(user_id=self.user_id, online_status="playing", last_match_id=self.match_id, ttl=3600)

        # Initialize lock for the match_id if not already present
        if self.match_id not in GameSessionConsumer.broadcast_locks:
            GameSessionConsumer.broadcast_locks[self.match_id] = asyncio.Lock()

        # Create a broadcast task for the game if not already present
        async with GameSessionConsumer.broadcast_locks[self.match_id]:
            if self.match_id not in GameSessionConsumer.broadcast_tasks:
                GameSessionConsumer.broadcast_tasks[self.match_id] = asyncio.create_task(self.broadcast_game_data())
                GameSessionConsumer.game_states[self.match_id] = asyncio.create_task(self.state_change_listener())
            else:
                await rs.publish_match_state_channel(self.match_id, GameState.RUNNING)

    async def disconnect(self, close_code):
        # Decrement the connection count for the game
        redis_instance.decr(f"game:{self.match_id}:connections")

        # Handle user disconnecting from the game
        redis_instance.set(f"user:session:{self.user_id}:state", "online", ex=3600)
        logger.info(f"User {self.user_id} disconnected from game {self.match_id}")
        await self.channel_layer.group_discard(self.match_id, self.channel_name)
    
        # Check if there are any listeners left
        if not await self.has_listeners(self.match_id):
            # Perform necessary cleanup
            logger.info(f"No listeners left for game {self.match_id}")
            async with GameSessionConsumer.broadcast_locks[self.match_id]:
                if self.match_id in GameSessionConsumer.broadcast_tasks:
                    GameSessionConsumer.broadcast_tasks[self.match_id].cancel()
                    del GameSessionConsumer.broadcast_tasks[self.match_id]
                    del GameSessionConsumer.game_states[self.match_id]
                # Delete the lock for the match_id
                del GameSessionConsumer.broadcast_locks[self.match_id]
        else:
            await rs.publish_match_state_channel(self.match_id, GameState.PAUSED)

    async def receive(self, text_data):
        # data = json.loads(text_data)
        
        # # Update game state in Redis
        # redis_instance.set(f"game:{self.match_id}:state", text_data)
        
        # # Broadcast game state to all players
        # await self.channel_layer.group_send(
        #     self.match_id,
        #     {
        #         'type': 'game_update',
        #         'data': data
        #     }
        # )
        pass

    async def game_update(self, event):
        # Send game update to WebSocket
        await self.send(text_data=json.dumps(event['data']))

    async def broadcast_game_data(self):
        previos_state = None
        while True:
            if self.current_state == GameState.RUNNING:
                if previos_state != GameState.RUNNING:
                    if previos_state == GameState.PAUSED and self.disconnect_timer_task:
                        self.disconnect_timer_task.cancel()
                        self.disconnect_timer_task = None
                    previos_state = GameState.RUNNING
                    await self.channel_layer.group_send(
                        self.match_id,
                        {
                            'type': 'game_update',
                            'data': {'state': 'running'}
                        }
                    )
            elif self.current_state == GameState.PAUSED:
                if previos_state != GameState.PAUSED:
                    previos_state = GameState.PAUSED
                    await self.channel_layer.group_send(
                        self.match_id,
                        {
                            'type': 'game_update',
                            'data': {'state': 'paused'}
                        }
                    )
                    await self.handle_player_disconnect()
            elif self.current_state == GameState.FINISHED:
                if previos_state != GameState.FINISHED:
                    previos_state = GameState.FINISHED
                    await self.channel_layer.group_send(
                        self.match_id,
                        {
                            'type': 'game_update',
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
        await sync_to_async(redis_instance.delete)(f"game:{self.match_id}:channel")
        # Implement logic to declare the other player as the winner
        # For example, you might update the game state and notify the players

    async def has_listeners(self, match_id):
        # Check the connection count in Redis
        connection_count = int(redis_instance.get(f"game:{match_id}:connections") or 0)
        return connection_count > 0