import os
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from .models import Games, CustomUser
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer, GameHistorySerializer, UserNameSerializer, UserCreateSerializer, TOTPSetupSerializer, TOTPVerifySerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.middleware import csrf
from .permissions import IsSelf
import pyotp
import qrcode
import random
import time
from io import BytesIO
import base64

#MAX_OTP_ATTEMPTS = 5

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
		print("request user view", request)
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


class CookieCreationMixin:
	def createCookies(self, response):
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
			path = settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH_PATH'],
			expires = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
			secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
			httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
			samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
		)
		del response.data['access']
		del response.data['refresh']
		

class CustomTokenObtainPairView(TokenObtainPairView, CookieCreationMixin):
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
		
		self.createCookies(response)
		csrf.get_token(request) #probably set by TokenObtainPairView or middleware already?
		return response


class CustomTokenRefreshView(TokenRefreshView, CookieCreationMixin):
	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		self.createCookies(response)
		return response

class CheckEmail(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		if CustomUser.objects.filter(email=request.data['email']).exists():
			return Response({'detail': 'User with this email exists'}, status=status.HTTP_200_OK)
		return Response({'detail': 'User with this email does not exist'}, status=status.HTTP_400_BAD_REQUEST)
		# add another state for when users have started the registration but not completed email verification


class GenerateOTPView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		user = CustomUser.objects.filter(email=request.data['email']).values('email', 'email_verified')
		if not user.exists():
			return  Response({'detail': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
		if user.first()['email_verified'] == True:
			return Response({'detail': 'User already verified'}, status=status.HTTP_400_BAD_REQUEST)
		
		'''
		otp_attempts_key = f'{request.data["email"]}_otp_attempts'
		otp_attempts = cache.get(otp_attempts_key, 0)

		if otp_attempts >= MAX_OTP_ATTEMPTS:
			return Response({'detail': 'Exceeded maximum OTP attempts. Please try again later.'}, status=429) 
		'''


		otp = random.randint(100000, 999999)
		otp_cache_key = f'{request.data["email"]}_otp'
		cache.set(otp_cache_key, otp, timeout=300)
		#cache.incr(otp_attempts_key)
		#send email with otp
		print("send email with otp", otp)
		
		return Response({'status': 'success', 'message': 'OTP generated successfully', 'email': request.data['email']}, status=200)
		

#add a class view that is routed to when user enters email token and click on "verify"
#should create access token and refresh token and set them as cookies
class ValidateEmailView(APIView, CookieCreationMixin):
	permission_classes = [AllowAny]

	def post(self, request):
		user = CustomUser.objects.get(email=request.data['email'])
		otp_provided = int(request.data['otp'])

		#check if user is locked due to too many attempts

		otp_cache_key = f'{request.data["email"]}_otp'
		stored_otp = cache.get(otp_cache_key)

		if not stored_otp:
			return Response({'detail': 'OTP expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
		if stored_otp != otp_provided:
			#increment attempts
			return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
		if stored_otp == otp_provided:
			cache.delete(otp_cache_key)
			#cache.delete(f'{request.data["email"]}_otp_attempts')
			user.email_verified = True
			user.save()
			#generate access token and refresh token
			token = get_tokens_for_user(user)
			#set them as cookies
			response = Response(token, status=status.HTTP_200_OK)
			self.createCookies(response)
			return response

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
