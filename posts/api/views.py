"""
API views for the posts app

Includes endpoints for:
- Posts: list, detail, create, update, delete
- Comments: create, update, delete
- Likes: toggle like/unlike on a post
"""

from rest_framework import generics, status
from posts.models import Post, Comment, Like
from posts.serializers import PostSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from ..filters import filter_posts
from posts.utils import notify_comment_emails, generate_post_pdf_bytes
from posts.tasks import generate_post_pdf_task_and_email
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from mylogger import Logger

logger = Logger()


# -----------------------POSTS-----------------------

class PostListAPIView(generics.ListAPIView):
    """ List all posts (read-only for unauthenticated users) """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_at')
        params = self.request.query_params 
        logger.info(f"User {self.request.user} fetched post list with params: {dict(self.request.query_params)}")
        return filter_posts(queryset, params)


class PostDetailAPIView(generics.RetrieveAPIView):
    """ Retrieve a single post (read-only for unauthenticated users) """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        post = super().get_object()
        logger.info(f"User {self.request.user} viewed post {post.pk}")
        return post
    

class PostCreateAPIView(generics.CreateAPIView):
    """ Create a new post (authenticated users only) """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        logger.info(f"User {self.request.user} created a new post: {serializer.validated_data.get('title')}")


class PostUpdateAPIView(generics.RetrieveUpdateAPIView):
    """ Update an existing post (only by the author) """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.info(f"User {self.request.user} is accessing their posts for update")
        return Post.objects.filter(author=self.request.user)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"User {request.user} is updating post {instance.pk}")
        response = super().update(request, *args, **kwargs)
        logger.success(f"User {request.user} successfully updated post {instance.pk}")
        return response


class PostDeleteAPIView(generics.DestroyAPIView):
    """ Delete a post (only by the author) """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.info(f"User {self.request.user} is accessing posts for deletion")
        return Post.objects.filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"User {request.user} requested to delete post {instance.pk}")
        self.perform_destroy(instance)
        logger.success(f"User {request.user} deleted post {instance.pk}")
        return Response({"detail": "Post deleted successfully."}, status=status.HTTP_200_OK)


class PostGeneratePDFAPIView(APIView):
    """
    VGenerates PDF of a post

    Hybrid behavior:
    - If synchronous generation finishes within PDF_SYNC_TIMEOUT_SECONDS, return the PDF in the response
    - Otherwise, dispatch Celery task to generate PDF and email it to the user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, post_pk, format=None):
        post = get_object_or_404(Post, pk=post_pk)
        timeout = getattr(settings, "PDF_SYNC_TIMEOUT_SECONDS", 2)
        logger.info(f"User {request.user} requested PDF for post {post.pk}")

        # Try synchronous PDF generation first
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(generate_post_pdf_bytes, post)
            try:
                pdf_bytes = future.result(timeout=timeout)
                logger.success(f"PDF for post {post.pk} generated synchronously within {timeout}s")
                filename = f"{post.title}.pdf"
                filename = f"{post.title}.pdf"
                response = HttpResponse(pdf_bytes, content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                return response

            except TimeoutError:
                # Dispatch Celery task if it takes too long
                logger.warning(f"PDF generation for post {post.pk} took longer than {timeout}s, running asynchronously")
                recipient_email = request.user.email
                generate_post_pdf_task_and_email.delay(post.pk, recipient_email)
                return Response({
                    "success": True,
                    "message": "PDF generation is taking longer than expected. "
                               "We will email you a download link when it's ready."
                }, status=202)
    

# -----------------------COMMENTS-----------------------

class CommentCreateAPIView(generics.CreateAPIView):
    """
    Create a new comment or reply (authenticated users only).

    - Supports a two-level structure:
        - Top-level comments are direct responses to the post.
        - Replies are nested under the top-level comment (the parent),
        but tagged to the specific user being replied to.
    - Automatically prepends '@username' to replies.
    - Sends async email notifications to user being replied to.
    """
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
                original_parent = Comment.objects.filter(pk=parent_id, post=post).first() # comment being replied to
                if original_parent:
                    replied_to_user = original_parent.author # user being replied to
                    root_parent = original_parent.parent or original_parent # top-level comment for nesting

        comment = serializer.save(
            post=post,
            author=self.request.user,
            parent=root_parent,
            replied_to=replied_to_user,
        )

        # Add @username when replying to another user
        if comment.replied_to:
            tag = f"@{comment.replied_to.username}"
            if not comment.content.strip().startswith(tag):
                comment.content = f"{tag} {comment.content}"
                comment.save(update_fields=["content"])

        logger.info(f"User {self.request.user} commented on post {post.pk}")
        if replied_to_user:
            logger.info(f"User {self.request.user} replied to {replied_to_user.username} under comment {root_parent.pk if root_parent else 'N/A'}")

        # Send async email notifications
        notify_comment_emails(comment, post, self.request.user)


class CommentUpdateAPIView(generics.RetrieveUpdateAPIView):
    """ Update a comment (only by the author) """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        logger.info(f"User {request.user} is is attempting to update comment {instance.pk}")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.success(f"User {request.user} successfully updated comment {instance.pk}")
        return Response({
            "detail": "Comment updated successfully.",
            "comment": serializer.data
        }, status=status.HTTP_200_OK)


class CommentDeleteAPIView(generics.DestroyAPIView):
    """ Delete a comment (only by the author) """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        logger.info(f"User {request.user} requested to delete comment {comment.pk}")
        self.perform_destroy(comment)
        logger.success(f"User {request.user} deleted comment {comment.pk}")
        return Response({"detail": "Comment deleted successfully."}, status=status.HTTP_200_OK)



# -----------------------LIKES-----------------------

class ToggleLikeAPIView(APIView):
    """ Toggle like/unlike on a post (authenticated users only) """
    permission_classes = [IsAuthenticated]

    def post(self, request, post_pk, format=None):
        post = get_object_or_404(Post, pk=post_pk)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            logger.info(f"User {request.user} unliked post {post.pk}")
            liked = False
        else:
            logger.info(f"User {request.user} liked post {post.pk}")
            liked = True
        return Response({
            "liked": liked,
            "like_count": post.likes.count()
        }, status=status.HTTP_200_OK)
