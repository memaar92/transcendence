from .utils.vector2 import Vector2

class Paddle:
    def __init__(self, position: Vector2 = Vector2(0, 0), size: Vector2 = Vector2(20, 100), speed: float = 10.0, world_size: Vector2 = Vector2(10000, 10000), center_of_mass = None) -> None:
        self._base_position: Vector2 = position.copy()
        self._current_position: Vector2 = position
        self.size: Vector2 = size
        self.speed: float = speed
        self.direction: int = 0 # -1, 0, 1
        self.world_size: Vector2 = world_size
        self._center_of_mass: Vector2 = center_of_mass if center_of_mass is not None else Vector2(position.x + size.x / 2, position.y + size.y / 2)

    def move(self, delta_time: float) -> None:
        if self.direction == 0:
            return

        self._current_position.y += self.direction * self.speed * delta_time
        # Ensure the paddle stays within the world bounds
        self._current_position.y = max(0, min(self._current_position.y, self.world_size.y - self.size.y))

    def get_position(self) -> Vector2:
        return self._current_position
    
    def get_size(self) -> Vector2:
        return self.size
    
    def reset_position(self) -> None:
        print(f"Resetting paddle position to {self._base_position}")
        self._current_position = self._base_position.copy()

    def get_center_of_mass(self) -> Vector2:
        return self._center_of_mass

    def to_dict(self):
        return {
            "x": self._current_position.x,
            "y": self._current_position.y
        }