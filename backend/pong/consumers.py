import json
import struct
import redis
import asyncio
import uuid
from enum import Enum, auto
from pong.matchmaking.MatchHandler import MatchHandler
from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

import logging
logger = logging.getLogger("PongConsumer")

redis_instance = redis.StrictRedis(host='redis', port=6379, db=0)

async def save_user_info(user_id, online_status, current_match_id, ttl=3600):
    user_key = f"user:{user_id}:info"
    user_info = {
        'online_status': online_status,
        'current_match_id': current_match_id
    }
    redis_instance.setex(user_key, ttl, json.dumps(user_info))

class SetupFailed(Exception):
    def __init__(self, message="Setup failed"):
        self.message = message
        super().__init__(self.message)

class ClientState(Enum):
    SETUP = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()

class MatchType(Enum):
    LOCAL_MATCHMAKING = auto()
    ONLINE_MATCHMAKING = auto()
    LOCAL_TOURNAMENT = auto()
    ONLINE_TOURNAMENT = auto()

# class ClientConsumer(AsyncWebsocketConsumer):
#     def __init__(self) -> None:
#         self.id = uuid.uuid4()
#         self.state = ClientState.SETUP
#         self.match_handler = MatchHandler()
#         self.groups = self.groups or []
#         self._receive_queue = asyncio.Queue()
#         self._closed = False

#     async def connect(self):
#         # Check if user is authenticated
#         if self.scope['user'] and not isinstance(self.scope['user'], AnonymousUser):
#             print(f"Client connected: {self.scope['user']}")
#             print(f"User ID: {self.scope['user'].id}")
#             await self.accept()
#         else:
#             print("Client not authenticated")
#             await self.close()
#             return
#         # await self.accept()
#         self.match_handler.register_client(self)
#         logger.info(f"Client connected: {self.channel_name}, ID: {self.id}")

#     async def disconnect(self, close_code):
#         self.match_handler.unregister_client(self)
#         self._closed = True

#     async def receive(self, text_data):
#         match self.state:
#             case ClientState.SETUP:
#                 text_data_json = {}
#                 try:
#                     text_data_json = json.loads(text_data)            
#                 except:
#                     return

#                 message_type = text_data_json.get("type", "")

#                 if message_type == "setup":
#                     try:
#                         await self.handleSetup(text_data_json.get("matchType", ""))
#                         self.state = ClientState.RUNNING
#                         logger.info("Client setup complete")
#                     except SetupFailed:
#                         await self.sendSetupStatus(False)
#             case ClientState.READY:
#                 if message_type == "ready":
#                     return
#             case ClientState.RUNNING:
#                 self._receive_queue.put_nowait(text_data)
#                 logger.info(f"Received data: {text_data}")
#             case ClientState.PAUSED:
#                 pass
#             case _:
#                 return
            
#     def get_receive_queue_item(self):
#         if self._receive_queue.qsize() == 0:
#             return None
#         return self._receive_queue.get_nowait()

#     async def sendSetupStatus(self, status: bool) -> None:
#         message = {"Type": "setup", "valid": status}
#         logger.info(f"Sending Setup message to Client: {message}")
#         try:
#             await self.send(text_data=json.dumps(message))
#         except Exception as e:
#             logger.error(f"Failed to send message: {e}")

#     async def sendHandshake(self, type: MatchType) -> None:
#         match type:
#             case MatchType.LOCAL_MATCHMAKING:
#                 pass
#             case MatchType.ONLINE_MATCHMAKING:
#                 await self.sendSetupStatus(True);
#             case MatchType.LOCAL_TOURNAMENT:
#                 pass
#             case MatchType.ONLINE_TOURNAMENT:
#                 pass

#     async def handleSetup(self, text_data: str) -> None:
#         match text_data:
#             case "onlineMM":
#                 await self.sendHandshake(MatchType.ONLINE_MATCHMAKING)
#             case _:
#                 raise SetupFailed()



# class MatchmakingConsumer(AsyncWebsocketConsumer):

#     playerQueue = [] # Die Queue ist vielleicht unsinn, eine Variable sollte auch reichen
#     queueLock = asyncio.Lock() # Initialize the lock
#     roomID = None

#     async def connect(self):
#         await self.accept()
#         async with self.queueLock:
#             if len(self.playerQueue < 2):
#                 self.playerQueue.append(self.channel_name)
#                 self.roomID = uuid.uuid4()
#             self.ownRoomID = self.roomID
#             await self.channel_layer.group_add(self.roomID, self.channel_name)
#             if len(self.playerQueue == 2):
#                 send_start_message()
#                 self.playerQueue.pop(0)
#                 MatchmakingConsumer.broadcast_task = asyncio.create_task(self.broadcast_game_data())

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
#         del MatchmakingConsumer.connected_users[self.channel_name]
#         number_of_connected_users = len(MatchmakingConsumer.connected_users)
#         if number_of_connected_users == 0 and MatchmakingConsumer.broadcast_task:
#             MatchmakingConsumer.broadcast_task.cancel()
#             MatchmakingConsumer.broadcast_task = None

