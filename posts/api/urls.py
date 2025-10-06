from django.urls import path
from .views import PostListAPIView, PostDetailAPIView

urlpatterns = [
    path("posts/", PostListAPIView.as_view(), name="api_post_list"),
    path("posts/<int:pk>/", PostDetailAPIView.as_view(), name="api_post_detail"),
]
