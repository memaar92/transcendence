from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Chat, Message
from django.utils import timezone
from django.db.models import Q
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
import json

class ChatConsumer(AsyncWebsocketConsumer):
    
    user_id_to_channel_name = {}
    friends = {}

    async def send_message_to_user(self, receiver_id, message, message_type):
        channel_name = ChatConsumer.user_id_to_channel_name.get(receiver_id, None)
        if channel_name:
            await self.channel_layer.send(channel_name, {
                "type": "send_websocket_message",
                "sender_id": self.user_id,    
                "receiver_id": receiver_id,    
                "text": json.dumps({
                    "type": message_type,
                    "message": message,
                    "sender_id": self.user_id
                }),
            })

    async def get_user_list(self):
        users_info = []
        for user_id in ChatConsumer.user_id_to_channel_name:
            user = await self.get_user(user_id)
            users_info.append({'id': str(user.id), 'name': user.displayname})
        return users_info
        
    async def send_websocket_message(self, event):
        await self.send(text_data=event['text'])

    async def broadcast_user_list(self):
        users_info = await self.get_user_list()
        for user_id, channel_name in ChatConsumer.user_id_to_channel_name.items():
            modified_users_info = [
                {'id': user['id'], 'name': f"{user['name']}(you)" if str(user['id']) == str(user_id) else user['name']}
                for user in users_info
            ]
            user_list_message = json.dumps({
                'type': 'user_list',
                'users': modified_users_info
            })
            await self.channel_layer.send(channel_name, {
                'type': 'send_websocket_message',
                'text': user_list_message
            })

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
                    await self.broadcast_user_list()
                    await self.send(text_data=json.dumps({'type': 'user_id', 'user_id': self.user_id}))
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
        if hasattr(self, 'user_id') and self.user_id in ChatConsumer.user_id_to_channel_name:
            del ChatConsumer.user_id_to_channel_name[self.user_id]
            await self.broadcast_user_list()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', None)   

        print(f"Received message: {data}")
        if message_type == 'chat_request':
            await self.chat_request(data)
        elif message_type == 'chat_message':
            if data['sender_id'] in self.friends:
                await self.chat_message(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'chat_message',
                    'message': 'You are not friends with this user',
                    'sender_id': 'Server',
                    'receiver_id': data['sender_id']
                }))
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
        if sender_id == receiver_id:
            return
        if receiver_id in ChatConsumer.user_id_to_channel_name:
            receiver_channel_name = ChatConsumer.user_id_to_channel_name[receiver_id]
            sender_name = await self.get_user_displayname(sender_id)
            await self.channel_layer.send(
                receiver_channel_name,
                {
                    'type': 'chat_request_notification',
                    'sender_id': sender_id,
                    'sender_name': sender_name,
                    'receiver_id': receiver_id
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
                    'sender_id': sender_id,
                    'receiver_id': receiver_id
                }
            )
        await self.save_message(sender_id, receiver_id, message)


    async def add_friend(self, data):
        receiver_id = data['receiver_id']
        sender_id = data['sender_id']
        self.friends[sender_id] = receiver_id
        self.friends[receiver_id] = sender_id

    async def chat_history(self, data):
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        messages = await self.get_chat_history(sender_id, receiver_id)
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages,
            'sender_id': sender_id,
            'receiver_id': receiver_id
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
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'sender_name': event['sender_name']
        }))

    async def chat_message(self, event):
        sender_displayname = await self.get_user_displayname(event['sender_id'])
        await self.send_message_to_user(event['receiver_id'], event['message'], 'chat_message')

    async def chat_request_accepted(self, event):
        sender_id = event['sender_id']
        receiver_id = event['receiver_id']
        
        self.friends[sender_id] = receiver_id
        self.friends[receiver_id] = sender_id

        await self.send_message_to_user(sender_id, receiver_id, 'add_friend')
        await self.send_message_to_user(receiver_id, sender_id, 'add_friend')

        # Notify both users
        await self.send_message_to_user(sender_id, f"You are now friends with {await self.get_user_displayname(receiver_id)}", 'chat_request_accepted')
        await self.send_message_to_user(receiver_id, f"You are now friends with {await self.get_user_displayname(sender_id)}", 'chat_request_accepted')


    async def chat_request_denied(self, event):
        receiver_displayname = await self.get_user_displayname(event['receiver_id'])
        await self.send_message_to_user(event['sender_id'], receiver_displayname, 'chat_request_denied')

    @database_sync_to_async
    def get_user_displayname(self, user_id):
        user = get_user_model().objects.get(id=user_id)
        return user.displayname