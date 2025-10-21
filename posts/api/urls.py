"""
URL routing for posts app (API endpoints)

Includes routes for:
- Creating, viewing, updating, deleting, downloading posts
- Adding, updating and deleting comments
- Liking/unliking posts
"""

from django.urls import path
from .views import ( PostListAPIView, PostDetailAPIView,
    PostCreateAPIView, PostUpdateAPIView, PostDeleteAPIView, PostGeneratePDFAPIView,
    CommentCreateAPIView, CommentUpdateAPIView, CommentDeleteAPIView,
    ToggleLikeAPIView,
)

urlpatterns = [
    # posts
    path("posts/", PostListAPIView.as_view(), name="api_post_list"),
    path("posts/<int:pk>/", PostDetailAPIView.as_view(), name="api_post_detail"),
    path("posts/create/", PostCreateAPIView.as_view(), name="api_post_create"),
    path("posts/<int:pk>/update/", PostUpdateAPIView.as_view(), name="api_post_update"),
    path("posts/<int:pk>/delete/", PostDeleteAPIView.as_view(), name="api_post_delete"),
    path("posts/<int:post_pk>/generate-pdf/", PostGeneratePDFAPIView.as_view(),name="api_post_generate_pdf"),

    # comments
    path("posts/<int:post_pk>/comment/", CommentCreateAPIView.as_view(), name="api_comment_create"),
    path("comments/<int:pk>/update/", CommentUpdateAPIView.as_view(), name="api_comment_update"),
    path("comments/<int:pk>/delete/", CommentDeleteAPIView.as_view(), name="api_comment_delete"),

    # likes
    path("posts/<int:post_pk>/like/", ToggleLikeAPIView.as_view(), name="api_toggle_like"),
]