"""
Serializers for the posts app

Includes serializers for:
- Posts
- Comments
- Nested Comments
"""

from rest_framework import serializers
from .models import Post, Comment

class PostSerializer(serializers.ModelSerializer):
    """ Handles serialization for Post model """
    author = serializers.StringRelatedField(read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)
    comments = serializers.SerializerMethodField() 

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'likes_count', 'comments_count', 'comments']

    def get_comments(self, obj):
        qs = obj.comments.filter(parent__isnull=True).order_by('-created_at')
        return CommentSerializer(qs, many=True).data


class NestedCommentSerializer(serializers.ModelSerializer):
    """ Serializer for nested replies """
    author = serializers.StringRelatedField(read_only=True)
    replied_to = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'parent', 'replied_to']
        read_only_fields = ['id', 'post', 'author', 'content', 'created_at', 'parent', 'replied_to']


class CommentSerializer(serializers.ModelSerializer):
    """ Serializer for top-level comments including nested replies """
    author = serializers.StringRelatedField(read_only=True)
    replied_to = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'parent', 'replied_to', 'replies']
        read_only_fields = ['id', 'post', 'author', 'created_at', 'replied_to', 'replies']

    def get_replies(self, obj):
        if obj.parent is not None:
            return None  
        qs = obj.replies.all().order_by('created_at')  
        return NestedCommentSerializer(qs, many=True).data