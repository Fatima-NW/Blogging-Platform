"""
Serializers for the users app.

It includes:
- UserSerializer
- RegisterSerializer
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """ Serializer for returning basic user profile data """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'bio']
        read_only_fields = ["id", "email", "username"]


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
        """ Ensure that password and password2 match """
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        """ Create and return a new user with a validated password """
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
