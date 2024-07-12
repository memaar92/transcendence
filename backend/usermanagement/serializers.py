from django.contrib.auth.models import User
from .models import Games, Profile
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
	profile_picture = serializers.SerializerMethodField()

	class Meta:
		model = User
		fields = ["id", "username", "password", "email", "first_name", "last_name", "profile_picture"]
		extra_kwargs = {"password": {"write_only": True}}

	def get_profile_picture(self, obj):
		try:
			profile = Profile.objects.get(user=obj)
			if profile.profile_picture:
				return profile.profile_picture.url
		except Profile.DoesNotExist:
			pass
		return None

	def create(self, validated_data):
		user = User.objects.create_user(**validated_data)
		Profile.objects.create(user=user)  # Create a profile for the user
		return user

class UserNameSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ["id", "username"]

class GameHistorySerializer(serializers.ModelSerializer):
	class Meta:
		model = Games
		fields = ["id", "home_id", "visitor_id", "visitor_score", "home_score", "created_at", "updated_at"]
		read_only_fields = fields

class ProfilePictureSerializer(serializers.ModelSerializer):
	class Meta:
		model = Profile
		fields = ['profile_picture']