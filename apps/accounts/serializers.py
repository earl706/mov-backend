from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import ProductivityProfile

User = get_user_model()


class ProductivityProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductivityProfile
        exclude = ["id", "user"]
        read_only_fields = ["momentum_score", "burnout_risk", "consistency_score", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProductivityProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "uuid", "email", "full_name", "avatar_url", "timezone", "profile"]
        read_only_fields = ["id", "uuid"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["email", "full_name", "password", "timezone"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds basic user info to the token response for convenience."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
