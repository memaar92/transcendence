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
        self.direction = 0
        self.connection_id = None

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
    def __init__(self, canvas_size: Vector2, tick_rate, player_1: Player, player_2: Player, x: float, y: float, speed: float = 20, direction: Vector2 = degree_to_vector(45), size: int = 20):
        self.canvas_size = canvas_size
        self.tick_rate = tick_rate
        self.player_1 = player_1
        self.player_2 = player_2
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.size = size
        self.start_pos = Vector2(x, y)
        self.can_collide_with_paddle = True # Prevents multiple collisions with the same paddle
        self.ticks_until_can_collide_with_paddle = 0 # Prevents multiple collisions with the same paddle

    def update(self):
        """Update the ball's position based on its speed and direction."""
        if self.is_colliding_with_wall(self.canvas_size.y):
            self.direction.y *= -1
        elif self.is_colliding_with_paddle(self.player_1) or self.is_colliding_with_paddle(self.player_2):
            self.ticks_until_can_collide_with_paddle = self.tick_rate / 2
            self.can_collide_with_paddle = False
            self.direction.x *= -1
        elif self.is_colliding_with_goal(self.canvas_size.x):
            self.direction.x *= -1
            self.x = self.start_pos.x
            self.y = self.start_pos.y
        self.x += self.speed * self.direction.x
        self.y += self.speed * self.direction.y

    # def get_new_position(self):
    #     """Predict the ball's next position."""
    #     return (
    #         Vector2(
    #             self.x + self.speed * self.direction.x,
    #             self.y + self.speed * self.direction.y
    #             )
    #         )

    def is_colliding_with_paddle(self, paddle):
        """Check if the ball is colliding with a paddle."""
        if self.ticks_until_can_collide_with_paddle > 0:
            self.ticks_until_can_collide_with_paddle -= 1
            if self.ticks_until_can_collide_with_paddle == 0:
                self.can_collide_with_paddle = True
        if self.can_collide_with_paddle:
            return (
                self.x < paddle.x + paddle.paddle_width
                and self.x + self.size > paddle.x
                and self.y < paddle.y + paddle.paddle_height
                and self.y + self.size > paddle.y
            )
        else:
            return False

    def is_colliding_with_wall(self, canvas_height):
        """Check if the ball is colliding with the top or bottom wall."""
        return self.y < 0 or self.y + self.size > canvas_height
    
    def is_colliding_with_goal(self, canvas_width):
        """Check if the ball is colliding with the left or right wall."""
        return self.x < 0 or self.x + self.size > canvas_width

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }

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