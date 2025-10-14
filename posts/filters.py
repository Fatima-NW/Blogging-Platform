"""
Filtering logic for Post querysets

It applies filters based on query parameters:
- Author name (supports partial matches in username, first name, or last name)
- Post title (case-insensitive partial match)
- Post content (case-insensitive partial match)
- Creation date (specific date or within a range)
"""

from django.db.models import Q
from datetime import datetime, timedelta

def filter_posts(queryset, params):
    """ Applies filtering logic """

    author_name = params.get("author", "").strip()
    title_query = params.get("title", "").strip()
    content_query = params.get("content", "").strip()
    created_after = params.get("created_after", "").strip()
    created_before = params.get("created_before", "").strip()
    created_on = params.get("created_on", "").strip()

    # Filter by author name (partial match, case-insensitive)
    if author_name:
        queryset = queryset.filter(
            Q(author__username__istartswith=author_name)
            | Q(author__first_name__istartswith=author_name)
            | Q(author__last_name__istartswith=author_name)
        )

    # Filter by title (case-insensitive partial match)
    if title_query:
        if len(title_query) == 1:
            queryset = queryset.filter(title__istartswith=title_query)
        else:
            queryset = queryset.filter(title__icontains=title_query)


    # Filter by content (case-insensitive partial match)
    if content_query:
        queryset = queryset.filter(content__icontains=content_query)

    # Exact date filter
    if created_on:
        queryset = queryset.filter(created_at__date=created_on)

    # Filter by date range
    elif created_after and created_before:
        end_date = datetime.strptime(created_before, "%Y-%m-%d") + timedelta(days=1)
        queryset = queryset.filter(created_at__gte=created_after, created_at__lt=end_date)
    elif created_after:
        queryset = queryset.filter(created_at__gte=created_after)
    elif created_before:
        end_date = datetime.strptime(created_before, "%Y-%m-%d") + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_date)

    return queryset
