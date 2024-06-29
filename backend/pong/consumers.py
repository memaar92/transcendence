import json
import uuid
from asyncio import sleep
import asyncio
import math

from channels.generic.websocket import AsyncWebsocketConsumer


def degree_to_vector(angle_degrees):
    # Convert angle from degrees to radians
    angle_radians = math.radians(angle_degrees)
    # Calculate x and y components
    x = math.cos(angle_radians)
    y = math.sin(angle_radians)
    return (Vector2(x, y))


def vector_to_degree(x, y):
    # Calculate angle in radians
    angle_radians = math.atan2(y, x)
    # Convert angle from radians to degrees
    angle_degrees = math.degrees(angle_radians)
    return angle_degrees

class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }

class Player:
    def __init__(self, player_id, player_number, x, y):
        self.player_id = player_id
        self.player_number = player_number
        self.x = x
        self.y = y

    def update(self, x, y):
        self.x = x
        self.y = y

    def to_dict(self):
        return {
            "playerId": self.player_id,
            "player_number": self.player_number,
            "x": self.x,
            "y": self.y
        }
    
class Ball:
    def __init__(self, x: float, y: float, speed: float, direction: Vector2):
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = direction

    def update(self):
        self.x += self.speed * self.direction.x
        self.y += self.speed * self.direction.y

    def get_new_position(self):
        return (
            Vector2(
                self.x + self.speed * self.direction.x,
                self.y + self.speed * self.direction.y
                )
            )

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "speed": self.speed,
            "direction": self.direction.to_dict()
        }

class MultiplayerConsumer(AsyncWebsocketConsumer):
    game_group_name = "game_group"
    player_1 = Player(str(uuid.uuid4()), 1, 0, 0.5)
    player_2 = Player(str(uuid.uuid4()), 2, 1, 0.5)
    ball = Ball(0.5, 0.5, 0.01, degree_to_vector(-85))
    connected_players = 0
    broadcast_task = None


    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        self.connected_players += 1
        if self.connected_players == 1:
            MultiplayerConsumer.broadcast_task = asyncio.create_task(self.broadcast_game_data())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        MultiplayerConsumer.connected_players -= 1
        if MultiplayerConsumer.connected_players == 0 and MultiplayerConsumer.broadcast_task:
            MultiplayerConsumer.broadcast_task.cancel()
            MultiplayerConsumer.broadcast_task = None

    async def receive(self, text_data):
        # Process incoming message from WebSocket
        if text_data:
            text_data_json = json.loads(text_data)
            # Update game state based on received data
            # For example, updating player position
            # self.player_1.update_position(text_data_json['x'], text_data_json['y'])
            await self.send(text_data=text_data)  # Echo back the received data

    def update_player_position(self):
        pass

    def update_ball_position(self):
        new_position = self.ball.get_new_position()
        if new_position.x < 0 or new_position.x > 1:
            self.ball.x = 0.5
            self.ball.y = 0.5
            return
        
        if new_position.y < 0 or new_position.y > 1:
            self.ball.direction.y *= -1
        self.ball.update()
        

    def update_game_state(self):
        # self.update_player_position()
        self.update_ball_position()

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
                await sleep(1/32)  # Adjust the sleep time to control broadcast rate
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            pass

    async def group_message(self, event):
        # Forward the message to WebSocket
        await self.send(text_data=event['message'])