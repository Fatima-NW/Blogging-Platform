""" 
Admin configuration for the posts app 

Registers: 
- Post
- Comment
- Like
"""

from django.contrib import admin
from .models import Post, Comment, Like

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
