"""
Serializers for the users app

It includes:
- UserSerializer
- RegisterSerializer
- DeleteSerializer
- NotificationSerializer
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for returning basic user profile data """
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'bio', 'new_password']
        read_only_fields = ["id", "email"]

    def validate_new_password(self, value):
        if value:
            validate_password(value, self.instance)
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration — validates and creates new users."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2', 'bio']
        extra_kwargs = {
            'bio': {'required': False},  
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class DeleteSerializer(serializers.Serializer):
    """ Serializer for account deletion via API """
    confirm = serializers.CharField(allow_blank=True)

    def validate_confirm(self, value):
        if value != "DELETE":
            raise serializers.ValidationError("You must type DELETE to confirm.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """ Serializer for displaying user notifications """
    created_at = serializers.DateTimeField(format="%d-%m-%Y %H:%M")

    class Meta:
        model = Notification
        fields = ['id', 'message', 'read', 'created_at']
