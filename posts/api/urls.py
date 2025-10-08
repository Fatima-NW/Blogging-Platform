from django.urls import path
from .views import ( PostListAPIView, PostDetailAPIView,
    PostCreateAPIView, PostUpdateAPIView, PostDeleteAPIView,
    CommentCreateAPIView, CommentDeleteAPIView,
    ToggleLikeAPIView,
)

urlpatterns = [
    # posts
    path("posts/", PostListAPIView.as_view(), name="api_post_list"),
    path("posts/<int:pk>/", PostDetailAPIView.as_view(), name="api_post_detail"),
    path("posts/create/", PostCreateAPIView.as_view(), name="api_post_create"),
    path("posts/<int:pk>/update/", PostUpdateAPIView.as_view(), name="api_post_update"),
    path("posts/<int:pk>/delete/", PostDeleteAPIView.as_view(), name="api_post_delete"),

    # comments
    path("posts/<int:post_pk>/comment/", CommentCreateAPIView.as_view(), name="api_comment_create"),
    path("comments/<int:pk>/delete/", CommentDeleteAPIView.as_view(), name="api_comment_delete"),

    # likes
    path("posts/<int:post_pk>/like/", ToggleLikeAPIView.as_view(), name="api_toggle_like"),
]