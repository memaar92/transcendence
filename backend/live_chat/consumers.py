from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import Message, Relationship
from django.utils import timezone
from django.db import models
from django.db.models import Q
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
import json

RelationshipStatus = Relationship.RelationshipStatus

class ChatConsumer(AsyncWebsocketConsumer):

    user_id_to_channel_name = {}

    async def send_message_to_user(self, receiver_id, message, message_type, message_key):
        channel_name = ChatConsumer.user_id_to_channel_name.get(receiver_id, None)
        if channel_name:
            await self.channel_layer.send(channel_name, {
                "type": "send_websocket_message",
                "sender_id": self.user_id,    
                "receiver_id": receiver_id,    
                "text": json.dumps({
                    "type": message_type,
                    message_key: message,
                    "context": self.context,
                    "sender_id": self.user_id,
                    "receiver_id": receiver_id,
                    "sender_name": self.scope['user'].displayname
                }),
            })

    async def send_friends_list(self, user_id):
        friends_list = await self.get_friends_list(user_id)
        await self.send(text_data=json.dumps({
            'type': 'friends_list',
            'friends': friends_list,
            'context': self.context
        }))

    async def get_user_list(self):
        users_info = []
        for user_id in ChatConsumer.user_id_to_channel_name:
            user = await self.get_user(user_id)
            users_info.append({'id': str(user.id), 'name': user.displayname, 'profile_picture_url': user.profile_picture.url})
        return users_info

    async def send_websocket_message(self, event):
        await self.send(text_data=event['text'])

    async def broadcast_user_list(self):
         users_info = await self.get_user_list()
         for user_id, channel_name in ChatConsumer.user_id_to_channel_name.items():
             modified_users_info = [
                 {
                     'id': user['id'],
                     'name': user['name'],
                     'profile_picture_url': user['profile_picture_url']
                 }
                 for user in users_info if str(user['id']) != str(user_id)
             ]
             user_list_message = json.dumps({
                 'type': 'user_list',
                 'context': 'home',
                 'users': modified_users_info
             })
             await self.channel_layer.send(channel_name, {
                 'type': 'send_websocket_message',
                 'text': user_list_message
             })

    async def send_pending_chat_notifications(self, user_id):
        pending_requests = await self.get_pending_requests(user_id)
        for request in pending_requests:
            sender_id = request.user1_id
            if user_id == request.user2_id:
                sender_name = await self.get_user_displayname(sender_id)
                await self.send_message_to_user(sender_id, "Pending chat request", 'chat_request_notification', 'message')


    async def connect(self):
        token = self.scope['query_string'].decode().split('=')[1]

        if token:
            user_id = await self.get_user_id_from_jwt(token)
            if user_id:
                user = await self.get_user(user_id)
                if user:
                    self.scope['user'] = user
                    self.user_id = str(user.id)
                    self.context = None
                    ChatConsumer.user_id_to_channel_name[self.user_id] = self.channel_name
                    await self.accept()
                    # await self.send_friends_list(self.user_id)
                    print("Connected to chat")
                    return
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

        if message_type == 'set_context':

            self.context = data.get('context', None)
            await self.send(text_data=json.dumps({'type': 'user_id', 'user_id': self.user_id, 'context': self.context}))
            await self.broadcast_user_list()
            if self.context == 'home':
                await self.send_friends_list(self.user_id)
            return
        try:
            match self.context:
                case 'home':
                    await self.handleHomeContext(data)
                case 'chat':
                    await self.handleChatContext(data)
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown context: {context}'
                    }))
        except Exception as e:
            print(f"Error handling message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error handling message: {str(e)}'
            }))

    async def handleHomeContext(self, data):
        message_type = data.get('type', None)
        try:
            match message_type:
                case 'message_preview':
                    await self.send_latest_message(data['user_id_1'], data['user_id_2'])
                case 'chat_history':
                    await self.chat_history(data)
                case 'update_status':
                    await self.update_status(data['user_id_1'], data['user_id_2'], data['status'])
                    await self.send_friends_list(data['user_id_1'])
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}'
                    }))
        except Exception as e:
            print(f"Error handling message in home context: {e}")
            print(data)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error handling message in home context: {str(e)}'
            }))
    
    async def handleChatContext(self, data):
        message_type = data.get('type', None)
        try:
            match message_type:
                case 'chat_message':
                    await self.chat_message(data)
                case 'message_read':
                    await self.update_messages_status(data['sender_id'], data['receiver_id'])
                case 'chat_history':
                    await self.chat_history(data)
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}'
                    }))
        except Exception as e:
            print(f"Error handling message in chat context: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error handling message in chat context: {str(e)}'
            }))

    async def chat_request(self, data):
        receiver_id = data['receiver_id']
        sender_id = data['sender_id']
        print (f"Chat request from {sender_id} to {receiver_id}")
        if sender_id == receiver_id:
            return
        if receiver_id in ChatConsumer.user_id_to_channel_name:
            receiver_channel_name = ChatConsumer.user_id_to_channel_name[receiver_id]
            await self.update_status(sender_id, receiver_id, RelationshipStatus.PENDING)
            await self.channel_layer.send(
                receiver_channel_name,
                {
                    'type': 'chat_request_notification',
                    'context': self.context,
                    'sender_id': sender_id,
                    'sender_name': self.scope['user'].displayname,
                    'receiver_id': receiver_id
                }
            )

    async def send_latest_message(self, user_id_1):
        friends = await self.get_friends_list(user_id_1)
        # create an array of latest messages for each friend
        for friend in friends:
            latest_message = await self.get_latest_message(user_id_1, friend['id'])
            if latest_message:
                friend['latest_message'] = latest_message
            

        await self.send(text_data=json.dumps({
            'type': 'message_preview',
            'context': self.context,
            'message': latest_message
        }))

    async def chat_request_notification(self, event):
        await self.update_status(event['sender_id'], event['receiver_id'], RelationshipStatus.PENDING)
        await self.send(text_data=json.dumps({
            'type': 'chat_request_notification',
            'context': self.context,
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'sender_name': event['sender_name']
        }))

    async def chat_message(self, data):
        receiver_id = data.get('receiver_id')
        sender_id = data.get('sender_id')
        message = data.get('message')

        try:
            if not receiver_id or not sender_id or not message:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid message format.'
                }))
                return
            status = await self.get_status(sender_id, receiver_id)
            if status != RelationshipStatus.BEFRIENDED:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'You are not friends with this user.'
                }))
                return
            elif receiver_id in ChatConsumer.user_id_to_channel_name:
                receiver_channel_name = ChatConsumer.user_id_to_channel_name[receiver_id]
                if (self.user_id == sender_id):
                    await self.send_message_to_user(receiver_id, message, 'chat_message', 'message')
            else:
                print(f"Receiver {receiver_id} is offline. Message will be saved but not sent.")

            if (self.user_id == sender_id):
                await self.save_message(sender_id, receiver_id, message)
                await self.send_unread_messages_count(receiver_id)

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to send message: {str(e)}',
                'original_message': data
        }))

    async def chat_request_accepted(self, data):
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        await self.update_status(sender_id, receiver_id, RelationshipStatus.BEFRIENDED)

        await self.send_message_to_user(sender_id, f"You are now friends with {await self.get_user_displayname(receiver_id)}", 'chat_message', 'message')
        await self.send_message_to_user(receiver_id, f"You are now friends with {self.scope['user'].displayname}", 'chat_message', 'message')

        await self.send_friends_list(sender_id)
        await self.send_friends_list(receiver_id)

    async def chat_request_denied(self, data):
        receiver_displayname = await self.get_user_displayname(data['receiver_id'])
        await self.update_status(data['sender_id'], data['receiver_id'], RelationshipStatus.DEFAULT)
        await self.send_message_to_user(data['sender_id'], receiver_displayname, 'chat_request_denied', 'message')

    async def chat_history(self, data):
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        messages = await self.get_chat_history(sender_id, receiver_id)
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'context': self.context,
            'messages': messages,
            'sender_id': sender_id,
            'receiver_id': receiver_id
        }))

    async def send_unread_messages_count(self, user_id):
        unread_messages = await self.get_unread_messages_count(user_id)
        await self.send_message_to_user(user_id, unread_messages, 'unread_counts', 'unread_messages')

    @database_sync_to_async
    def update_messages_status(self, sender_id, receiver_id):
        Message.objects.filter(Q(sender_id=sender_id, receiver_id=receiver_id)).update(status='read')

    @database_sync_to_async
    def get_chat_history(self, sender_id, receiver_id):
        messages = Message.objects.filter(
            Q(sender_id=sender_id, receiver_id=receiver_id) | Q(sender_id=receiver_id, receiver_id=sender_id)
        ).order_by('timestamp')
        return [
            {
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id,
                'message': msg.content,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_name': msg.sender.displayname
            } for msg in messages
        ]

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message):
        sender = get_user_model().objects.get(id=sender_id)
        receiver = get_user_model().objects.get(id=receiver_id)
        msg = Message.objects.create(sender=sender, receiver=receiver, content=message, timestamp=timezone.now())
        return msg

    @database_sync_to_async
    def get_status(self, user_id_1, user_id_2):
        try:
            relationship = Relationship.objects.get(
                Q(user1_id=user_id_1, user2_id=user_id_2) | Q(user1_id=user_id_2, user2_id=user_id_1)
            )
            return relationship.status
        except Relationship.DoesNotExist:
            return RelationshipStatus.DEFAULT


    @database_sync_to_async
    def update_status(self, user_id_1, user_id_2, status):
        try:
            print(f"Updating status to {status} for {user_id_1} and {user_id_2}")
            relationship = Relationship.objects.get(
                Q(user1_id=user_id_1, user2_id=user_id_2) | Q(user1_id=user_id_2, user2_id=user_id_1)
            )
            relationship.status = status
            relationship.save()
        except Relationship.DoesNotExist:
            Relationship.objects.create(user1_id=user_id_1, user2_id=user_id_2, status=status)

    @database_sync_to_async
    def get_pending_requests(self, user_id):
        pending_requests = Relationship.objects.filter(
            Q(user2_id=user_id, status=RelationshipStatus.PENDING) | Q(user1_id=user_id, status=RelationshipStatus.PENDING)
        )
        return list(pending_requests)

    @database_sync_to_async
    def get_user_field(self, user_id, field_name):
        try:
            user = get_user_model().objects.get(id=user_id)
            return getattr(user, field_name, None)
        except get_user_model().DoesNotExist:
            return None

    @database_sync_to_async
    def get_friends_list(self, user_id):
        friends = Relationship.objects.filter(
            (Q(user1_id=user_id) | Q(user2_id=user_id)),
            status=RelationshipStatus.BEFRIENDED
        )
        friend_list = []
        user_model = get_user_model()
    
        for friend in friends:
            if str(friend.user1_id) == str(user_id):
                friend_id = friend.user2_id
            else:
                friend_id = friend.user1_id
    
            friend_user = user_model.objects.get(id=friend_id)
            friend_list.append({
                'id': str(friend_user.id),
                'name': friend_user.displayname,
                'profile_picture_url': friend_user.profile_picture.url if friend_user.profile_picture else None
            })
    
        return friend_list

    @database_sync_to_async
    def get_unread_messages_count(self, user_id):
        unread_messages = Message.objects.filter(
            receiver_id=user_id, status='unread'
        ).values('sender_id').annotate(count=models.Count('id'))
        unread_messages_dict = {msg['sender_id']: min(msg['count'], 99) for msg in unread_messages}
        return unread_messages_dict

    @database_sync_to_async
    def get_latest_message(self, user_id_1, user_id_2):
        messages = Message.objects.filter(
            Q(sender_id=user_id_1, receiver_id=user_id_2) | Q(sender_id=user_id_2, receiver_id=user_id_1)
        ).order_by('timestamp')
        if messages:
            latest_message = messages[0]
            return {
                'sender_id': latest_message.sender_id,
                'receiver_id': latest_message.receiver_id,
                'message': latest_message.content,
                'timestamp': latest_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_name': latest_message.sender.displayname
            }
        return None