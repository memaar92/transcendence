import os
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from .models import Games, CustomUser
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer, GameHistorySerializer, UserNameSerializer, UserCreateSerializer, TOTPSetupSerializer, TOTPVerifySerializer, GenerateOTPSerializer, ValidateEmailSerializer, CheckEmailSerializer, CustomTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError, AuthenticationFailed, NotAuthenticated, Throttled
from django.middleware import csrf
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes
from .permissions import IsSelf, Check2FA
from utils.utils import get_tokens_for_user
from utils.mixins import CookieCreationMixin
import pyotp
import qrcode
import random
import time
from io import BytesIO
import base64
import jwt


MAX_OTP_ATTEMPTS = 5
OTP_LOCK_TIME = 300
OTP_LIFETIME = 300


#TO DO: add a cron job that regularly deletes users that have not verified their email within a certain time frame
#TO DO: add a cron job that regularly deletes expired tokens from the blacklist


#everywhere where access token is sent, if expired --> 401 / detail: token expired
#out of the box:
'''
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [
        {
            "token_class": "AccessToken",
            "token_type": "access",
            "message": "Token is invalid or expired"
        }
    ]
}
'''


class CreateUserView(generics.CreateAPIView):
    # Discussion with Wayne:
    # (maybe differentiate between email and pw error)
    # TO DO: integrate backend library for pw checking

    queryset = CustomUser.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]
    
    

class EditUserView(generics.RetrieveUpdateDestroyAPIView):
    # not discussed with Wayne yet
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
    # not discussed with Wayne yet
    permission_classes = [IsAuthenticated, Check2FA]

    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        serializer = UserNameSerializer(user)
        return Response(serializer.data)

class GameHistoryList(APIView):
    # not discussed with Wayne yet
    permission_classes = [AllowAny]
    #only allow GET requests
    def get(self, request, format=None):
        games = Games.objects.all()
        serializer = GameHistorySerializer(games, many=True)
        return Response(serializer.data)
    
class ProfilePictureDeleteView(APIView):
    # not discussed with Wayne yet
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
    # not discussed with Wayne yet
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['qr_code']}
                },
            },
        },
    )

    def get(self, request):
# Get the token from the header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        # Decode the token to get the user ID
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = decoded_token.get('user_id')

        user_profile = get_object_or_404(CustomUser, id=user_id)
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

class TOTPVerifyView(APIView, CookieCreationMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = TOTPVerifySerializer

    @extend_schema(
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['2FA verification successful']}
                },
            },
            (400, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Refresh token not provided']}
                },
            },
            (401, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Invalid refresh token', 'Invalid 2fa token']},
                },
            },
        },
    )

    def post(self, request):
        # Get the token from the header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        # Decode the token to get the user ID
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = decoded_token.get('user_id')
        # Get the refresh token from the request data
        refresh_token = request.data['refresh']
        if not refresh_token:
            return Response({'detail': 'Refresh token not provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
        except Exception as e:
            return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get the user using the user ID
        user = get_object_or_404(CustomUser, id=user_id)
        serializer = TOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        totp = pyotp.TOTP(user.totp_secret)

        if totp.verify(serializer.validated_data['token']):
            if not user.is_2fa_enabled:
                user.is_2fa_enabled = True
                user.save()
            # Generate new tokens with custom claim
            refresh = RefreshToken.for_user(user)
            refresh['2fa'] = 2
            access = refresh.access_token
            token.blacklist()
            response = Response({
                'detail': '2FA verification successful',
                'access': str(access),
                'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
            self.createCookies(response)
            return response
        return Response({'detail': 'Invalid 2fa token'}, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView, CookieCreationMixin):

    # discussion with Wayne: 
    # 1. Successful login --> 200 / access and refresh tokens as cookies DONE
    # 2. User not found --> 404 / description (user not found) Q: In what case is this even triggered?
    # 3. Invalid credentials --> 401 / (No active account found with the given credentials) Out of the box: no differentiation between email and pw error
    # check if email is verified? (kinda already done when frontend checks if email is verified, but still if someone manages to call the login endpoint directly...)


    @extend_schema(
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Access and refresh tokens successfully created']},
                    '2fa': {'type': 'int', 'enum': [0, 1]}
                },
            },
            (401, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['No active account found with the given credentials']}
                },
            },
        },
    )

    def post(self, request, *args, **kwargs):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data
        response = Response(token, status=200)
        user = CustomUser.objects.get(email=request.data['email'])
        user_profile = get_object_or_404(CustomUser, email=user) # in what case is this even triggered?
        self.createCookies(response)
        csrf.get_token(request) #probably set by TokenObtainPairView or middleware already?

        if user_profile.is_2fa_enabled:
            response.data = {'detail': 'Access and refresh tokens successfully created', '2fa': 1}
        else:
            response.data = {'detail': 'Access and refresh tokens successfully created', '2fa': 0}
        return response

