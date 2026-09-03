from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "date_joined")
        read_only_fields = ("id", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "email", "username", "password", "first_name", "last_name")
        extra_kwargs = {
            "username": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
