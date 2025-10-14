"""
Custom user model for the users app.

Extends Django's AbstractUser to include:
- Unique email
- Optional bio
"""

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """ Custom user model with unique email and optional bio field """
    email = models.EmailField(unique=True)   
    bio = models.TextField(blank=True, null=True) 
    
    def __str__(self):
        return self.username
