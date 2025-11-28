"""
Utility helpers for the posts app

Includes:
- Post queryset filters
- In-app and asynchronous email notifications for comments, mentions and replies
- Post PDF generation and temporary storage
- @username to profile linking

This module centralizes logic that may be shared across multiple views
"""

from django.db.models import Q
from datetime import datetime, timedelta
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Case, When, IntegerField
import re
from django.contrib.auth import get_user_model
from weasyprint import HTML
from django.conf import settings
import os
import uuid
from io import BytesIO
from users.models import Notification


User = get_user_model()



# ----------------------- FILTERS -----------------------

def filter_posts(queryset, params):
    """
    Applies filters to Post querysets based on query parameters.

    Supports:
    - Author name
    - Post title
    - Post content
    - Date range
    - General search across title, content, and author
    """

    author_name = params.get("author", "").strip()
    title_query = params.get("title", "").strip()
    content_query = params.get("content", "").strip()
    start_date = params.get("start_date", "").strip()
    end_date = params.get("end_date", "").strip()
    general_query = params.get("query", "").strip()

    # AUTHOR FILTER (supports case-insensitive partial match)
    if author_name:
        queryset = queryset.filter(
            Q(author__username__istartswith=author_name) | 
            Q(author__first_name__istartswith=author_name) | 
            Q(author__last_name__istartswith=author_name)
        )


    # TITLE FILTER (case-insensitive partial match)
    if title_query:
        if len(title_query) == 1:   
            # only titles that start with that letter                                    
            queryset = queryset.filter(title__istartswith=title_query)  
        else:
            queryset = (
                queryset
                .filter(title__icontains=title_query)  
                .annotate(
                    _title_priority=Case(
                        When(title__istartswith=title_query, then=0),
                        default=1,
                        output_field=IntegerField(),
                    )
                )
                # titles that start with those letters first, then all titles that contains those letters
                .order_by("_title_priority", "-created_at")  
            )


    # CONTENT FILTER (Vector search + fallback)  
    if content_query:
        # Vector search
        search_vector = SearchVector("title", "content")
        search_query = SearchQuery(content_query)
        vector_qs = queryset.annotate(rank=SearchRank(search_vector, search_query)).filter(rank__gte=0.05)

        # Always combine with icontains
        icontains_qs = queryset.filter(
            Q(title__icontains=content_query) |
            Q(content__icontains=content_query)
        )
        queryset = (vector_qs | icontains_qs).distinct().order_by('-created_at')


    # DATE RANGE FILTER (Inclusive)
    if start_date and end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        queryset = queryset.filter(created_at__gte=start_date, created_at__lt=end_dt)
    elif start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    elif end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_dt)


    # GENERAL SEARCH (across title, content, and author)
    if general_query:
        # Vector search
        search_vector = SearchVector("title", "content")
        search_query = SearchQuery(general_query)
        vector_qs = queryset.annotate(rank=SearchRank(search_vector, search_query)).filter(rank__gte=0.05)
        
        # Always combine with icontains
        icontains_qs = queryset.filter(
            Q(title__icontains=general_query) |
            Q(content__icontains=general_query) |
            Q(author__username__icontains=general_query) |
            Q(author__first_name__icontains=general_query) |
            Q(author__last_name__icontains=general_query)
        )
        queryset = (vector_qs | icontains_qs).distinct().order_by('-created_at')

    return queryset



# ----------------------- TAGGED USER RENDERING -----------------------

def linkify_tagged_users(content):
    """
    Convert @username in content to <a> links to their profiles
    """
    if not content:
        return ""

    def replacer(match):
        username = match.group(1)
        url = f"/users/profile/{username}/"
        return f'<a href="{url}" class="text-decoration-none text-muted profile-link">@{username}</a>'

    return re.sub(r'@([\w.\-]+)', replacer, content)



# ----------------------- NOTIFICATIONS -----------------------

def notify_comment(comment, post, user, new_content: str | None = None, is_new_comment: bool = False, old_content: str = ""):
    """
    - Send in-app notifications
    - Send async email notifications
        Handles:
        - Post author notifications for top-level comments
        - Replied-to user notifications
        - @tagged user notifications
    """
    from posts.tasks import send_email_task

    content_to_check = new_content if new_content is not None else comment.content

    # Notify post author ONLY for top-level comments
    if is_new_comment and not comment.parent and post.author.email and post.author != user:
        Notification.objects.create(
            user=post.author,
            message=f"{user.username} commented on your post '{post.title}'",
            post=post,
            comment=comment
        )
        subject = f"New comment on your post '{post.title}'"
        message = f"{user.username} commented on your post '{post.title}':  {content_to_check}"
        send_email_task.delay(subject, message, [post.author.email])

    # Notify replied-to user
    if is_new_comment and comment.replied_to and comment.replied_to.email and comment.replied_to != user:
        Notification.objects.create(
            user=comment.replied_to,
            message=f"{user.username} replied to your comment on '{post.title}'",
            post=post,
            comment=comment
        )
        subject = f"New reply to your comment on '{post.title}'"
        message = f"{user.username} replied to your comment on '{post.title}': {content_to_check}"
        send_email_task.delay(subject, message, [comment.replied_to.email])

    # Notify @tagged users
    old_tags = set(re.findall(r'@([\w.\-]+)', old_content))
    new_tags = set(re.findall(r'@([\w.\-]+)', content_to_check))
    for username in new_tags - old_tags:
        tagged_user = User.objects.filter(username=username).first()
        if tagged_user not in [user, post.author, comment.replied_to] and tagged_user.email:
            Notification.objects.create(
                user=tagged_user,
                message=f"{user.username} mentioned you in a comment on '{post.title}'",
                post=post,
                comment=comment
            )
            subject = f"You were mentioned in a comment on '{post.title}'"
            message = f"{user.username} mentioned you in a comment on '{post.title}': {content_to_check}"
            send_email_task.delay(subject, message, [tagged_user.email])



# ----------------------- PDFS -----------------------

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
        "site_name": getattr(settings, "SITE_NAME"),
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
