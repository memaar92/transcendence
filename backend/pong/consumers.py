import json
from asyncio import sleep
import asyncio
from .game_logic.player import Player
from .game_logic.ball import Ball
from .utils.vector2 import Vector2
from .utils.vector_utils import degree_to_vector

from channels.generic.websocket import AsyncWebsocketConsumer




class MultiplayerConsumer(AsyncWebsocketConsumer):
    game_group_name = "game_group"
    canvas_size = Vector2(800, 800)
    tick_rate = 60
    player_1 = Player(1, 0, 400 - 50, 100, 20, 12)
    player_2 = Player(2, 800 - 20, 400 - 50, 100, 20, 12)
    ball = Ball(canvas_size, tick_rate, player_1, player_2, canvas_size.x / 2, canvas_size.y / 2, 10, degree_to_vector(-50))
    connected_players = 0
    broadcast_task = None
    connected_users = {}


    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        self.connected_users[self.channel_name] = self
        
        if MultiplayerConsumer.connected_players < 2:
            if MultiplayerConsumer.connected_players == 0:
                self.player_1.connection_id = self.channel_name
            elif MultiplayerConsumer.connected_players == 1:
                self.player_2.connection_id = self.channel_name
            MultiplayerConsumer.connected_players += 1
            if MultiplayerConsumer.connected_players == 1:
                MultiplayerConsumer.broadcast_task = asyncio.create_task(self.broadcast_game_data())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        MultiplayerConsumer.connected_players -= 1
        if MultiplayerConsumer.connected_players == 0 and MultiplayerConsumer.broadcast_task:
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

    def update_player_position(self):
        player_1_velocity = self.player_1.speed * self.player_1.direction
        player_1_new_y = self.player_1.y + player_1_velocity
        player_2_velocity = self.player_2.speed * self.player_2.direction
        player_2_new_y = self.player_2.y + player_2_velocity

        if player_1_new_y < 0:
            self.player_1.y = 0
        elif player_1_new_y + self.player_1.paddle_height > self.canvas_size.y:
            self.player_1.y = self.canvas_size.y - self.player_1.paddle_height
        else:
            self.player_1.y = player_1_new_y
        if self.player_2.y < 0:
            self.player_2.y = 0
        elif self.player_2.y + self.player_2.paddle_height > self.canvas_size.y:
            self.player_2.y = self.canvas_size.y - self.player_2.paddle_height
        else:
            self.player_2.y = player_2_new_y

    def update_game_state(self):
        self.update_player_position()
        self.ball.update()

    async def broadcast_game_data(self):
        try:
            while True:
                # Update game state, e.g., move the ball, check for scores
                # self.update_game_state()
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
            # Handle cancellation gracefully
            pass

    async def group_message(self, event):
        # Forward the message to WebSocket
        await self.send(text_data=event['message'])