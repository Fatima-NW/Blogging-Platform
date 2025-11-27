"""
Models for the posts app

Includes:
- Post: Represents a blog post
- Comment: Represents comments on posts, supports nested replies
- Like: Represents a user liking a post
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Post(models.Model):
    """ Blog post model """
    title = models.CharField(max_length=120)
    content = models.TextField(max_length=20000)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    """ Comment model """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )
    replied_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="replies_received"
    )

    def __str__(self):
        return f"Comment by {self.author} on {self.post.title}"
    
    def save(self, *args, **kwargs):
        """ Validate that comment content does not exceed 2000 characters """
        if self.content and len(self.content) > 2000:
            raise ValidationError("Content cannot exceed 2000 characters.")
        super().save(*args, **kwargs)


class Like(models.Model):
    """ Like model """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return f"{self.user} liked {self.post}"
