from .utils.vector2 import Vector2
from .utils.vector_utils import degree_to_vector
import copy
import logging

logger = logging.getLogger("Ball")

class Ball:
    def __init__(self,
                position: Vector2 = Vector2(0, 0),
                direction: Vector2 = degree_to_vector(45),
                speed: float = 20,
                size: int = 20,
                canvas_size: Vector2 = Vector2(10000, 10000),
                collider_list: list = None):
        self.position: Vector2 = position
        self.direction: Vector2 = direction
        self.speed: float = speed
        self.size: int = size
        self.start_pos: Vector2 = copy.deepcopy(position)

        # Game configuration
        self.canvas_size: Vector2 = canvas_size

        # List of colliders that the ball can collide with
        self.collider_list: list = collider_list if collider_list is not None else []
        self.collided_with_list: list = []

    def move(self):
        """Update the ball's position based on its speed and direction."""

        if self.is_colliding_with_wall():
            self.direction.y *= -1
        elif self.is_colliding():
            self.direction.x *= -1
        elif self.is_colliding_with_goal():
            self.reset()
            self.direction.x *= -1
        self.position.x += self.speed * self.direction.x
        self.position.y += self.speed * self.direction.y

    def reset(self):
        """Reset the ball to its starting position."""
        self.position.x = self.start_pos.x
        self.position.y = self.start_pos.y

    def is_colliding(self):
        """Check if the ball is colliding with a paddle."""
        for collider in self.collider_list:
            if (self.position.x < collider.position.x + collider.size.x and
                self.position.x + self.size > collider.position.x and
                self.position.y < collider.position.y + collider.size.y and
                self.position.y + self.size > collider.position.y):
                if collider not in self.collided_with_list:
                    self.collided_with_list.append(collider)
                return True
            elif collider in self.collided_with_list:
                self.collided_with_list.remove(collider)
        return False

    def is_colliding_with_wall(self):
        """Check if the ball is colliding with the top or bottom wall."""
        return (self.position.y < 0 or
                self.position.y + self.size > self.canvas_size.y)

    def is_colliding_with_goal(self):
        """Check if the ball is colliding with the left or right wall."""
        return (self.position.x < 0 or
                self.position.x + self.size > self.canvas_size.x)

    def to_dict(self):
        return {
            "x": self.position.x,
            "y": self.position.y
        }
