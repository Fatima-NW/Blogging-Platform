from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)   # ensure emails are unique
    bio = models.TextField(blank=True, null=True) # bio field added in database
    
    def __str__(self):
        return self.username

