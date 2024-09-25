import math
from pong.utils.vector2 import Vector2

def degree_to_vector(value: float):
    new_vector = Vector2(0, 0)
    # Convert angle from degrees to radians
    angle_radians = math.radians(value)
    # Calculate x and y components
    new_vector.x = math.cos(angle_radians)
    new_vector.y = math.sin(angle_radians)
    return (new_vector)


def vector_to_degree(value: Vector2):
    # Calculate angle in radians
    angle_radians = math.atan2(value.y, value.x)
    # Convert angle from radians to degrees
    angle_degrees = math.degrees(angle_radians)
    return (angle_degrees)