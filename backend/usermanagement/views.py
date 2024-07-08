from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Games
from rest_framework import generics
from .serializers import UserSerializer, GameHistorySerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.
def json(request):
	# Render the main page
	return render(request, 'json.json')

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserGameHistory(generics.CreateAPIView):
      queryset = Games.objects.all()
      serializer_class = GameHistorySerializer
      permission_classes = [AllowAny]