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
    def __init__(self, player: int, x: int, y: int, paddle_height: int = 100, paddle_width: int = 20, speed: int = 10):
        self.player_id = str(uuid.uuid4())
        self.player = player
        self.paddle_height = paddle_height
        self.paddle_width = paddle_width
        self.speed = speed
        self.x = x
        self.y = y
        self.up = False
        self.down = False

    def update(self, x, y):
        self.x = x
        self.y = y

    def to_dict(self):
        return {
            "player": self.player,
            "x": self.x,
            "y": self.y
        }
    
class Ball:
    def __init__(self, x: float, y: float, speed: float = 20, direction: Vector2 = degree_to_vector(45), size: int = 20):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.size = size
        self.start_pos = Vector2(x, y)

    def update(self):
        """Update the ball's position based on its speed and direction."""
        self.x += self.speed * self.direction.x
        self.y += self.speed * self.direction.y

    def get_new_position(self):
        """Predict the ball's next position."""
        return (
            Vector2(
                self.x + self.speed * self.direction.x,
                self.y + self.speed * self.direction.y
                )
            )

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }

class MultiplayerConsumer(AsyncWebsocketConsumer):
    game_group_name = "game_group"
    player_1 = Player(1, 0, 400 - 50, 100, 20, 20)
    player_2 = Player(2, 800 - 20, 400 - 50, 100, 20, 20)
    ball = Ball(400, 400, 15, degree_to_vector(-50))
    canvas_width = 800
    canvas_height = 800
    connected_players = 0
    broadcast_task = None


    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        if MultiplayerConsumer.connected_players <= 2:
            MultiplayerConsumer.connected_players += 1
            await self.send(text_data=json.dumps({
                'type': 'player_id',
                'player_id': self.player_1.player_id if MultiplayerConsumer.connected_players == 1 else MultiplayerConsumer.player_2.player_id,
            }))
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
            if text_data_json["type"] == "player_update":
                payload = text_data_json["payload"]
                player_id = payload["player_id"]
                key = payload["key"]
                pressed = payload["pressed"]
                if player_id == self.player_1.player_id:
                    if key == "up":
                        self.player_1.up = pressed
                    elif key == "down":
                        self.player_1.down = pressed
                elif player_id == self.player_2.player_id:
                    if key == "up":
                        self.player_2.up = pressed
                    elif key == "down":
                        self.player_2.down = pressed 

    def update_player_position(self):
        if self.player_1.up:
            self.player_1.y -= self.player_1.speed
        if self.player_1.down:
            self.player_1.y += self.player_1.speed
        if self.player_2.up:
            self.player_2.y -= self.player_2.speed
        if self.player_2.down:
            self.player_2.y += self.player_2.speed
        pass

    def update_ball_position(self):
        new_position = self.ball.get_new_position()
        if new_position.x < 0 or new_position.x > self.canvas_width:
            self.ball.x = self.ball.start_pos.x
            self.ball.y = self.ball.start_pos.y
            return
        
        if new_position.y < 0 or new_position.y > self.canvas_height:
            self.ball.direction.y *= -1
        self.ball.update()
        

    def update_game_state(self):
        self.update_player_position()
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