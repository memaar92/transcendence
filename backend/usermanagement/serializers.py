from .models import Games
from rest_framework import serializers
from .models import CustomUser
from utils.utils import generateUsername
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'displayname', 'profile_picture', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

class UserNameSerializer(serializers.ModelSerializer):
    # game_history = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'displayname', 'profile_picture']  # Add other user fields as needed

    # def get_game_history(self, obj):
    #     games = Games.objects.filter(home_id=obj) | Games.objects.filter(visitor_id=obj)
    #     return GameSerializer(games, many=True).data

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Games
        fields = ['id', 'home_id', 'visitor_id', 'visitor_score', 'home_score', 'created_at']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'password']
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        username = generateUsername()
        while CustomUser.objects.filter(displayname=username).exists():
            username = generateUsername()
        user = CustomUser(
            email=validated_data['email'],
            displayname=username,
            profile_picture='profile_pics/default.png'
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class TOTPSetupSerializer(serializers.Serializer):
    qr_code = serializers.CharField()

class TOTPVerifySerializer(serializers.Serializer):
    token = serializers.CharField()
    refresh = serializers.CharField()

class GenerateOTPSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class ValidateEmailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    otp = serializers.IntegerField(min_value=100000, max_value=999999)

class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        if user.is_2fa_enabled:
            token['2fa'] = 1
        else:
            token['2fa'] = 0
        return token
