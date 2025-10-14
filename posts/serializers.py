"""
Serializers for the posts app

It includes:
- PostSerializer
- CommentSerializer
"""

from rest_framework import serializers
from .models import Post, Comment

class PostSerializer(serializers.ModelSerializer):
    """ Handles serialization for Post model """
    author = serializers.StringRelatedField(read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'likes_count', 'comments_count']


class CommentSerializer(serializers.ModelSerializer):
    """ Handles serialization for Comment model """
    author = serializers.StringRelatedField(read_only=True)
    replied_to = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'parent', 'replied_to']
        read_only_fields = ['id', 'post', 'author', 'created_at', 'replied_to']
