"""
Asynchronous tasks for the posts app

Includes tasks for:
- Sending emails 
- Generating PDFs of posts and emailing download links
- Cleaning up temporary PDF files
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from posts.models import Post
from django.urls import reverse
from posts.utils import generate_post_pdf_bytes, save_pdf_bytes_temp
from pathlib import Path
from datetime import timedelta, datetime
from django.utils import timezone

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
def generate_post_pdf_task_and_email(post_id, recipient_email):
    """
    Celery task that:
    - Generates PDF of a post
    - Saves it temporarily
    - Emails a download link to the user
    """
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return None
    
    # Generate pdf bytes
    pdf_bytes = generate_post_pdf_bytes(post)

    # Save to temporary folder and get uid
    uid, file_path = save_pdf_bytes_temp(pdf_bytes, filename=f"{post.slug if hasattr(post,'slug') else post.pk}.pdf")
    
    # Build download URL and email
    download_path = reverse("download_generated_pdf", args=[uid])
    download_url = f"{settings.SITE_URL}{download_path}"
    expiry_minutes = getattr(settings, "PDF_LINK_EXPIRY_MINUTES", 15)

    subject = f"Your PDF for '{post.title}' is ready"
    message = (
        f"Hi,\n\nYour PDF for post \"{post.title}\" is ready for download.\n"
        f"Download it using this one-time link:\n{download_url}\n\n"
        f"⚠️ Please note:\n"
        f"- The link will automatically expire after {expiry_minutes} minutes.\n"
        f"- The file will be deleted after it is downloaded once.\n\n"
    )
    send_email_task(subject, message, [recipient_email])

    return {"uid": uid, "path": file_path}


@shared_task
def cleanup_old_temp_pdfs(max_age_minutes=None):
    """
    Delete temporary PDF files older than 'max_age_minutes'.
    """
    max_age_minutes = max_age_minutes or getattr(settings, "PDF_LINK_EXPIRY_MINUTES", 15)
    folder = getattr(settings, "PDFS_TEMP_ROOT")
    cutoff = timezone.now() - timedelta(minutes=max_age_minutes)
    for p in Path(folder).glob("*.pdf"):
        try:
            mtime = timezone.make_aware(
                datetime.fromtimestamp(p.stat().st_mtime),
                timezone.get_default_timezone()
            )
            print(f"Checking {p}: mtime={mtime}, cutoff={cutoff}")
            if mtime < cutoff:
                p.unlink()
                print(f"Deleted {p}")
        except Exception as e:
            print(f"Error deleting {p}: {e}")

