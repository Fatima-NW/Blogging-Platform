"""
Forms for the users app

Includes:
- CustomUserCreationForm: Custom registration form using the CustomUser model
- ProfileForm: For users to edit their profile
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """ Form for user registration with additional fields """
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name","username", "email", "password1", "password2", "bio"]


class ProfileForm(forms.ModelForm):
    """ Form for editing user profile details """
    current_password = forms.CharField(
        label="Current Password",
        required=False,
        widget=forms.PasswordInput()
    )
    new_password1 = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput()
    )
    new_password2 = forms.CharField(
        label="Confirm Password",
        required=False,
        widget=forms.PasswordInput()
    )

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "bio"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if current_password or new_password1 or new_password2:
            
             # All fields must be filled
            if not current_password:
                self.add_error("current_password", "Enter your current password.")
            if not new_password1:
                self.add_error("new_password1", "Enter a new password.")
            if not new_password2:
                self.add_error("new_password2", "Confirm your new password.")

            # If all are filled, do further validation
            if current_password and new_password1 and new_password2:
                if not self.user.check_password(current_password):
                    self.add_error("current_password", "Current password is incorrect.")
                if new_password1 != new_password2:
                    self.add_error("new_password2", "Passwords do not match!")
                else:
                    try:
                        validate_password(new_password1, user=self.user)
                    except ValidationError as e:
                        self.add_error("new_password1", e.messages)
