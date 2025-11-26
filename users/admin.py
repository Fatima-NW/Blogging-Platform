"""
Admin configuration for the users app

Registers:
- CustomUser
- Notification
"""

from django.contrib import admin
from .models import CustomUser, Notification

admin.site.register(CustomUser)
admin.site.register(Notification)


