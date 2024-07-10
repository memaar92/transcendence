import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Chat, Message

class ChatConsumer(AsyncWebsocketConsumer):
    user_id_to_channel_name = {}

    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user_id = str(self.scope["user"].id)
        else:
            self.user_id = "anonymous_" + self.channel_name
        ChatConsumer.user_id_to_channel_name[self.user_id] = self.channel_name
        await self.accept()
        print("Connected to chat")
        print (self.user_id)
        print(self.channel_name)
        await self.broadcast_user_list()

    async def disconnect(self, close_code):
        if self.user_id in ChatConsumer.user_id_to_channel_name:
            del ChatConsumer.user_id_to_channel_name[self.user_id]
        print("Disconnected from chat")
        await self.close()
        await self.broadcast_user_list()

    async def broadcast_user_list(self):
        users = await self.get_user_list()
        for user_id, channel_name in ChatConsumer.user_id_to_channel_name.items():
            modified_users = [
                f"{user}(you)" if str(user) == user_id else user
                for user in users
            ]
            user_list_message = json.dumps({
                'type': 'user_list',
                'users': modified_users
            })
            await self.channel_layer.send(channel_name, {
                'type': 'send_websocket_message',
                'text': user_list_message
            })

    async def send_websocket_message(self, event):
        # Method to handle sending the actual WebSocket message
        await self.send(text_data=event['text'])

    async def send_message_to_user(self, receiver_id, message, type):
        receiver_id = str(receiver_id)
        channel_name = ChatConsumer.user_id_to_channel_name.get(receiver_id)
        print ("USER " + self.user_id + " SENT MESSAGE TO " + receiver_id + " " + message + " " + type)
        if channel_name:
            await self.channel_layer.send(channel_name, {
                "type": type,
                "sender_id": self.user_id,
                "receiver_id": receiver_id,
                "message": message,
            })
    
    async def chat_request(self, event):
            sender_id = self.user_id
            receiver_id = event['receiver_id']
            await self.send_message_to_user(receiver_id, 'You have a new chat request from ' + sender_id, 'chat_request')

    async def chat_request_denied(self, event):
        sender_id = self.user_id
        receiver_id = event['receiver_id']

        await self.send_message_to_user(receiver_id, 'Your chat request to ' + receiver_id + ' was denied', 'chat_request_denied')

    async def chat_request_accepted(self, event):
        sender_id = self.user_id
        receiver_id = event['receiver_id']

        await self.send_message_to_user(receiver_id, 'Your chat request to ' + receiver_id + ' was accepted', 'chat_request_accepted')

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            receiver_id = text_data_json.get('receiver_id')

            match message_type:
                case 'chat_request':
                    await self.chat_request(text_data_json)
                case 'chat_request_accepted':
                    await self.chat_request_accepted(text_data_json)
                case 'chat_request_denied':
                    await self.chat_request_denied(text_data_json)
                case 'chat_message':
                    chat = await self.get_or_create_chat(self.user_id, receiver_id)
                    if not chat:
                        return
                    await self.save_message(chat, text_data_json.get('content'), self.user_id, receiver_id)
                    await self.send_message_to_user(receiver_id, text_data_json.get('content'), 'chat_message')
                case 'request_user_list':
                    await self.send_user_list()
                case _:
                    print('Unknown message type')

    async def send_user_list(self):
        # Fetch or construct the user list
        users = self.get_user_list()
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': users
        }))

    @database_sync_to_async
    def get_user_list(self):
        connected_user_ids = list(ChatConsumer.user_id_to_channel_name.keys())
        connected_user_ids_str = [str(user_id) for user_id in connected_user_ids]
        return connected_user_ids_str

    @database_sync_to_async
    def get_or_create_chat(self, sender_id, receiver_id):
        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return None

        chats = Chat.objects.filter(participants=sender).filter(participants=receiver)

        chats = [chat for chat in chats if chat.participants.count() == 2]

        if chats:
            return chats[0]
        else:
            chat = Chat.objects.create()
            chat.participants.add(sender, receiver)
            return chat

    @database_sync_to_async
    def save_message(self, chat, content, sender_id, receiver_id):
        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return None
        return Message.objects.create(chat=chat, content=content, sender=sender, receiver=receiver, timestamp=timezone.now())