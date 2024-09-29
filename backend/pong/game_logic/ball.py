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
        self._position: Vector2 = position
        self._direction: Vector2 = direction
        self._speed: float = speed
        self._size: int = size
        self._start_pos: Vector2 = copy.deepcopy(position)

        # Game configuration
        self._canvas_size: Vector2 = canvas_size

        # List of colliders that the ball can collide with
        self._collider_list: list = collider_list if collider_list is not None else []
        self._collided_with_list: list = []

    def move(self, delta_time: float) -> None:
        """Update the ball's position based on its speed and direction."""

        movement_vector = self._direction * self._speed * delta_time
        new_position = self._position + movement_vector
        if self._is_colliding_with_wall(new_position):
            movement_vector.y *= -1
            self._direction.y *= -1
        elif self._is_colliding(new_position):
            movement_vector.x *= -1
            self._direction.x *= -1
        self._position += movement_vector

    def reset(self):
        """Reset the ball to its starting position."""
        self._position = copy.deepcopy(self._start_pos)

    def _is_colliding(self, position: Vector2):
        """Check if the ball is colliding with a collider object."""
        for collider in self._collider_list:
            if (collider.position.x < position.x + self._size and
                collider.position.x + collider.size.x > position.x and
                collider.position.y < position.y + self._size and
                collider.position.y + collider.size.y > position.y):
                if collider not in self._collided_with_list:
                    self._collided_with_list.append(collider)
                return True
            elif collider in self._collided_with_list:
                self._collided_with_list.remove(collider)
        return False

    def _is_colliding_with_wall(self, position: Vector2):
        """Check if the ball is colliding with the top or bottom wall."""
        if position is None:
            position = self._position
        return (position.y < 0 or
                position.y + self._size > self._canvas_size.y)

    def _is_colliding_with_goal(self, position: Vector2):
        """Check if the ball is colliding with the left or right wall."""
        if position is None:
            position = self._position
        return (position.x < 0 or
                position.x + self._size > self._canvas_size.x)
    
    def get_position(self):
        return self._position
    
    def get_size(self):
        return self._size
    
    def get_speed(self):
        return self._speed
    
    def get_direction(self):
        return self._direction

    def to_dict(self):
        return {
            "x": self._position.x,
            "y": self._position.y
        }
