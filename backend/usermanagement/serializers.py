from django.contrib.auth.models import User
from .models import Games
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user

class GameHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Games
        fields = ["id", "home_id", "visitor_id", "visitor_score", "home_score", "created_at", "updated_at"]
        read_only_fields = fields

