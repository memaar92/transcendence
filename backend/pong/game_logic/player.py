import uuid

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