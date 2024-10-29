from django.http import JsonResponse
from rest_framework.views import APIView
from django.db.models import Q
from .models import Relationship
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

class RelationshipStatusView(APIView):
    def get(self, request, user_id_1, user_id_2):
        try:
            relationship = Relationship.objects.get(
                Q(user1_id=user_id_1, user2_id=user_id_2) | Q(user1_id=user_id_2, user2_id=user_id_1)
            )
            relationship_data = serialize('json', [relationship])
            relationship_dict = json.loads(relationship_data)[0]
            return JsonResponse({"relationship": relationship_dict}, status=200)
        except Relationship.DoesNotExist:
            return JsonResponse({"message": "Relationship does not exist"}, status=200)

    def patch(self, request, user_id_1, user_id_2):
        try:
            relationship, created = Relationship.objects.filter(
                Q(user1_id=user_id_1, user2_id=user_id_2) | Q(user1_id=user_id_2, user2_id=user_id_1)
            ).get_or_create(
                defaults={'user1_id': user_id_1, 'user2_id': user_id_2}
            )
            if created:
                relationship.requester_id = user_id_1
                relationship.save()
            if 'status' in request.data:
                relationship.update_status(request.data['status'], request.user.id)
            relationship_data = serialize('json', [relationship])
            relationship_dict = json.loads(relationship_data)[0]
            channel_layer = get_channel_layer()
            if request.data['status'] == 'PD':
                async_to_sync(channel_layer.group_send)(
                    f"chat_{user_id_2}",
                    {
                        "type": "http_send_pending_chat_notifications",
                        "user_id": user_id_2
                    }
                )
            else:
                async_to_sync(channel_layer.group_send)(
                    f"chat_{user_id_1}",
                    {
                        "type": "http_send_friends_info",
                        "user_id": user_id_1
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    f"chat_{user_id_2}",
                    {
                        "type": "http_send_friends_info",
                        "user_id": user_id_2
                    }
                )
            return JsonResponse({"relationship": relationship_dict}, status=200)
        except Exception as e:
            #print(e)
            return JsonResponse({"error": str(e)}, status=400)