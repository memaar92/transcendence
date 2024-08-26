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
from django.contrib.auth.models import AnonymousUser
import json
import traceback
import uuid
from django_redis import get_redis_connection

RelationshipStatus = Relationship.RelationshipStatus
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    
    online_users = set()

    async def send_message_to_user(self, receiver_id, message_info):
        await self.channel_layer.group_send(
            str(receiver_id),
            {
                "type": "send_websocket_message",  
                "text": json.dumps({
                    "type": message_info.get("message_type"),
                    message_info.get("message_key"): message_info.get("message"),
                    "sender_id": self.user_id,
                    "receiver_id": receiver_id,
                    "sender_name": self.scope['user'].displayname,
                    "timestamp": message_info.get("timestamp"),
                    "message_id": str(uuid.uuid4())
                }),
            }
        )

    async def send_friends_info(self, user_id):
        friends_list = await self.get_friends_list(user_id)
        await self.send_message_to_user(user_id, {'message': friends_list, 'message_type': 'friends_list', 'message_key': 'friends'})

    async def send_websocket_message(self, event):
        message_data = json.loads(event['text'])
        message_id = message_data.get('message_id')

        redis_conn = get_redis_connection("default")
        redis_key = f"msg:{message_id}:{self.user_id}"

        try:
            print(f"Setting Redis key: {redis_key} with value 1")
            if redis_conn.setnx(redis_key, "1"):
                print(f"Key {redis_key} set successfully and expiration set to 300 seconds.")
                message_data['context'] = self.context
                await self.send(text_data=json.dumps(message_data))
                redis_conn.delete(redis_key)
            else:
                print(f"Duplicate message {message_id} for user {self.user_id}. Key {redis_key} already exists.")
        except Exception as e:
            print(f"Redis error: {str(e)}. Sending message anyway.")
            message_data['context'] = self.context
            await self.send(text_data=json.dumps(message_data))

    async def broadcast_user_list(self):
        users_info = await self.get_user_list()
        for user_id in ChatConsumer.online_users:
            modified_users_info = [
                {
                    'id': user['id'],
                    'name': user['displayname'],
                    'profile_picture_url': user['profile_picture']
                }
                for user in users_info if str(user['id']) != str(user_id)
            ]
            user_list_message = json.dumps({
                'type': 'user_list',
                'users': modified_users_info
            })
            await self.send_message_to_user(user_id, {'message': user_list_message, 'message_type': 'user_list', 'message_key': 'users'}
            )

    # async def send_pending_chat_notifications(self, user_id):
    #     pending_requests = await self.get_pending_requests(user_id)
    #     for request in pending_requests:
    #         sender_id = request.user1_id
    #         if user_id == request.user2_id:
    #             sender_name = await self.get_user_displayname(sender_id)
    #             await self.send_message_to_user(sender_id, "Pending chat request", 'chat_request_notification', 'message')


    async def connect(self):
        if self.scope['user'] and not isinstance(self.scope['user'], AnonymousUser):
            print(f"Client connected: {self.scope['user']}")
            print(f"User ID: {self.scope['user'].id}")
            await self.accept()
        else:
            print("Client not authenticated")
            await self.close()
            return
        self.user_id = str(self.scope['user'].id)
        self.context = None
        self.user_group_name = self.user_id
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        ChatConsumer.online_users.add(self.user_id)
        await self.broadcast_user_list()
        return

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        if hasattr(self, 'user_id'):
            self.online_users.remove(self.user_id)
            await self.broadcast_user_list()

            # Clean up Redis keys
            redis_conn = get_redis_connection("default")
            redis_keys = redis_conn.keys(f"msg:*:{self.user_id}")
            for key in redis_keys:
                redis_conn.delete(key)


    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"Received message: {data}")

        if self.context is None:
            self.context = data.get('context', None)
        try:
            match self.context:
                case 'home':
                    await self.handleHomeContext(data)
                case 'chat':
                    await self.handleChatContext(data)
                case 'setup':
                    self.context = data.get('type', None)
                    await self.send(text_data=json.dumps({'type': 'user_id', 'user_id': self.user_id, 'context': self.context}))
                    if self.context == 'home':
                        await self.send_friends_info(self.user_id)
                        await self.send_unread_messages_count(self.user_id)
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown context: {context}'
                    }))
        except Exception as e:
            print(f"Error handling message: {e}")

    async def handleHomeContext(self, data):
        message_type = data.get('type', None)
        try:
            match message_type:
                case 'message_preview':
                    await self.send_latest_message()
                case 'update_status':
                    await self.update_status(data['user_id_1'], data['user_id_2'], data['status'])
                    await self.send_friends_info(data['user_id_1'])
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}'
                    }))
        except Exception as e:
            print(f"Error handling message in home context: {e}")
    
    async def handleChatContext(self, data):
        message_type = data.get('type', None)
        print(f"Handling chat context message: {data}")
        try:
            receiver_id = await self.get_user_id_from_displayname(data.get('receiver_id'))
        except Exception as e:
            print(f"Error getting receiver ID: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error getting receiver ID: {str(e)}'
            }))
            return
        try:
            match message_type:
                case 'chat_message':
                    await self.chat_message(data, receiver_id)
                case 'message_read':
                    await self.update_messages_status(data['sender_id'], receiver_id)
                case 'chat_history':
                    await self.chat_history(data, receiver_id)
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}'
                    }))
        except Exception as e:
            error_message = f"Error handling message in chat context: {str(e)}"
            error_traceback = traceback.format_exc()
            print(f"{error_message}\n{error_traceback} for user {self.user_id}")
            
    # async def chat_request(self, data):
    #     receiver_id = data['receiver_id']
    #     sender_id = data['sender_id']
    #     print (f"Chat request from {sender_id} to {receiver_id}")
    #     if sender_id == receiver_id:
    #         return
    #     if receiver_id in ChatConsumer.user_id_to_channel_name:
    #         receiver_channel_name = ChatConsumer.user_id_to_channel_name[receiver_id]
    #         await self.update_status(sender_id, receiver_id, RelationshipStatus.PENDING)
    #         await self.channel_layer.send(
    #             receiver_channel_name,
    #             {
    #                 'type': 'chat_request_notification',
    #                 'context': self.context,
    #                 'sender_id': sender_id,
    #                 'sender_name': self.scope['user'].displayname,
    #                 'receiver_id': receiver_id
    #             }
    #         )

    async def send_latest_message(self):
        friends = await self.get_friends_list(self.user_id)
        latest_messages = {}

        for friend in friends:
            latest_message = await self.get_latest_message(self.user_id, friend['id'])
            if latest_message:
                latest_messages[friend['id']] = latest_message

        await self.send_message_to_user(self.user_id, {
            'message': latest_messages,
            'message_type': 'message_preview',
            'message_key': 'latest_messages'
        })


    # async def chat_request_notification(self, event):
    #     await self.update_status(event['sender_id'], event['receiver_id'], RelationshipStatus.PENDING)
    #     await self.send(text_data=json.dumps({
    #         'type': 'chat_request_notification',
    #         'context': self.context,
    #         'sender_id': event['sender_id'],
    #         'receiver_id': event['receiver_id'],
    #         'sender_name': event['sender_name']
    #     }))

    async def chat_message(self, data, receiver_id):
        sender_id = data.get('sender_id')
        message = data.get('message')
        timestamp = data.get('timestamp')

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
            # elif receiver_id in self.online_users:
            print(f"Sending message to {receiver_id}")
            await self.send_message_to_user(receiver_id, {
                'message': message,
                'timestamp': timestamp,
                'message_type': 'chat_message',
                'message_key': 'message'})

            await self.save_message(sender_id, receiver_id, message)
            await self.send_unread_messages_count(receiver_id)
        except Exception as e:
            error_message = f"Error sending message: {str(e)}"
            error_traceback = traceback.format_exc()
            print(f"{error_message}\n{error_traceback} for user {self.user_id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': error_message,
                'traceback': error_traceback
            }))

    # async def chat_request_accepted(self, data):
    #     sender_id = data['sender_id']
    #     receiver_id = data['receiver_id']
    #     await self.update_status(sender_id, receiver_id, RelationshipStatus.BEFRIENDED)

    #     await self.send_message_to_user(sender_id, f"You are now friends with {await self.get_user_displayname(receiver_id)}", 'chat_message', 'message')
    #     await self.send_message_to_user(receiver_id, f"You are now friends with {self.scope['user'].displayname}", 'chat_message', 'message')

    #     await self.send_friends_info(sender_id)
    #     await self.send_friends_info(receiver_id)

    # async def chat_request_denied(self, data):
    #     receiver_displayname = await self.get_user_displayname(data['receiver_id'])
    #     await self.update_status(data['sender_id'], data['receiver_id'], RelationshipStatus.DEFAULT)
    #     await self.send_message_to_user(data['sender_id'], receiver_displayname, 'chat_request_denied', 'message')

    async def chat_history(self, data, receiver_id):
        sender_id = data['sender_id']
        messages = await self.get_chat_history(sender_id, receiver_id)
        await self.send_message_to_user(sender_id, {
            'message': messages,
            'message_type': 'chat_history',
            'message_key': 'messages'
        })

    async def send_unread_messages_count(self, user_id):
        unread_messages = await self.get_unread_messages_count(user_id)
        await self.send_message_to_user(user_id, {'message': unread_messages, 'message_type': 'unread_counts', 'message_key': 'unread_messages'})

    @database_sync_to_async
    def update_messages_status(self, sender_id, receiver_id):
        print(f"Updating messages status for {sender_id} and {receiver_id}")
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
                'profile_picture_url': friend_user.profile_picture.url if friend_user.profile_picture else None,
                'chat': True if Message.objects.filter(Q(sender_id=user_id, receiver_id=friend_id) | Q(sender_id=friend_id, receiver_id=user_id)).exists() else False
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
        ).order_by('-timestamp')
        if messages:
            latest_message = messages.first()
            return {
                'sender_id': latest_message.sender_id,
                'receiver_id': latest_message.receiver_id,
                'message': latest_message.content,
                'timestamp': latest_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_name': latest_message.sender.displayname
            }
        return None

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

    @database_sync_to_async
    def get_user_list(self):
        return list(User.objects.filter(id__in=ChatConsumer.online_users).values('id', 'displayname', 'profile_picture'))

    @database_sync_to_async
    def get_user_id_from_displayname(self, displayname):
        try:
            user = User.objects.get(displayname=displayname)
            return user.id
        except User.DoesNotExist:
            return None