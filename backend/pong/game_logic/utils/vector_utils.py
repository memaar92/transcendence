import math
from .vector2 import Vector2

def degree_to_vector(value: float) -> Vector2:
    """Convert an angle in degrees to a unit vector."""
    angle_radians = math.radians(value)
    return Vector2(math.cos(angle_radians), math.sin(angle_radians))

def vector_to_degree(value: Vector2) -> float:
    """Convert a vector to an angle in degrees."""
    angle_radians = math.atan2(value.y, value.x)
    return math.degrees(angle_radians)