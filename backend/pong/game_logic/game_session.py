import logging
from .ball import Ball
from .paddle import Paddle
from .utils.vector2 import Vector2
from .utils.vector_utils import degree_to_vector
from typing import Callable

logger = logging.getLogger("game_session")

WORLD_SIZE = Vector2(16, 9)
PADDLE_SIZE = Vector2(0.5, 2)
PADDLE_SPEED = 0.1
BALL_SPEED = 0.1
BALL_SIZE = 0.2

class GameSession:
    def __init__(self, on_player_scored: Callable[[str], None]) -> None:
        self._on_player_scored = on_player_scored
        self.paddle_left = Paddle(position=Vector2(0, WORLD_SIZE.y / 2), size=PADDLE_SIZE, speed=PADDLE_SPEED, world_size=WORLD_SIZE)
        self.paddle_right = Paddle(position=Vector2(WORLD_SIZE.x - PADDLE_SIZE.x, WORLD_SIZE.y / 2), size=PADDLE_SIZE, speed=PADDLE_SPEED, world_size=WORLD_SIZE)
        self.ball = Ball(Vector2(WORLD_SIZE.x / 2, WORLD_SIZE.y / 2), direction=degree_to_vector(55), speed=BALL_SPEED, size=BALL_SIZE, canvas_size=WORLD_SIZE, collider_list=[self.paddle_left, self.paddle_right])

    def update_player_direction(self, player_id: int, direction: int) -> None:
        '''Direction is -1(up), 0(stop), or 1(down)'''
        if player_id == 0:
            self.paddle_left.direction = direction
        elif player_id == 1:
            self.paddle_right.direction = direction

    async def calculate_game_state(self) -> None:
        self.paddle_left.move()
        self.paddle_right.move()
        self.ball.move()

        if self.ball.position.x < 0:
            await self._on_player_scored(0)
            self.ball.reset()
            self.ball.direction.x *= -1
        elif self.ball.position.x + self.ball.size > WORLD_SIZE.x:
            await self._on_player_scored(1)
            self.ball.reset()
            self.ball.direction.x *= -1

    def to_dict(self):
        return {
            "paddle_left": self.paddle_left.to_dict(),
            "paddle_right": self.paddle_right.to_dict(),
            "ball": self.ball.to_dict()
        }