class CustomTokenRefreshView(TokenRefreshView, CookieCreationMixin):
    @extend_schema(
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Access and refresh tokens successfully created']}
                },
            },
            (401, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Token is blacklisted', 'Token is invalid or expired']},
                    'code': {'type': 'string', 'enum': ['token_not_valid']}
                },
            },
        },
    )

    def post(self, request, *args, **kwargs):
        print("request.data: ", request.data)
        response = super().post(request, *args, **kwargs)
        self.createCookies(response)
        response.data = {'detail': 'Access and refresh tokens successfully created'}
        return response


class CheckEmail(APIView):
    permission_classes = [AllowAny]
    serializer_class = CheckEmailSerializer

    @extend_schema(
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['User with this email exists']},
                    'id': {'type': 'integer'},
                    'email_verified': {'type': 'boolean'}
                },
            },
            (400, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Bad request']}
                },
            },
            (404, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['User with this email does not exist']}
                },
            },
        },
    )

    def post(self, request):
        serializer = CheckEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.filter(email=request.data['email']).values('email', 'email_verified', 'id')
        if user.exists():
            return Response({'detail': 'User with this email exists', 'id': user.first()['id'], 'email_verified': user.first()['email_verified']}, status=200)
        return Response({'detail': 'User with this email does not exist'}, status=404)


class GenerateOTPView(APIView): 
    permission_classes = [AllowAny]
    serializer_class = GenerateOTPSerializer

    @extend_schema(
        request=GenerateOTPSerializer,
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['OTP generated successfully']},
                    'id': {'type': 'integer'},
                    'email': {'type': 'string', 'format': 'email'}
                },
            },
            (400, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['User already verified']}
                },
            },
            (404, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['User not found']}
                },
            },
            (429, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Exceeded maximum OTP attempts or generations. Please try again later.']}
                },
            },
        },
    )

    def post(self, request):
        serializer = GenerateOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_profile = get_object_or_404(CustomUser, pk=request.data['id'])
        if user_profile.email_verified == True:
            return Response({'detail': 'User already verified'}, status=400)
        
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
        cache.set(otp_cache_key, otp, timeout=OTP_LIFETIME)
        cache.incr(otp_attempts_key)

        #send email with otp // for testing this is disabled and the otp is printed in the console
        print("send email with otp", otp)

        return Response({'detail': 'OTP generated successfully', 'id': user_profile.id, 'email': user_profile.email}, status=200)


class ValidateEmailView(APIView, CookieCreationMixin): 
    permission_classes = [AllowAny]
    serializer_class = ValidateEmailSerializer

    @extend_schema(
        request=ValidateEmailSerializer,
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Successfully verified']},
                },
            },
            # is there a better way to represent the different error messages with drf spectatular?
            (401, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Invalid OTP', 'OTP expired. Please request a new one.']},
                    'suberror code': {'type': 'int', 'enum': ['904', '905']},
                },
            },
            (404, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['User not found']}
                },
            },
            (429, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Exceeded maximum OTP attempts. Please try again later.']}
                },
            },
        },
    )

    def post(self, request):
        serializer = ValidateEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_profile = get_object_or_404(CustomUser, pk=request.data['id'])
        otp_provided = int(request.data['otp'])

        otp_attempts_key = f'{user_profile.id}_otp_attempts'
        otp_cache_key = f'{user_profile.id}_otp'
        stored_otp = cache.get(otp_cache_key)

        if not stored_otp:
            return Response({'detail': 'OTP expired. Please request a new one.', 'suberror code': 905}, status=401)

        if stored_otp != otp_provided:
            if cache.get(otp_attempts_key) >= MAX_OTP_ATTEMPTS:
                otp_lock_key = f'{user_profile.id}_otp_lock'
                cache.set(otp_lock_key, True, timeout=OTP_LOCK_TIME)
                cache.set(otp_attempts_key, 0)
                return Response({'detail': 'Exceeded maximum OTP attempts. Please try again later.'}, status=429)
            cache.incr(otp_attempts_key)
            return Response({'detail': 'Invalid OTP', 'suberror code': 904}, status=401)

        if stored_otp == otp_provided:
            cache.delete(otp_cache_key)
            cache.delete(otp_attempts_key)
            user_profile.email_verified = True
            user_profile.save()
            token = get_tokens_for_user(user_profile)
            response = Response(token, status=200)
            self.createCookies(response)
            response.data = {'detail': 'Successfully verified'}
            return response


class LogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if refresh_token is None:
                return Response({"detail": "Refresh token not provided"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response(status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], path=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH_PATH'])
            return response
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)