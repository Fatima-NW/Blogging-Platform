"""
Custom user model for the users app

Extends Django's AbstractUser to include:
- Unique email
- Optional bio
"""

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """ Custom user model with unique email and optional bio field """
    email = models.EmailField(unique=True)   
    bio = models.TextField(blank=True, null=True, max_length=300) 
    
    def __str__(self):
        return self.username


class Notification(models.Model):
    """ Notification for a user about posts, comments, or other events """
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(max_length=500)
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('posts.Comment', on_delete=models.CASCADE, null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:80]}"
