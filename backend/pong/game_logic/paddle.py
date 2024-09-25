from utils.vector2 import Vector2

class Paddle:
    def __init__(self, position: Vector2 = Vector2(0, 0), size: Vector2 = Vector2(20, 100), speed: float = 10.0, world_size: Vector2 = Vector2(10000, 10000)):
        self.position: Vector2 = position
        self.size: Vector2 = size
        self.speed: float = speed
        self.direction: int = 0 # -1, 0, 1
        self.world_size: Vector2 = world_size

    def move(self):
        if self.direction == 0:
            return
        velocity = self.speed * self.direction
        new_y = self.position.y + velocity

        if new_y < 0:
            self.position.y = 0
        elif new_y + self.size.y > self.world_size.y:
            self.position.y = self.world_size.y - self.size.y
        else:
            self.position.y = new_y

    def to_dict(self):
        return {
            "x": self.position.x,
            "y": self.position.y
        }