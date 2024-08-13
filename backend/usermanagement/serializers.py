from .models import Games
from rest_framework import serializers
from .models import CustomUser
from utils.utils import generateUsername
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = CustomUser
		fields = ['id', 'email', 'displayname', 'profile_picture']

class UserNameSerializer(serializers.ModelSerializer):
	class Meta:
		model = CustomUser
		fields = ["id", "displayname"]

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

class GameHistorySerializer(serializers.ModelSerializer):
	class Meta:
		model = Games
		fields = ["id", "home_id", "visitor_id", "visitor_score", "home_score", "created_at", "updated_at"]
		read_only_fields = fields

class TOTPSetupSerializer(serializers.Serializer):
	qr_code = serializers.CharField()

class TOTPVerifySerializer(serializers.Serializer):
	token = serializers.CharField()

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