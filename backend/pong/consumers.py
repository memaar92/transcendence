import json
from asyncio import sleep
import asyncio
from .game_logic.player import Player
from .game_logic.ball import Ball
from .utils.vector2 import Vector2
from .utils.vector_utils import degree_to_vector

import logging
logger = logging.getLogger(__name__)

from channels.generic.websocket import AsyncWebsocketConsumer

class MultiplayerConsumer(AsyncWebsocketConsumer):
    game_group_name = "game_group"
    canvas_size = Vector2(800, 800)
    paddle_size = Vector2(20, 100)
    start_position_p1 = Vector2(0, canvas_size.y / 2 - paddle_size.y / 2)
    start_position_p2 = Vector2(canvas_size.x - paddle_size.x, canvas_size.y / 2 - paddle_size.y / 2)
    start_position_ball = Vector2(canvas_size.x / 2, canvas_size.y / 2)
    player_speed = 12.0
    tick_rate = 60
    player_1 = Player(1, start_position_p1, paddle_size, 12, canvas_size)
    player_2 = Player(2, start_position_p2, paddle_size, 12, canvas_size)
    collider_list = [player_1, player_2]
    ball = Ball(start_position_ball, degree_to_vector(-50), 10, 20, canvas_size, tick_rate, collider_list)
    broadcast_task = None
    connected_users = {}



    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        self.connected_users[self.channel_name] = self
        number_of_connected_users = len(MultiplayerConsumer.connected_users)
        
        if number_of_connected_users <= 2:
            if number_of_connected_users == 1:
                self.player_1.connection_id = self.channel_name
                MultiplayerConsumer.broadcast_task = asyncio.create_task(self.broadcast_game_data())
            elif number_of_connected_users == 2:
                self.player_2.connection_id = self.channel_name

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        del MultiplayerConsumer.connected_users[self.channel_name]
        number_of_connected_users = len(MultiplayerConsumer.connected_users)
        if number_of_connected_users == 0 and MultiplayerConsumer.broadcast_task:
            MultiplayerConsumer.broadcast_task.cancel()
            MultiplayerConsumer.broadcast_task = None

    async def receive(self, text_data):
        # Process incoming message from WebSocket
        user_id = self.channel_name
        if text_data:
            text_data_json = json.loads(text_data)
            if text_data_json["type"] == "player_update":
                payload = text_data_json["payload"]
                direction = payload["direction"]
                if direction < -1 or direction > 1:
                    return
                if user_id == self.player_1.connection_id:
                    self.player_1.direction = payload["direction"]
                elif user_id == self.player_2.connection_id:
                    self.player_2.direction = payload["direction"]

    def update_game_state(self):
        self.player_1.move()
        self.player_2.move()
        self.ball.move()

    async def broadcast_game_data(self):
        try:
            while True:
                # Update game state, e.g., move the ball, check for scores
                self.update_game_state()
                player_data = {
                    "player_1": self.player_1.to_dict(),
                    "player_2": self.player_2.to_dict(),
                    "ball": self.ball.to_dict(),
                }
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        "type": "group.message",
                        "message": json.dumps(player_data),
                    }
                )
                await sleep(1/self.tick_rate)  # Adjust the sleep time to control broadcast rate
        except asyncio.CancelledError:
            # Handle cancellation gracefully # TODO: Implement this
            pass

    async def group_message(self, event):
        # Forward the message to WebSocket
        await self.send(text_data=event['message'])