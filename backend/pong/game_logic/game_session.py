import logging
import struct
import asyncio
from .ball import Ball
from .paddle import Paddle
from .utils.vector2 import Vector2
from .utils.vector_utils import degree_to_vector
from typing import Callable
from django.conf import settings

logger = logging.getLogger("game_session")

WORLD_SIZE = Vector2(settings.GAME_CONFIG['world_size'][0], settings.GAME_CONFIG['world_size'][1])
PADDLE_SIZE = Vector2(settings.GAME_CONFIG['paddle']['size'][0], settings.GAME_CONFIG['paddle']['size'][1])
PADDLE_X_OFFSET = settings.GAME_CONFIG['paddle']['x_offset']
PADDLE_SPEED = settings.GAME_CONFIG['paddle']['speed']
PADDLE_CENTER_OF_MASS = Vector2(settings.GAME_CONFIG['paddle']['center_of_mass'][0], settings.GAME_CONFIG['paddle']['center_of_mass'][1])
BALL_SPEED = settings.GAME_CONFIG['ball']['speed']
BALL_SIZE = settings.GAME_CONFIG['ball']['size']

class GameSession:
    def __init__(self, on_player_scored: Callable[[str], None]) -> None:
        self._on_player_scored = on_player_scored
        paddle_left_position = Vector2(PADDLE_X_OFFSET, WORLD_SIZE.y / 2 - PADDLE_SIZE.y / 2)
        paddle_right_position = Vector2(WORLD_SIZE.x - PADDLE_SIZE.x - PADDLE_X_OFFSET, WORLD_SIZE.y / 2 - PADDLE_SIZE.y / 2)
        self.paddle_left = Paddle(position=paddle_left_position, size=PADDLE_SIZE, speed=PADDLE_SPEED, world_size=WORLD_SIZE, center_of_mass=Vector2(PADDLE_CENTER_OF_MASS.x * -1, PADDLE_CENTER_OF_MASS.y))
        self.paddle_right = Paddle(position=paddle_right_position, size=PADDLE_SIZE, speed=PADDLE_SPEED, world_size=WORLD_SIZE, center_of_mass=PADDLE_CENTER_OF_MASS)
        self.ball = Ball(Vector2(WORLD_SIZE.x / 2, WORLD_SIZE.y / 2), direction=degree_to_vector(55), speed=BALL_SPEED, size=BALL_SIZE, canvas_size=WORLD_SIZE, collider_list=[self.paddle_left, self.paddle_right])

    def __del__(self):
        logger.debug(f"Deleted game session {self}")

    def update_player_direction(self, player_id: int, direction: int) -> None:
        '''Direction is -1(up), 0(stop), or 1(down)'''
        if player_id == 0:
            self.paddle_left.direction = direction
        elif player_id == 1:
            self.paddle_right.direction = direction

    async def calculate_game_state(self, delta_time: float) -> None:
        self.paddle_left.move(delta_time)
        self.paddle_right.move(delta_time)
        self.ball.move(delta_time)

        if self.ball.get_position().x < 0:
            await self._on_player_scored(1) # Call the callback function
            self.ball.reset()
        elif self.ball.get_position().x + self.ball.get_size() > WORLD_SIZE.x:
            await self._on_player_scored(0) # Call the callback function
            self.ball.reset()

    def to_dict(self):
        return {
            "paddle_left": self.paddle_left.to_dict(),
            "paddle_right": self.paddle_right.to_dict(),
            "ball": self.ball.to_dict()
        }
    
    def to_bytearray(self):
        # Create a byte array and pack the positions as 32-bit floats
        left_paddle_position = self.paddle_left.get_position()
        right_paddle_position = self.paddle_right.get_position()
        ball_position = self.ball.get_position()
        byte_array = bytearray(24)
        struct.pack_into('<f', byte_array, 0, left_paddle_position.x)
        struct.pack_into('<f', byte_array, 4, left_paddle_position.y)
        struct.pack_into('<f', byte_array, 8, right_paddle_position.x)
        struct.pack_into('<f', byte_array, 12, right_paddle_position.y)
        struct.pack_into('<f', byte_array, 16, ball_position.x)
        struct.pack_into('<f', byte_array, 20, ball_position.y)

        return byte_array