from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Games
from rest_framework import generics
from rest_framework.response import Response
from .serializers import UserSerializer, GameHistorySerializer, UserNameSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class ChangeUserView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = UserSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		return User.objects.filter(pk=user.pk)

class UserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        # check if user is the same as the one requesting
        if request.user.pk == user.pk:
            serializer = UserSerializer(user)
        else:
            serializer = UserNameSerializer(user)
        return Response(serializer.data)

class GameHistoryList(APIView):
    permission_classes = [AllowAny]
	#only allow GET requests
    def get(self, request, format=None):
        games = Games.objects.all()
        serializer = GameHistorySerializer(games, many=True)
        return Response(serializer.data)

