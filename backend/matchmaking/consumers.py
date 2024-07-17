import json
import struct
from asyncio import sleep
import asyncio

import logging
logger = logging.getLogger(__name__)

from channels.generic.websocket import AsyncWebsocketConsumer

class MatchmakingConsumer(AsyncWebsocketConsumer):
	