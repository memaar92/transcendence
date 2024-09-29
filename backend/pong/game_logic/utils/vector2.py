class Vector2:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other):
        return Vector2(self.x * other, self.y * other)
    
    def __truediv__(self, other):
        return Vector2(self.x / other, self.y / other)
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return f"({self.x}, {self.y})"

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }