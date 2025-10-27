"""
Utility helpers for the posts app

Includes:
- Asynchronous email notifications for comments and replies
- Post downloads

This module centralizes logic that may be shared across multiple views
"""

import re
from django.contrib.auth import get_user_model
from weasyprint import HTML
from django.conf import settings
import os
import uuid
from io import BytesIO
import tempfile
from django.utils.text import slugify


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
    from posts.tasks import send_email_task

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


def generate_post_pdf_bytes(post):
    """
    Generate a PDF of a post and return it as bytes
    """
    from django.template.loader import render_to_string
    from django.utils import timezone
    from django.conf import settings

    html_content = render_to_string("posts/post_pdf.html", {
        "post": post,
        "generation_date": timezone.localtime(timezone.now()),
        "site_name": getattr(settings, "SITE_NAME", "Fatima's Blog"),
    })
    pdf_io = BytesIO()
    HTML(string=html_content, base_url=settings.BASE_DIR).write_pdf(pdf_io)
    return pdf_io.getvalue()


def save_pdf_bytes_temp(pdf_bytes, filename: str | None = None):
    """
    Save PDF bytes to a temporary file PDFs
    """
    pdfs_dir = getattr(settings, "PDFS_TEMP_ROOT", None)
    if not pdfs_dir:
        pdfs_dir = os.path.join(settings.BASE_DIR, "PDFs")

    os.makedirs(pdfs_dir, exist_ok=True)

    uid = uuid.uuid4().hex
    stored_name = f"{uid}.pdf"
    file_path = os.path.join(pdfs_dir, stored_name)

    # write bytes to the file
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
        f.flush()

    # return uid (for download link) and actual path on disk
    return uid, file_path
