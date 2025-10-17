"""
Utility helpers for the posts app

Includes:
- Asynchronous email notifications for comments and replies

This module centralizes logic that may be shared across multiple views
"""

import re
from django.contrib.auth import get_user_model
from posts.tasks import send_email_task

User = get_user_model()

def extract_tagged_users(content):
    """
    Extract valid tagged users from comment content
    """
    usernames = re.findall(r'@([\w.\-]+)', content)
    return list(User.objects.filter(username__in=usernames))


def notify_comment_emails(comment, post, user):
    """
    Send async email notifications when a comment is added
    Handles:
      - Post author notifications for top-level comments
      - Replied-to user notifications
      - @tagged user notifications
    """
    # Notify post author ONLY for top-level comments
    if not comment.parent and post.author.email and post.author != user:
        subject = f"New comment on your post '{post.title}'"
        message = f"{user.username} commented: {comment.content}"
        send_email_task.delay(subject, message, [post.author.email])

    # Notify replied-to user
    if comment.replied_to and comment.replied_to.email and comment.replied_to != user:
        subject = f"New reply to your comment on '{post.title}'"
        message = f"{user.username} replied: {comment.content}"
        send_email_task.delay(subject, message, [comment.replied_to.email])

    # Notify @tagged users
    tagged_users = extract_tagged_users(comment.content)
    for tagged_user in tagged_users:
        # Avoid duplicate email if already notified
        if tagged_user not in [user, post.author, comment.replied_to] and tagged_user.email:
            subject = f"You were mentioned in a comment on '{post.title}'"
            message = f"{user.username} mentioned you in a comment: {comment.content}"
            send_email_task.delay(subject, message, [tagged_user.email])
