from django.urls import path
from .views import PostListView, PostDetailView, PostCreateView, PostUpdateView, PostDeleteView, add_comment, delete_comment, toggle_like

urlpatterns = [
    path("", PostListView.as_view(), name="post_list"),
    path("<int:pk>/", PostDetailView.as_view(), name="post_detail"),
    path("new/", PostCreateView.as_view(), name="post_create"),
    path("<int:pk>/edit/", PostUpdateView.as_view(), name="post_edit"),
    path("<int:pk>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("<int:pk>/comment/", add_comment, name="add_comment"),
    path("comment/<int:pk>/delete/", delete_comment, name="delete_comment"),
    path("<int:pk>/like/", toggle_like, name="toggle_like"),
]
