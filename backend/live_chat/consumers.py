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
from pong.data_managment.user import User as PongUser
from pong.match.match_session_handler import MatchSessionHandler
from pong.data_managment.matches import Matches

RelationshipStatus = Relationship.RelationshipStatus
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    
    online_users = set()
    active_connections = {}

    async def send_message_to_user(self, receiver_id, message_info, value = False):
        print (f"Message type: {message_info.get('message_type')}")
        if not message_info.get("misc"):
            message_info["misc"] = None

        await self.channel_layer.group_send(
            f"chat_{receiver_id}",
            {
            "type": "send_websocket_message",  
            "text": json.dumps({
                "type": message_info.get("message_type"),
                message_info.get("message_key"): message_info.get("message"),
                "sender_id": self.user_id,
                "receiver_id": receiver_id,
                "sender_name": self.scope['user'].displayname,
                "timestamp": message_info.get("timestamp"),
                "message_id": str(uuid.uuid4()),
                "misc": message_info.get("misc"),
                "flag": value
            }),
            }
        )

    # for the patch method in the RelationshipStatusView
    async def http_send_friends_info(self, event):
        user_id = event['user_id']
        await self.send_friends_info(user_id)

    # for the patch method in the RelationshipStatusView
    async def http_send_pending_chat_notifications(self, event):
        user_id = event['user_id']
        await self.send_pending_chat_notifications(user_id)

    async def send_friends_info(self, user_id):
        friends_list = await self.get_friends_list(user_id)
        await self.send_message_to_user(user_id, {'message': friends_list, 'message_type': 'friends_list', 'message_key': 'friends'})

    async def send_websocket_message(self, event):
        message_data = json.loads(event['text'])
        message_data['context'] = self.context
        await self.send(text_data=json.dumps(message_data))


    async def broadcast_user_list(self):
        users_info = await self.get_user_list()
    
        all_blocked_users = {}
        for user_id in list(ChatConsumer.online_users):
            friends_list = await self.get_friends_list(user_id)
            blocked_users = [friend['id'] for friend in friends_list if friend['status'] == RelationshipStatus.BLOCKED]
            all_blocked_users[user_id] = blocked_users
    
        for user_id in list(ChatConsumer.online_users):
            blocked_users = all_blocked_users.get(user_id, [])
    
            blocked_by_users = {blocker for blocker, blocked in all_blocked_users.items() if user_id in blocked}
    
            modified_users_info = [
                {
                    'id': user['id'],
                    'name': user['displayname'],
                    'profile_picture_url': user['profile_picture'],
                    'is_online': user['id'] in ChatConsumer.online_users
                }
                for user in users_info 
                if user['id'] != user_id and user['id'] not in blocked_users and user['id'] not in blocked_by_users
            ]
    
            user_list_message = json.dumps({
                'type': 'user_list',
                'users': modified_users_info
            })
            await self.send_message_to_user(user_id, {
                'message': user_list_message,
                'message_type': 'user_list',
                'message_key': 'users'
            })

    async def send_pending_chat_notifications(self, user_id):
        pending_requests = await self.get_pending_requests(user_id)
        pending_requests_info = []

        for request in pending_requests:
            requester_id = request.requester_id
            requester_name = await self.get_user_field(requester_id, 'displayname')
            profile_picture = await self.get_user_field(requester_id, 'profile_picture')
            requester_profile_picture_url = profile_picture.url if profile_picture else None

            pending_requests_info.append({
                'requester_id': requester_id,
                'requester_name': requester_name,
                'requester_profile_picture': requester_profile_picture_url
            })

        await self.send_message_to_user(user_id, {
            'message': pending_requests_info,
            'message_type': 'pending_requests',
            'message_key': 'requests'
        })

    async def create_match(self, user_id):
        if await self.get_status(self.user_id, user_id) != RelationshipStatus.BEFRIENDED:
            return
        try:
            await self.check_users_registered(user_id)
        except Exception as e:
            await self.send_message_to_user(self.user_id, {
                'message': str(e),
                'message_type': 'game_error',
                'message_key': 'message',
                'misc': user_id
            }, value = True)
            return
        match = await MatchSessionHandler.create_match(int(self.user_id), int(user_id), MatchSessionHandler.remove_match)
        await MatchSessionHandler.send_match_ready_message(match.get_id(), int(self.user_id), int(user_id))
        await self.update_inviter(self.user_id, user_id, True)
        await self.send_message_to_user(self.user_id, {
            'message_type': 'match_id',
            'message_key': 'match_id',
            'message': match.get_id(),
        })
        await self.send_message_to_user(user_id, {
            'message_type': 'match_id',
            'message_key': 'match_id',
            'message': match.get_id(),
        })

    async def upcoming_match(self, event):
        await self.send_message_to_user(self.user_id, {
            'message': 'You have an upcoming tournament match!',
            'message_type': 'tournament',
            'message_key': 'message'
        })

    async def game_invite_cancelled(self, user_id):
        await self.update_inviter(self.user_id, user_id, True)
        await self.send_message_to_user(user_id, {
            'message': self.user_id,
            'message_type': 'game_invite_cancelled',
            'message_key': 'message'
        })

    async def check_users_registered(self, user_id):
        if PongUser.is_user_registered(int(self.user_id)):
            raise ValueError("You are already registered for a match or a tournament. Cancel your current registration to start a new one.")
        if PongUser.is_user_registered(int(user_id)):
            raise ValueError("The other user is already registered for a match or a tournament. Please try again later.")

    async def connect(self):
        if self.scope['user'] and not isinstance(self.scope['user'], AnonymousUser):
            await self.accept()
        else:
            await self.close()
            return
        self.user_id = str(self.scope['user'].id)
        self.context = None
        self.user_group_name = f"chat_{self.user_id}"

        # Check if the user already has active connections
        is_new_connection = self.user_id not in ChatConsumer.active_connections

        # Add the channel to the user's active connections
        if self.user_id in ChatConsumer.active_connections:
            ChatConsumer.active_connections[self.user_id].add(self.channel_name)
        else:
            ChatConsumer.active_connections[self.user_id] = {self.channel_name}

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        if is_new_connection:
            ChatConsumer.online_users.add(self.user_id)

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        if hasattr(self, 'user_id'):
            # Remove the channel from the user's active connections
            if self.user_id in ChatConsumer.active_connections:
                ChatConsumer.active_connections[self.user_id].discard(self.channel_name)
                if not ChatConsumer.active_connections[self.user_id]:
                    del ChatConsumer.active_connections[self.user_id]
                    ChatConsumer.online_users.remove(self.user_id)
                    await self.broadcast_user_list()

    async def receive(self, text_data):
        data = json.loads(text_data)

        try:
            if data.get('context', None) == 'setup':
                self.context = data.get('type', None)
                await self.send(text_data=json.dumps({'type': 'user_id', 'user_id': self.user_id, 'context': self.context}))
                if self.context == 'home':
                    await self.send_friends_info(self.user_id)
                    await self.send_unread_messages_count(self.user_id)
                    await self.send_pending_chat_notifications(self.user_id)
                if self.context == 'none':
                    await self.send_unread_messages_count(self.user_id)
                await self.broadcast_user_list()
                return
            match self.context:
                case 'home':
                    await self.handleHomeContext(data)
                case 'chat':
                    await self.handleChatContext(data)
                case 'none':
                    print ("Context is none")
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown context: {self.context}'
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
                    await self.update_status(data['sender_id'], data['receiver_id'], data['status'])
                    await self.send_friends_info(data['sender_id'])
                    await self.send_unread_messages_count(data['sender_id'])
                    await self.send_friends_info(data['receiver_id'])
                    await self.send_unread_messages_count(data['receiver_id'])
                    await self.broadcast_user_list()
                case 'chat_request_accepted':
                    await self.chat_request_accepted(data)
                case 'chat_request_denied':
                    await self.chat_request_denied(data)
                case 'game_invite':
                    try:
                        await self.check_users_registered(int(data['receiver_id']))
                    except Exception as e:
                        await self.send_message_to_user(int(data['sender_id']), {
                            'message': str(e),
                            'message_type': 'game_error',
                            'message_key': 'message',
                            'misc': data['receiver_id']
                        })
                        return
                    await self.update_inviter(data['sender_id'], data['receiver_id'])
                    await self.send_message_to_user(data['receiver_id'], {
                        'message': 'You have been invited to a game.',
                        'message_type': 'game_invite',
                        'message_key': 'message'
                    })
                case 'game_invite_accepted':
                    await self.create_match(data['sender_id'])
                case 'game_invite_cancelled':
                    await self.game_invite_cancelled(data['receiver_id'])
                case _:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}'
                    }))
        except Exception as e:
            print(f"Error handling message in home context: {e}")
    
    async def handleChatContext(self, data):
        message_type = data.get('type', None)
        try:
            receiver_id = await self.get_user_id_from_displayname(data.get('receiver_id'))
        except Exception as e:
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
            await self.send_message_to_user(receiver_id, {
                'message': message,
                'timestamp': timestamp,
                'message_type': 'chat_message',
                'message_key': 'message'})

            await self.save_message(sender_id, receiver_id, message, timestamp)
        except Exception as e:
            error_message = f"Error sending message: {str(e)}"
            error_traceback = traceback.format_exc()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': error_message,
                'traceback': error_traceback
            }))

    async def chat_request_accepted(self, data):
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        if (await self.get_status(sender_id, receiver_id)) != RelationshipStatus.PENDING:
            await self.send_message_to_user(sender_id, {
                'message': await self.get_user_field(receiver_id, 'displayname') + ' cancelled the request.',
                'message_type': 'request_status',
                'message_key': 'message'
            })

        await self.update_status(sender_id, receiver_id, RelationshipStatus.BEFRIENDED)

        await self.send_message_to_user(sender_id, {
            'message': 'You are now friends with ' + await self.get_user_field(receiver_id, 'displayname'),
            'message_type': 'request_status',
            'message_key': 'message'
        }, True)
        await self.send_message_to_user(receiver_id, {
            'message': 'You are now friends with ' + await self.get_user_field(sender_id, 'displayname'),
            'message_type': 'request_status',
            'message_key': 'message'
        }, True)

        await self.send_friends_info(sender_id)
        await self.send_friends_info(receiver_id)
        await self.broadcast_user_list()

    async def chat_request_denied(self, data):
        if (await self.get_status(data['sender_id'], data['receiver_id'])) != RelationshipStatus.PENDING:
            return
        receiver_displayname = await self.get_user_field(data['receiver_id'], 'displayname')
        await self.update_status(data['sender_id'], data['receiver_id'], RelationshipStatus.DEFAULT)
        await self.send_message_to_user(data['sender_id'], {
            'message': f'Your friend request was denied by {receiver_displayname}',
            'message_type': 'request_status',
            'message_key': 'message'
        })

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
        Message.objects.filter(Q(sender_id=receiver_id, receiver_id=sender_id)).update(status='read')

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
                'timestamp': msg.timestamp.isoformat(),
                'sender_name': msg.sender.displayname
            } for msg in messages
        ]

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, timestamp):
        sender = get_user_model().objects.get(id=sender_id)
        receiver = get_user_model().objects.get(id=receiver_id)
        msg = Message.objects.create(sender=sender, receiver=receiver, content=message, timestamp=timestamp)
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
            relationship = Relationship.objects.get(
                Q(user1_id=user_id_1, user2_id=user_id_2) | Q(user1_id=user_id_2, user2_id=user_id_1)
            )
            relationship.update_status(status, user_id_1)
        except Relationship.DoesNotExist:
            Relationship.objects.create(user1_id=user_id_1, user2_id=user_id_2, status=status)

    @database_sync_to_async
    def get_pending_requests(self, user_id):
        pending_requests = Relationship.objects.filter(
            (Q(user1_id=user_id) | Q(user2_id=user_id)) & Q(status=RelationshipStatus.PENDING) & ~Q(requester_id=user_id)
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
            (Q(user1_id=user_id) | Q(user2_id=user_id)) & 
            (Q(status=RelationshipStatus.BEFRIENDED) | Q(status=RelationshipStatus.BLOCKED))
        )
        friend_list = []
        user_model = get_user_model()

        for friend in friends:
            if str(friend.user1_id) == str(user_id):
                friend_id = friend.user2_id
            else:
                friend_id = friend.user1_id

            try:
                friend_user = user_model.objects.get(id=friend_id)
            except user_model.DoesNotExist:
                continue

            friend_list.append({
                'id': str(friend_user.id),
                'name': friend_user.displayname,
                'profile_picture_url': friend_user.profile_picture.url if friend_user.profile_picture else None,
                'chat': True if Message.objects.filter(Q(sender_id=user_id, receiver_id=friend_id) | Q(sender_id=friend_id, receiver_id=user_id)).exists() else False,
                'status': friend.status,
                'inviter_id': friend.inviter_id,
                'invitee_id': friend.user1_id if friend.user2_id == friend.inviter_id else friend.user2_id,
                'blocker_id': friend.blocker_id
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
                'timestamp': latest_message.timestamp.isoformat(),
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
        users = User.objects.filter(id__in=ChatConsumer.online_users)
        user_list = []
        for user in users:
            user_list.append({
                'id': str(user.id),
                'displayname': user.displayname,
                'profile_picture': user.profile_picture.url if user.profile_picture else None
            })
        return user_list

    @database_sync_to_async
    def get_user_id_from_displayname(self, displayname):
        try:
            user = User.objects.get(displayname=displayname)
            return user.id
        except User.DoesNotExist:
            return None

    @database_sync_to_async 
    def update_inviter(self, user1_id, user2_id, option = False):
        relationship = Relationship.objects.get(
            Q(user1_id=user1_id, user2_id=user2_id) | Q(user1_id=user2_id, user2_id=user1_id)
        ) 
        if option:
            relationship.inviter_id = None
        else:
            relationship.inviter_id = user1_id
        relationship.save()
        print ("Inviter ID: ", relationship.inviter_id)