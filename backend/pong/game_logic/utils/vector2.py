class Vector2:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }