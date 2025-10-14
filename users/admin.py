"""
Admin configuration for the users app.

Registers:
- CustomUser
"""

from django.contrib import admin
from .models import CustomUser

admin.site.register(CustomUser)


