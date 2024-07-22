import json
import struct
from asyncio import sleep
import asyncio
from .game_logic.paddle import Player
from .game_logic.ball import Ball
from .utils.vector2 import Vector2
from .utils.vector_utils import degree_to_vector
from enum import Enum, auto

import logging
logger = logging.getLogger(__name__)

from channels.generic.websocket import AsyncWebsocketConsumer

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

class ClientConsumer(AsyncWebsocketConsumer):
    def __init__(self) -> None:
        self.state = ClientState.SETUP
        self.groups = []
    # game_group_name = "game_group"
    # canvas_size = Vector2(800, 800)
    # paddle_size = Vector2(20, 100)
    # start_position_p1 = Vector2(0, canvas_size.y / 2 - paddle_size.y / 2)
    # start_position_p2 = Vector2(canvas_size.x - paddle_size.x, canvas_size.y / 2 - paddle_size.y / 2)
    # start_position_ball = Vector2(canvas_size.x / 2, canvas_size.y / 2)
    # player_speed = 15.0
    # player_1 = Player(1, start_position_p1, paddle_size, 12, canvas_size)
    # player_2 = Player(2, start_position_p2, paddle_size, 12, canvas_size)
    # collider_list = [player_1, player_2]
    # ball = Ball(start_position_ball, degree_to_vector(-50), 12, 20, canvas_size, tick_rate, collider_list)
    tick_rate = 60
    broadcast_task = None
    connected_users = {}
    is_online_matchmaking = False
    online_matchmaking_queue = []

    async def sendSetupStatus(self, status: bool) -> None:
        message = {"Type": "setup", "valid": status}
        logger.info(f"Sending Setup message to Client: {message}")
        try:
            await self.send(text_data=json.dumps(message))
            logger.info("Message sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def sendHandshake(self, type: MatchType) -> None:
        match type:
            case MatchType.LOCAL_MATCHMAKING:
                pass
            case MatchType.ONLINE_MATCHMAKING:
                await self.sendSetupStatus(True);
                self.online_matchmaking_queue.append(self)
                is_online_matchmaking = True
            case MatchType.LOCAL_TOURNAMENT:
                pass
            case MatchType.ONLINE_TOURNAMENT:
                pass

    async def handleSetup(self, text_data: str) -> None:
        match text_data:
            case "onlineMM":
                await self.sendHandshake(MatchType.ONLINE_MATCHMAKING)
            case _:
                raise SetupFailed()

    async def connect(self):
        await self.accept()
        # await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        # logger.info(f"Channel name: {self.channel_name}")
        self.connected_users[self.channel_name] = self
        # number_of_connected_users = len(ClientConsumer.connected_users)
        
        # if number_of_connected_users <= 2:
        #     if number_of_connected_users == 1:
        #         self.player_1.connection_id = self.channel_name
        #         ClientConsumer.broadcast_task = asyncio.create_task(self.broadcast_game_data())
        #     elif number_of_connected_users == 2:
        #         self.player_2.connection_id = self.channel_name

    async def disconnect(self, close_code):
        # await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        del ClientConsumer.connected_users[self.channel_name]
        # number_of_connected_users = len(ClientConsumer.connected_users)
        # if number_of_connected_users == 0 and ClientConsumer.broadcast_task:
        #     ClientConsumer.broadcast_task.cancel()
        #     ClientConsumer.broadcast_task = None

    async def receive(self, text_data):
        text_data_json = {}
        try:
            text_data_json = json.loads(text_data)            
        except:
            return

        message_type = text_data_json.get("type", "")

        match self.state:
            case ClientState.SETUP:
                if message_type == "setup":
                    try:
                        await self.handleSetup(text_data_json.get("matchType", ""))
                    except SetupFailed:
                        await self.sendSetupStatus(False)
            case ClientState.READY:
                if message_type == "ready":
                    return
            case ClientState.RUNNING:
                if message_type == "input":
                    return
            case ClientState.PAUSED:
                if message_type == "unpause":
                    return
            case _:
                return

    # async def receive(self, text_data):
    #     # Process incoming message from WebSocket
    #     user_id = self.channel_name
    #     try:
    #         text_data_json = json.loads(text_data)
    #     except json.JSONDecodeError:
    #         return

    #     if text_data_json["type"] == "player_update":
    #         payload = text_data_json["payload"]
    #         direction = payload["direction"]
    #         if direction < -1 or direction > 1:
    #             return
    #         if user_id == self.player_1.connection_id:
    #             self.player_1.direction = payload["direction"]
    #         elif user_id == self.player_2.connection_id:
    #             self.player_2.direction = payload["direction"]

    def update_game_state(self):
        self.player_1.move()
        self.player_2.move()
        self.ball.move()

    async def broadcast_game_data(self):
        try:
            while True:
                # Update game state, e.g., move the ball, check for scores
                self.update_game_state()
                binary_data = struct.pack('ffffff',
                                        self.player_1.position.x,
                                        self.player_1.position.y,
                                        self.player_2.position.x,
                                        self.player_2.position.y,
                                        self.ball.position.x,
                                        self.ball.position.y)                
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        "type": "group.message",
                        "message": binary_data,
                    }
                )
                await sleep(1/self.tick_rate)  # Adjust the sleep time to control broadcast rate
        except asyncio.CancelledError:
            # Handle cancellation gracefully # TODO: Implement this
            pass

    async def group_message(self, event):
        # Forward the message to WebSocket
        await self.send(bytes_data=event['message'])