#     async def receive(self, text_data):
#         # Process incoming message from WebSocket
#         user_id = self.channel_name
#         if text_data:
#             text_data_json = json.loads(text_data)
#             if text_data_json["type"] == "player_update":
#                 payload = text_data_json["payload"]
#                 direction = payload["direction"]
#                 if direction < -1 or direction > 1:
#                     return
#                 if user_id == self.player_1.connection_id:
#                     self.player_1.direction = payload["direction"]
#                 elif user_id == self.player_2.connection_id:
#                     self.player_2.direction = payload["direction"]

class GameSessionConsumer(AsyncWebsocketConsumer):

    broadcast_tasks = {}
    broadcast_locks = {}
    game_states = {}

    def __init__(self):
        super().__init__()
        self.groups = []
        self.game_id = None
        self.user_id = None
        self.pubsub = None
        self.current_state = None
        self.disconnect_timer_task = None

    async def connect(self):
        # Extracting the game_id from the URL route parameters
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.user_id = self.scope["user"].id

        # Initialize pubsub connection
        self.pubsub = redis_instance.pubsub()
        
        # Subscribe to the game state channel
        await self.subscribe_to_game_state()

        # Check if user is authenticated
        if self.user_id is None:
            await self.close()
            logger.error("User not authenticated")
            return
        
        # Set user state to 'playing' in Redis
        await self.set_user_state("playing")
        await self.set_user_match_id(self.game_id)

        # Increment the connection count for the game
        await self.increment_connection_count()

        # Add the connection to the channel group for this game
        await self.channel_layer.group_add(self.game_id, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        logger.info(f"User {self.user_id} connected to game {self.game_id}")

        # Set user_id, match_id and online status in Redis
        await save_user_info(user_id=self.user_id, online_status="playing", current_match_id=self.game_id, ttl=3600)

        # Initialize lock for the game_id if not already present
        if self.game_id not in GameSessionConsumer.broadcast_locks:
            GameSessionConsumer.broadcast_locks[self.game_id] = asyncio.Lock()

        # Create a broadcast task for the game if not already present
        async with GameSessionConsumer.broadcast_locks[self.game_id]:
            if self.game_id not in GameSessionConsumer.broadcast_tasks:
                GameSessionConsumer.broadcast_tasks[self.game_id] = asyncio.create_task(self.broadcast_game_data())
                GameSessionConsumer.game_states[self.game_id] = asyncio.create_task(self.state_change_listener())
            else:
                await self.set_game_state("running")

    async def disconnect(self, close_code):
        # Decrement the connection count for the game
        redis_instance.decr(f"game:{self.game_id}:connections")

        # Handle user disconnecting from the game
        redis_instance.set(f"user:{self.user_id}:state", "online", ex=3600)
        logger.info(f"User {self.user_id} disconnected from game {self.game_id}")
        await self.channel_layer.group_discard(self.game_id, self.channel_name)
    
        # Check if there are any listeners left
        if not await self.has_listeners(self.game_id):
            # Perform necessary cleanup
            logger.info(f"No listeners left for game {self.game_id}")
            async with GameSessionConsumer.broadcast_locks[self.game_id]:
                if self.game_id in GameSessionConsumer.broadcast_tasks:
                    GameSessionConsumer.broadcast_tasks[self.game_id].cancel()
                    del GameSessionConsumer.broadcast_tasks[self.game_id]
                    del GameSessionConsumer.game_states[self.game_id]
                # Delete the lock for the game_id
                del GameSessionConsumer.broadcast_locks[self.game_id]
        else:
            await self.set_game_state("paused")

    async def receive(self, text_data):
        # data = json.loads(text_data)
        
        # # Update game state in Redis
        # redis_instance.set(f"game:{self.game_id}:state", text_data)
        
        # # Broadcast game state to all players
        # await self.channel_layer.group_send(
        #     self.game_id,
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
            if self.current_state == "running":
                if previos_state != "running":
                    if previos_state == "paused" and self.disconnect_timer_task:
                        self.disconnect_timer_task.cancel()
                        self.disconnect_timer_task = None
                    previos_state = "running"
                    await self.channel_layer.group_send(
                        self.game_id,
                        {
                            'type': 'game_update',
                            'data': {'state': 'running'}
                        }
                    )
            elif self.current_state == "paused":
                if previos_state != "paused":
                    previos_state = "paused"
                    await self.channel_layer.group_send(
                        self.game_id,
                        {
                            'type': 'game_update',
                            'data': {'state': 'paused'}
                        }
                    )
                    await self.handle_player_disconnect()
            elif self.current_state == "finished":
                if previos_state != "finished":
                    previos_state = "finished"
                    await self.channel_layer.group_send(
                        self.game_id,
                        {
                            'type': 'game_update',
                            'data': {'state': 'finished'}
                        }
                    )           
            await asyncio.sleep(0.1)

    async def set_game_state(self, state):
        await sync_to_async(redis_instance.publish)(f"game:{self.game_id}:channel", state)

    async def subscribe_to_game_state(self):
        await sync_to_async(self.pubsub.subscribe)(f"game:{self.game_id}:channel")

    async def unsubscribe_from_game_state(self):
        await sync_to_async(self.pubsub.unsubscribe)(f"game:{self.game_id}:channel")
    
    async def increment_connection_count(self):
        await sync_to_async(redis_instance.incr)(f"game:{self.game_id}:connections")

    async def decrement_connection_count(self):
        await sync_to_async(redis_instance.decr)(f"game:{self.game_id}:connections")

    async def set_user_state(self, state):
        await sync_to_async(redis_instance.set)(f"user:{self.user_id}:state", state)

    async def set_user_match_id(self, match_id):
        await sync_to_async(redis_instance.set)(f"user:{self.user_id}:current_match_id", match_id)

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
        await sync_to_async(redis_instance.delete)(f"game:{self.game_id}:channel")
        # Implement logic to declare the other player as the winner
        # For example, you might update the game state and notify the players

    async def has_listeners(self, game_id):
        # Check the connection count in Redis
        connection_count = int(redis_instance.get(f"game:{game_id}:connections") or 0)
        return connection_count > 0


class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['user'].id
        if self.user_id is None:
            await self.close()
            logger.error("User not authenticated")
            return
        self.group_name = f"user_{self.user_id}"

        # Add user to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.reconnect_to_game()

    async def disconnect(self, close_code):
        if self.user_id is None:
            return
        # Remove user from group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        self.remove_from_queue()

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
        if data["match_type"] == "online" and data["action"] == "join":
            await self.join_queue()

    async def remove_from_queue(self):
        redis_instance.lrem("matchmaking_queue", 0, self.user_id)

    async def join_queue(self):
        redis_instance.rpush("matchmaking_queue", self.user_id)
        await self.check_queue()

    async def check_queue(self):
        queue_length = redis_instance.llen("matchmaking_queue")
        logger.info(f"Queue length: {queue_length}")
        if queue_length >= 2:
            player1_id = redis_instance.lpop("matchmaking_queue")
            player2_id = redis_instance.lpop("matchmaking_queue")
            # Decode bytes to strings
            player1_id = player1_id.decode('utf-8')
            player2_id = player2_id.decode('utf-8')
            logger.info(f"Match found: {player1_id} vs {player2_id}")
            game_id = await self.create_game(player1_id, player2_id)
            await self.notify_players(game_id, player1_id, player2_id)
            # await self.game_assigned({'game_id': game_id})

    async def create_game(self, player1_id, player2_id):
        game_id = f"game_{player1_id}_{player2_id}"
        logger.info(f"Creating game: {game_id}")
        redis_instance.set(f"game:{game_id}:state", json.dumps({'player1': player1_id, 'player2': player2_id, 'state': 'new'}))
        return game_id

    async def notify_players(self, game_id, player1_id, player2_id):
        logger.info(f"Notifying players: {player1_id} and {player2_id}")
        await self.channel_layer.group_send(
            f"user_{player1_id}",
            {
                'type': 'match_assigned',
                'game_id': game_id
            }
        )
        await self.channel_layer.group_send(
            f"user_{player2_id}",
            {
                'type': 'match_assigned',
                'game_id': game_id
            }
        )

    async def match_assigned(self, event):
        logger.info(f"Game assigned: {event['game_id']}")
        await self.send(text_data=json.dumps({
            'state': 'match_assigned',
            'game_id': event['game_id']
        }))

    # TEST FUNCTION FOR RECONNECTING TO GAME
    async def reconnect_to_game(self):
        current_match = redis_instance.get(f"user:{self.user_id}:current_match_id")
        logger.info(f"Reconnecting to game: {current_match}")
        if current_match:
            current_match = current_match.decode('utf-8')
            logger.info(f"Current match: {current_match}")
            does_match_exist = redis_instance.exists(f"game:{current_match}:state")
            logger.info(f"Match exists: {does_match_exist}")
            if does_match_exist:
                await self.send(text_data=json.dumps({
                    'state': 'reconnect',
                    'game_id': current_match
                }))
