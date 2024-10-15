from django.conf import settings
from .utils.vector2 import Vector2
from .utils.vector_utils import degree_to_vector
import logging

logger = logging.getLogger("Ball")

SPEED_MULTIPLIER = settings.GAME_CONFIG['ball']['speed_multiplier']

class Ball:
    def __init__(self,
                position: Vector2 = Vector2(0, 0),
                direction: Vector2 = degree_to_vector(45),
                speed: float = 8,
                size: int = 0.2,
                canvas_size: Vector2 = Vector2(10000, 10000),
                collider_list: list = None):
        self._position: Vector2 = position
        self._direction: Vector2 = direction
        self._base_speed: float = speed
        self._current_speed: float = speed
        self._size: int = size
        self._start_pos: Vector2 = position.copy()
        self._time_alive: float = 0

        # Game configuration
        self._canvas_size: Vector2 = canvas_size

        # List of colliders that the ball can collide with
        self._collider_list: list = collider_list if collider_list is not None else []
        self._collided_with_list: list = []

    def move(self, delta_time: float) -> None:
        """Update the ball's position based on its speed and direction."""

        # Update the ball's speed based on how long it has been alive
        self._current_speed = self._base_speed + self._time_alive * SPEED_MULTIPLIER
        movement_vector = self._direction * self._current_speed * delta_time
        new_position = self._position + movement_vector

        if self._is_colliding_with_wall(new_position):
            movement_vector.y *= -1
            self._direction.y *= -1
        elif self._is_colliding(new_position):
            for collider in self._collided_with_list:
                self._redirect_based_on_collider(collider)
            movement_vector = self._direction * self._current_speed * delta_time
            new_position = self._position + movement_vector
            if self._is_colliding_with_wall(new_position):
                movement_vector.y *= -1
                self._direction.y *= -1

        self._position += movement_vector
        self._time_alive += delta_time

    def reset(self):
        """Reset the ball to its starting position."""
        self._position = self._start_pos.copy()
        self._direction = degree_to_vector(45) * (-1 if self._direction.x < 0 else 1)
        self._current_speed = self._base_speed
        self._time_alive = 0

    def _is_colliding(self, position: Vector2) -> bool:
        """Check if the ball is colliding with a collider object."""
        for collider in self._collider_list:
            collider_position = collider.get_position()
            collider_size = collider.get_size()
            if (collider_position.x < position.x + self._size and
                collider_position.x + collider_size.x > position.x and
                collider_position.y < position.y + self._size and
                collider_position.y + collider_size.y > position.y):
                if collider not in self._collided_with_list:
                    self._collided_with_list.append(collider)
                return True
            elif collider in self._collided_with_list:
                self._collided_with_list.remove(collider)
        return False

    def _is_colliding_with_wall(self, position: Vector2) -> bool:
        """Check if the ball is colliding with the top or bottom wall."""
        if position is None:
            position = self._position
        return (position.y < 0 or
                position.y + self._size > self._canvas_size.y)

    def _is_colliding_with_goal(self, position: Vector2) -> bool:
        """Check if the ball is colliding with the left or right wall."""
        if position is None:
            position = self._position
        return (position.x < 0 or
                position.x + self._size > self._canvas_size.x)

    def _redirect_based_on_collider(self, collider: object) -> None:
        """Redirect the ball based on the center of mass of the collider."""
        collider_center = collider.get_position() + collider.get_center_of_mass()
        ball_center = self._position + Vector2(self._size / 2, self._size / 2)
        direction_vector = ball_center - collider_center
        self._direction = direction_vector.normalized()

    def get_position(self) -> Vector2:
        '''Get the position of the ball'''
        return self._position

    def get_size(self) -> int:
        '''Get the size of the ball'''
        return self._size

    def get_speed(self) -> float:
        '''Get the current speed of the ball'''
        return self._current_speed

    def get_direction(self) -> Vector2:
        '''Get the direction of the ball'''
        return self._direction

    def to_dict(self):
        return {
            "x": self._position.x,
            "y": self._position.y
        }