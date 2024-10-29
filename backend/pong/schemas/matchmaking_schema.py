from pydantic import BaseModel
from typing import Literal

class ActiveConnection(BaseModel):
    type: Literal["active_connection"]

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class QueueRegister(BaseModel):
    type: Literal["queue_register"]

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class QueueUnregister(BaseModel):
    type: Literal["queue_unregister"]

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class QueueIsRegistered(BaseModel):
    type: Literal["queue_is_registered"]

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class LocalMatchCreate(BaseModel):
    type: Literal["local_match_create"]

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class TournamentCreate(BaseModel):
    type: Literal["tournament_create"]
    name: str
    max_players: int

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class TournamentRegister(BaseModel):
    type: Literal["tournament_register"]
    tournament_id: str

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class TournamentUnregister(BaseModel):
    type: Literal["tournament_unregister"]
    tournament_id: str

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]

class TournamentStart(BaseModel):
    type: Literal["tournament_start"]
    tournament_id: str

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]
    
class TournamentCancel(BaseModel):
    type: Literal["tournament_cancel"]
    tournament_id: str

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]
    
class TournamentGetOpen(BaseModel):
    type: Literal["tournament_get_open"]

    @classmethod
    async def get_type(cls):
        return cls.__annotations__['type'].__args__[0]