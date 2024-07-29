import json
import struct
import asyncio
from enum import Enum, auto
from pong.matchmaking.MatchHandler import MatchHandler
from django.contrib.auth.models import AnonymousUser
import uuid

import logging
logger = logging.getLogger("PongConsumer")

from channels.generic.websocket import AsyncWebsocketConsumer

class SetupFailed(Exception):
    def __init__(self, message="Setup failed"):
        self.message = message
        super().__init__(self.message)

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

class ClientConsumer(AsyncWebsocketConsumer):
    def __init__(self) -> None:
        self.id = uuid.uuid4()
        self.state = ClientState.SETUP
        self.match_handler = MatchHandler()
        self.groups = self.groups or []
        self._receive_queue = asyncio.Queue()
        self._closed = False

    async def connect(self):
        # Check if user is authenticated
        if self.scope['user'] and not isinstance(self.scope['user'], AnonymousUser):
            print(f"Client connected: {self.scope['user']}")
            print(f"User ID: {self.scope['user'].id}")
            await self.accept()
        else:
            print("Client not authenticated")
            await self.close()
            return
        # await self.accept()
        self.match_handler.register_client(self)
        logger.info(f"Client connected: {self.channel_name}, ID: {self.id}")

    async def disconnect(self, close_code):
        self.match_handler.unregister_client(self)
        self._closed = True

    async def receive(self, text_data):
        match self.state:
            case ClientState.SETUP:
                text_data_json = {}
                try:
                    text_data_json = json.loads(text_data)            
                except:
                    return

                message_type = text_data_json.get("type", "")

                if message_type == "setup":
                    try:
                        await self.handleSetup(text_data_json.get("matchType", ""))
                        self.state = ClientState.RUNNING
                        logger.info("Client setup complete")
                    except SetupFailed:
                        await self.sendSetupStatus(False)
            case ClientState.READY:
                if message_type == "ready":
                    return
            case ClientState.RUNNING:
                self._receive_queue.put_nowait(text_data)
                logger.info(f"Received data: {text_data}")
            case ClientState.PAUSED:
                pass
            case _:
                return
            
    def get_receive_queue_item(self):
        if self._receive_queue.qsize() == 0:
            return None
        return self._receive_queue.get_nowait()

    async def sendSetupStatus(self, status: bool) -> None:
        message = {"Type": "setup", "valid": status}
        logger.info(f"Sending Setup message to Client: {message}")
        try:
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def sendHandshake(self, type: MatchType) -> None:
        match type:
            case MatchType.LOCAL_MATCHMAKING:
                pass
            case MatchType.ONLINE_MATCHMAKING:
                await self.sendSetupStatus(True);
            case MatchType.LOCAL_TOURNAMENT:
                pass
            case MatchType.ONLINE_TOURNAMENT:
                pass

    async def handleSetup(self, text_data: str) -> None:
        match text_data:
            case "onlineMM":
                await self.sendHandshake(MatchType.ONLINE_MATCHMAKING)
            case _:
                raise SetupFailed()
