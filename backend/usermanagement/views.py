import os
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from .models import Games, CustomUser
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer, GameHistorySerializer, UserNameSerializer, UserCreateSerializer, TOTPSetupSerializer, TOTPVerifySerializer, GenerateOTPSerializer, ValidateEmailSerializer, CheckEmailSerializer
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

MAX_OTP_ATTEMPTS = 5
OTP_LOCK_TIME = 300


#TO DO: add a cron job that regularly deletes users that have not verified their email within a certain time frame
#TO DO: add a cron job that regularly deletes expired tokens from the blacklist
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
		serializer = CheckEmailSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = CustomUser.objects.filter(email=request.data['email']).values('email', 'email_verified', 'id')
		if user.exists() and user.first()['email_verified'] == True:
			return Response({'detail': 'User with this email exists'}, status=status.HTTP_200_OK)
		elif user.exists() and user.first()['email_verified'] == False:
			return Response({'detail': 'User with this email exists but email not verified', 'id': user.first()['id']}, status=400) #status code?
		return Response({'detail': 'User with this email does not exist'}, status=status.HTTP_400_BAD_REQUEST) #tstaus code?


class GenerateOTPView(APIView): 
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = GenerateOTPSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user_profile = get_object_or_404(CustomUser, pk=request.data['id'])
		if user_profile.email_verified == True:
			return Response({'detail': 'User already verified'}, status=400) #what should be the status code here?
		
		otp_lock_key = f'{user_profile.id}_otp_lock'
		otp_attempts_key = f'{user_profile.id}_otp_attempts'
		otp_attempts = cache.get(otp_attempts_key)
		if not otp_attempts:
			cache.set(otp_attempts_key, 0)
			otp_attempts = cache.get(otp_attempts_key)

		#protect against brute force otp guessing
		if cache.get(otp_lock_key):
			return Response({'detail': 'Exceeded maximum OTP attempts or generations. Please try again later.'}, status=429)
		#protect against infinte otp generation
		if otp_attempts >= MAX_OTP_ATTEMPTS:
			cache.set(otp_lock_key, True, timeout=OTP_LOCK_TIME)
			cache.set(otp_attempts_key, 0)
			return Response({'detail': 'Exceeded maximum OTP generations. Please try again later.'}, status=429)

		otp = random.randint(100000, 999999)
		otp_cache_key = f'{user_profile.id}_otp'
		cache.set(otp_cache_key, otp, timeout=300)
		cache.incr(otp_attempts_key)

		#send email with otp
		print("send email with otp", otp)
		
		return Response({'message': 'OTP generated successfully', 'id': user_profile.id, 'email': user_profile.email}, status=200)
		

class ValidateEmailView(APIView, CookieCreationMixin): 
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = ValidateEmailSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user_profile = get_object_or_404(CustomUser, pk=request.data['id'])
		otp_provided = request.data['otp']

		otp_attempts_key = f'{user_profile.id}_otp_attempts'
		otp_cache_key = f'{user_profile.id}_otp'
		stored_otp = cache.get(otp_cache_key)

		if not stored_otp:
			return Response({'detail': 'OTP expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST) #status code?

		if stored_otp != otp_provided:
			if cache.get(otp_attempts_key) >= MAX_OTP_ATTEMPTS:
				otp_lock_key = f'{user_profile.id}_otp_lock'
				cache.set(otp_lock_key, True, timeout=OTP_LOCK_TIME)
				cache.set(otp_attempts_key, 0)
				return Response({'detail': 'Exceeded maximum OTP attempts. Please try again later.'}, status=429)
			cache.incr(otp_attempts_key)
			return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST) #status code?
		
		if stored_otp == otp_provided:
			cache.delete(otp_cache_key)
			cache.delete(otp_attempts_key)
			user_profile.email_verified = True
			user_profile.save()
			token = get_tokens_for_user(user_profile)
			response = Response(token, status=status.HTTP_200_OK)
			self.createCookies(response)
			return response

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
