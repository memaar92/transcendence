import json
import struct
from asyncio import sleep
import asyncio
from enum import Enum, auto
from channels.generic.websocket import AsyncWebsocketConsumer

import logging
logger = logging.getLogger(__name__)

class ClientState(Enum):
	SETUP = auto()
	READY = auto()
	RUNNING = auto()
	PAUSED = auto()

class MatchType(Enum):
	LOCAL_MATCHMAKING = auto()
	ONLINE_MATCHMAKING = auto()
	LOCAL_TOURNAMENT = auto()
	ONLINE_TOURNAMENT = auto()



class ClientSession:
	def __init__(self) -> None:
		self.state = ClientState.SETUP
		self.groups = []