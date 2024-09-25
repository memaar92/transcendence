class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }