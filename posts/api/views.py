from rest_framework import generics, status
from posts.models import Post, Comment, Like
from posts.serializers import PostSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404


# -----------------------POSTS-----------------------

# List all posts (read-only for unauthenticated users)
class PostListAPIView(generics.ListAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# Retrieve a single post (read-only for unauthenticated users)
class PostDetailAPIView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# Create a new post (authenticated users only)
class PostCreateAPIView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

# Update a post (only by author)
class PostUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

# Delete a post (only by author)
class PostDeleteAPIView(generics.DestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"detail": "Post deleted successfully."}, status=status.HTTP_200_OK)



# -----------------------COMMENTS-----------------------

# Add a comment (authenticated users only)
class CommentCreateAPIView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post_pk = self.kwargs.get("post_pk")
        post = get_object_or_404(Post, pk=post_pk)

        parent_raw = self.request.data.get("parent") or self.request.data.get("parent_id")
        root_parent = None
        replied_to_user = None

        if parent_raw:
            try:
                parent_id = int(parent_raw)
            except (TypeError, ValueError):
                parent_id = None

            if parent_id:
                # original_parent is the comment the user clicked "Reply" on
                original_parent = Comment.objects.filter(pk=parent_id, post=post).first()
                if original_parent:
                    # replied_to should be the author of the comment being replied to
                    replied_to_user = original_parent.author
                    # root_parent must be the top-level comment for two-level structure
                    root_parent = original_parent.parent or original_parent

        comment = serializer.save(
            post=post,
            author=self.request.user,
            parent=root_parent,
            replied_to=replied_to_user,
        )

        # Add autotagging text if replying to someone
        if comment.replied_to:
            tag = f"@{comment.replied_to.username}"
            if not comment.content.strip().startswith(tag):
                comment.content = f"{tag} {comment.content}"
                comment.save(update_fields=["content"])

# Update a comment (only by author)
class CommentUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "detail": "Comment updated successfully.",
            "comment": serializer.data
        }, status=status.HTTP_200_OK)

# Delete a comment (only by author)
class CommentDeleteAPIView(generics.DestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        self.perform_destroy(comment)
        return Response({"detail": "Comment deleted successfully."}, status=status.HTTP_200_OK)



# -----------------------LIKES-----------------------

# Toggle like/unlike on a post (authenticated users only)
class ToggleLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_pk, format=None):
        post = get_object_or_404(Post, pk=post_pk)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        return Response({
            "liked": liked,
            "like_count": post.likes.count()
        }, status=status.HTTP_200_OK)
