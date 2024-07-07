from pong.game_logic.player import Player
from pong.utils.vector2 import Vector2
from pong.utils.vector_utils import degree_to_vector

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
