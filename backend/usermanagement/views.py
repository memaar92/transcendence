from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.conf import settings
from .models import Games
from rest_framework import generics
from rest_framework.response import Response
from .serializers import UserSerializer, GameHistorySerializer, UserNameSerializer, ProfilePictureSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class ChangeUserView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = UserSerializer
	permission_classes = [IsAuthenticated]
	http_method_names = ['patch', 'delete']

	def get_object(self):
		return self.request.user

	def patch(self, request, *args, **kwargs):
		instance = self.get_object()
		serializer = self.get_serializer(instance, data=request.data, partial=True)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserView(APIView):
	permission_classes = [IsAuthenticated]

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

class ProfilePictureView(generics.UpdateAPIView):
	serializer_class = ProfilePictureSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		user = get_object_or_404(User, pk=self.kwargs['pk'])
		return user.profile

	def perform_update(self, serializer):
		instance = self.get_object()
		if 'profile_picture' in self.request.data:
			# Save the new profile picture
			serializer.save()

class ProfilePictureDeleteView(generics.DestroyAPIView):
	permission_classes = [IsAuthenticated]

	def get_object(self):
		user = get_object_or_404(User, pk=self.kwargs['pk'])
		return user.profile

	def delete(self, request, *args, **kwargs):
		instance = self.get_object()
		default_path = os.path.join(settings.MEDIA_ROOT, 'profiles/default/profilepic.jpg')
		profile_pic_path = instance.profile_picture.path

		if os.path.exists(profile_pic_path):
			os.remove(profile_pic_path)

		# Replace with default profile picture
		instance.profile_picture.save('profilepic.jpg', ContentFile(open(default_path, 'rb').read()))
		return Response(status=status.HTTP_204_NO_CONTENT)
