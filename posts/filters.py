"""
Filtering logic for Post querysets

It applies filters based on query parameters:
- Author name 
- Post title 
- Post content 
- Date range
- General search 
"""

from django.db.models import Q
from datetime import datetime, timedelta
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Case, When, IntegerField

def filter_posts(queryset, params):
    """ Applies filtering logic """

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
        # Vector search on title + content
        search_vector = SearchVector("title", "content")
        search_query = SearchQuery(content_query)
        vector_qs = (
            queryset.annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gte=0.05)
            .order_by("-rank", "-created_at")
        )
        # Fallback: if no vector results, use basic icontains
        if vector_qs.exists():
            queryset = vector_qs
        else:
            queryset = queryset.filter(
                Q(title__icontains=content_query) |
                Q(content__icontains=content_query)
            )


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
        search_vector = SearchVector("title", "content")
        search_query = SearchQuery(general_query)
        vector_qs = (
            queryset.annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gte=0.05)
            .order_by("-rank", "-created_at")
        )

        if vector_qs.exists():
            queryset = vector_qs
        else:
            # fallback includes author name fields too
            queryset = queryset.filter(
                Q(title__icontains=general_query) |
                Q(content__icontains=general_query) |
                Q(author__username__icontains=general_query) |
                Q(author__first_name__icontains=general_query) |
                Q(author__last_name__icontains=general_query)
            )


    return queryset
