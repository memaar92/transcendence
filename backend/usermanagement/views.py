import os
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import Games, CustomUser
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer, GameHistorySerializer, UserNameSerializer, UserCreateSerializer, TOTPSetupSerializer, TOTPVerifySerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.middleware import csrf
from .permissions import IsSelf
import pyotp
import qrcode
from io import BytesIO
import base64

class CreateUserView(generics.CreateAPIView):
	queryset = CustomUser.objects.all()
	serializer_class = UserCreateSerializer
	permission_classes = [AllowAny]

class EditUserView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class = UserSerializer
	permission_classes = [IsAuthenticated, IsSelf]
	http_method_names = ['patch', 'delete']
	queryset = CustomUser.objects.all()

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
		print("request", request)
		user = get_object_or_404(CustomUser, pk=pk)
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
	
class ProfilePictureDeleteView(APIView):
	permission_classes = [IsAuthenticated]

	def get_object(self):
		user = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
		if user != self.request.user:
			raise PermissionDenied("You don't have permission to delete this profile picture.")
		return user

	def delete(self, request, *args, **kwargs):
		user = self.get_object()
		default_picture = 'default.png'  # The default profile picture filename
		profile_pic_path = user.profile_picture.path

		if user.profile_picture.name != f'profile_pics/{default_picture}':  # Check if it's not the default picture
			if os.path.exists(profile_pic_path):
				os.remove(profile_pic_path)  # Delete the file if it exists

				# Update the profile picture to the default one
				user.profile_picture.name = f'profile_pics/{default_picture}'
				user.save()

		return Response(status=status.HTTP_204_NO_CONTENT)

class TOTPSetupView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		user_profile = request.user
		if not user_profile.totp_secret:
			user_profile.totp_secret = pyotp.random_base32()
			user_profile.save()

		totp = pyotp.TOTP(user_profile.totp_secret)
		uri = totp.provisioning_uri(request.user.displayname, issuer_name="Transcendence_Pongo")
		qr = qrcode.make(uri)
		buffered = BytesIO()
		qr.save(buffered, format="PNG")
		qr_code = base64.b64encode(buffered.getvalue()).decode()

		return Response({'qr_code': qr_code}, status=status.HTTP_200_OK)
	
#TODO: delete verify view, just for debugging
class TOTPVerifyView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = TOTPVerifySerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = CustomUser.objects.get(email=request.data['email'])
		user_profile = get_object_or_404(CustomUser, email=user)
		totp = pyotp.TOTP(user_profile.totp_secret)

		if totp.verify(serializer.validated_data['token']):
			return Response({'detail': '2FA verification successful'}, status=status.HTTP_200_OK)
		return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)



class CustomTokenObtainPairView(TokenObtainPairView):
	print("CustomTokenObtainPairView")
	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		user = CustomUser.objects.get(email=request.data['email'])
		user_profile = get_object_or_404(CustomUser, email=user)
		totp = pyotp.TOTP(user_profile.totp_secret)

		if user_profile.totp_secret:
			serializer = TOTPVerifySerializer(data=request.data)
			serializer.is_valid(raise_exception=True)
			print("2FA setup required")
			if not totp.verify(serializer.validated_data['token']):
				return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
		
		response.set_cookie(
			key = settings.SIMPLE_JWT['AUTH_COOKIE'],
			value = response.data['access'],
			expires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
			secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
			httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
			samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
		)
		response.set_cookie(
			key = settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
			value = response.data['refresh'],
			expires = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
			secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
			httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
			samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
		)
		del response.data['access']
		del response.data['refresh']
		csrf.get_token(request) #probably set by TokenObtainPairView or middleware already?
		return response


'''
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class LoginView(APIView)
	def post(self, request):
		data = request.data
		response = Response()
		username = data.get('username')
		password = data.get('password')
		user = authenticate(username=username, password=password)
		if user is not None:
			data = get_tokens_for_user(user)
			response.set_cookie(
								key = settings.SIMPLE_JWT['AUTH_COOKIE'],
								value = data['access'],
								expires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
								secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
								httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
								samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
			)
			csrf.get_token(request)
			response.data = {"Success" : "Login successfully","data":data}
			return response
		else:
			return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
'''