from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("PongConsumer")

class MatchmakingConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.group_name = None

    async def connect(self):
        self.user_id = self.scope['user'].id

        if self.user_id is None:
            await self.close()
            logger.error("User not authenticated")
            return

        self.group_name = f"user_{self.user_id}"

        # Add user to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
    
    async def disconnect(self, close_code):
        if self.user_id is None:
            return

        # Remove user from group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        pass

    