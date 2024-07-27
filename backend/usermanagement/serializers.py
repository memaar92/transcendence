from .models import Games
from rest_framework import serializers
from .models import CustomUser

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
		fields = ['id', 'email', 'password', 'displayname', 'profile_picture'] #rm displayname and profile_picture?
		extra_kwargs = {"password": {"write_only": True}}

	def create(self, validated_data):
		user = CustomUser(
			email=validated_data['email'],
			displayname=validated_data['displayname'], # here a random displayname should be generated instead of using the one provided by the user
			profile_picture=validated_data.get('profile_picture', 'profile_pics/default.png') # here the defaault profile picture should be generated instead of using the one provided by the user
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