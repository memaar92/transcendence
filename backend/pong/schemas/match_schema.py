from pydantic import BaseModel
from typing import Literal

class PlayerInput(BaseModel):
    type: Literal["player_input"]
    direction: int
    player_id: int

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

