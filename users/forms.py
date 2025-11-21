"""
Forms for the users app

Includes:
- CustomUserCreationForm: Custom registration form using the CustomUser model
- ProfileForm: For users to edit their profile
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """ Form for user registration with additional fields """
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name","username", "email", "password1", "password2", "bio"]


class ProfileForm(forms.ModelForm):
    """ Form for editing user profile details """
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "bio"]

