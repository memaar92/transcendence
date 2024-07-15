from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Chat, Message
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
import json

class ChatConsumer(AsyncWebsocketConsumer):
    user_id_to_channel_name = {}

    async def connect(self):
        # Extract the token from the query string
        token = self.scope['query_string'].decode().split('=')[1]

        if token:
            user_id = await self.get_user_id_from_jwt(token)
            if user_id:
                user = await self.get_user(user_id)
                if user:
                    self.scope['user'] = user
                    self.user_id = str(user.id)
                    ChatConsumer.user_id_to_channel_name[self.user_id] = self.channel_name
                    await self.accept()
                    print("Connected to chat")
                    return

        # Close the connection if no valid token is provided
        await self.close()

    @database_sync_to_async
    def get_user_id_from_jwt(self, token):
        try:
            
            decoded_data = UntypedToken(token)
            user_id = decoded_data['user_id']
            return user_id
        except (InvalidToken, TokenError) as e:
            print(f"Error decoding token: {e}")
            return None

    @database_sync_to_async
    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        if self.user_id in ChatConsumer.user_id_to_channel_name:
            del ChatConsumer.user_id_to_channel_name[self.user_id]

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', None)

        if message_type == 'chat_request':
            await self.chat_request(data)
        elif message_type == 'chat_message':
            await self.chat_message(data)
        elif message_type == 'chat_request_accepted':
            await self.chat_request_accepted(data)
        elif message_type == 'chat_request_denied':
            await self.chat_request_denied(data)
        elif message_type == 'add_friend':
            await self.add_friend(data)
        elif message_type == 'chat_history':
            await self.chat_history(data)

    async def chat_request(self, data):
        receiver_id = data['receiver_id']
        sender_id = data['sender_id']
        if receiver_id in ChatConsumer.user_id_to_channel_name:
            receiver_channel_name = ChatConsumer.user_id_to_channel_name[receiver_id]
            await self.channel_layer.send(
                receiver_channel_name,
                {
                    'type': 'chat_request_notification',
                    'sender_id': sender_id
                }
            )

    async def chat_message(self, data):
        receiver_id = data['receiver_id']
        sender_id = data['sender_id']
        message = data['message']
        if receiver_id in ChatConsumer.user_id_to_channel_name:
            receiver_channel_name = ChatConsumer.user_id_to_channel_name[receiver_id]
            await self.channel_layer.send(
                receiver_channel_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': sender_id
                }
            )
        await self.save_message(sender_id, receiver_id, message)

    async def chat_request_accepted(self, data):
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        if sender_id in ChatConsumer.user_id_to_channel_name:
            sender_channel_name = ChatConsumer.user_id_to_channel_name[sender_id]
            await self.channel_layer.send(
                sender_channel_name,
                {
                    'type': 'chat_request_accepted',
                    'receiver_id': receiver_id
                }
            )

    async def chat_request_denied(self, data):
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        if sender_id in ChatConsumer.user_id_to_channel_name:
            sender_channel_name = ChatConsumer.user_id_to_channel_name[sender_id]
            await self.channel_layer.send(
                sender_channel_name,
                {
                    'type': 'chat_request_denied',
                    'receiver_id': receiver_id
                }
            )

    async def add_friend(self, data):
        receiver_id = data['receiver_id']
        sender_id = data['sender_id']
        if receiver_id in ChatConsumer.user_id_to_channel_name:
            receiver_channel_name = ChatConsumer.user_id_to_channel_name[receiver_id]
            await self.channel_layer.send(
                receiver_channel_name,
                {
                    'type': 'add_friend',
                    'receiver_id': receiver_id,
                    'sender_id': sender_id
                }
            )

    async def chat_history(self, data):
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        messages = await self.get_chat_history(sender_id, receiver_id)
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages
        }))

    @database_sync_to_async
    def get_chat_history(self, sender_id, receiver_id):
        messages = Message.objects.filter(
            (Q(sender_id=sender_id) & Q(receiver_id=receiver_id)) |
            (Q(sender_id=receiver_id) & Q(receiver_id=sender_id))
        ).order_by('timestamp')
        return [{'sender_id': msg.sender_id, 'content': msg.content, 'timestamp': msg.timestamp} for msg in messages]

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message):
        sender = get_user_model().objects.get(id=sender_id)
        receiver = get_user_model().objects.get(id=receiver_id)
        Message.objects.create(sender=sender, receiver=receiver, content=message, timestamp=timezone.now())

    async def chat_request_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_request_notification',
            'sender_id': event['sender_id']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id']
        }))

    async def chat_request_accepted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_request_accepted',
            'receiver_id': event['receiver_id']
        }))

    async def chat_request_denied(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_request_denied',
            'receiver_id': event['receiver_id']
        }))

    async def add_friend(self, event):
        await self.send(text_data=json.dumps({
            'type': 'add_friend',
            'receiver_id': event['receiver_id'],
            'sender_id': event['sender_id']
        }))
