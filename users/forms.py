# Created file myself

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

# Registration form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name","username", "email", "password1", "password2"]

# Login form (we can use built-in AuthenticationForm, no need to redefine)
