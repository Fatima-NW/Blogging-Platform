"""
Forms for the users app

Includes:
- CustomUserCreationForm: Custom registration form using the CustomUser model
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """ Form for user registration with additional fields """
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name","username", "email", "password1", "password2", "bio"]
