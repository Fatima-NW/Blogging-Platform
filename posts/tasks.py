"""
Asynchronous tasks for the posts app

Includes tasks for:
- Sending emails
- Allowing users to download pdfs of posts
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from posts.models import Post

@shared_task
def send_email_task(subject, message, recipient_list):
    """ Asynchronous task to send emails """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )

@shared_task
def generate_post_pdf_task(post_id):
    """ Asynchronous task to generate a PDF for a post """
    from posts.utils import generate_post_pdf
    
    post = Post.objects.get(pk=post_id)
    pdf_path = generate_post_pdf(post)
    return pdf_path
