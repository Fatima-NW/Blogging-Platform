"""
Utility helpers for the posts app

Includes:
- Asynchronous email notifications for comments and replies

This module centralizes logic that may be shared across multiple views
"""


from posts.tasks import send_email_task

def notify_comment_emails(comment, post, user):
    """
    Send async email notifications when a comment is added.
    Ensures consistent behavior for both API and template views.
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
