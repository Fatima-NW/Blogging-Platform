"""
Model tests for the posts app

Includes tests for:
- Post model: creation and string representation
- Comment model: creation, replies, and content validation
- Like model: creation and uniqueness constraints

Uses pytest fixtures for creating test users and posts
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from posts.models import Post, Comment, Like
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------- FIXTURES ----------------

@pytest.fixture
def user(db):
    """ Create a test user """
    return User.objects.create_user(
        username="fatima",
        email="fatima@example.com",
        password="pass123"
    )

@pytest.fixture
def another_user(db):
    """ Create a second user """
    return User.objects.create_user(
        username="alex",
        email="alex@example.com",
        password="pass123"
    )

@pytest.fixture
def post(user):
    """ Create a Ssample post """
    return Post.objects.create(title="Sample Post", content="Some content", author=user)


# ---------------- POST MODEL TESTS ----------------

@pytest.mark.django_db
def test_post_creation(post):
    """ Post should save and return correct string representation """
    assert Post.objects.count() == 1
    assert str(post) == "Sample Post"
    assert post.author.username == "fatima"


# ---------------- COMMENT MODEL TESTS ----------------

@pytest.mark.django_db
def test_comment_creation(post, user):
    """ Comments should link correctly to post and user """
    comment = Comment.objects.create(post=post, author=user, content="Nice post!")
    assert comment.post == post
    assert comment.author == user
    assert str(comment) == f"Comment by {user} on {post.title}"

@pytest.mark.django_db
def test_comment_reply(post, user, another_user):
    """ Comments can have replies (parent-child relationship) """
    parent = Comment.objects.create(post=post, author=user, content="Parent comment")
    reply = Comment.objects.create(
        post=post, author=another_user, content="Reply here", parent=parent, replied_to=user
    )
    assert reply.parent == parent
    assert reply.replied_to == user
    assert reply.parent.replies.count() == 1

@pytest.mark.django_db
def test_comment_rejects_content_over_2000_chars(user, post):
    """Model should raise ValidationError if comment exceeds 2000 chars"""
    long_content = "x" * 2001
    comment = Comment(post=post, author=user, content=long_content)
    with pytest.raises(ValidationError) as excinfo:
        comment.save()


# ---------------- LIKE MODEL TESTS ----------------

@pytest.mark.django_db
def test_like_creation(post, user):
    """ User can like a post """
    like = Like.objects.create(post=post, user=user)
    assert str(like) == f"{user} liked {post}"

@pytest.mark.django_db
def test_like_unique_constraint(post, user):
    """ User cannot like the same post twice """
    Like.objects.create(post=post, user=user)
    with pytest.raises(IntegrityError):
        Like.objects.create(post=post, user=user)
