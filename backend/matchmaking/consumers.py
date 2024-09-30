import json
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer

import logging
logger = logging.getLogger(__name__)


class MatchmakingConsumer(AsyncWebsocketConsumer):

    playerQueue = [] # Die Queue ist vielleicht unsinn, eine Variable sollte auch reichen
    queueLock = asyncio.Lock() # Initialize the lock
    roomID = None

    async def connect(self):
        await self.accept()
        async with self.queueLock:
            if len(self.playerQueue < 2):
                self.playerQueue.append(self.channel_name)
                self.roomID = uuid.uuid4()
            self.ownRoomID = self.roomID
            await self.channel_layer.group_add(self.roomID, self.channel_name)
            if len(self.playerQueue == 2):
                send_start_message()
                self.playerQueue.pop(0)
                MatchmakingConsumer.broadcast_task = asyncio.create_task(self.broadcast_game_data())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        del MatchmakingConsumer.connected_users[self.channel_name]
        number_of_connected_users = len(MatchmakingConsumer.connected_users)
        if number_of_connected_users == 0 and MatchmakingConsumer.broadcast_task:
            MatchmakingConsumer.broadcast_task.cancel()
            MatchmakingConsumer.broadcast_task = None

    async def receive(self, text_data):
        # Process incoming message from WebSocket
        user_id = self.channel_name
        if text_data:
            text_data_json = json.loads(text_data)
            if text_data_json["type"] == "player_update":
                payload = text_data_json["payload"]
                direction = payload["direction"]
                if direction < -1 or direction > 1:
                    return
                if user_id == self.player_1.connection_id:
                    self.player_1.direction = payload["direction"]
                elif user_id == self.player_2.connection_id:
                    self.player_2.direction = payload["direction"]