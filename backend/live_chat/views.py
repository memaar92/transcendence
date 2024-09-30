from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from django.db.models import Q
from .models import Relationship
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def live_chat(request):
    return render(request, 'live_chat.html')

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
            return JsonResponse({"message": "Relationship does not exist"}, status=400)

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
            if 'requester' in request.data:
                if request.data['requester'] is None:
                    relationship.requester = None
                else:
                    relationship.requester = User.objects.get(id=request.data['requester'])
                relationship.save()
            relationship_data = serialize('json', [relationship])
            relationship_dict = json.loads(relationship_data)[0]
            return JsonResponse({"relationship": relationship_dict}, status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, status=400)