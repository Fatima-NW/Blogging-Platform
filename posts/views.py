"""
Template views for the posts app

Includes views for:
- Posts: view, create, update, delete, download
- Comments: create, update, delete
- Likes: toggle like/unlike on a post
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.shortcuts import render
from django.conf import settings
from .filters import filter_posts
from .utils import notify_comment_emails, generate_post_pdf_bytes
from .tasks import generate_post_pdf_task_and_email
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from django.contrib import messages
import os
from wsgiref.util import FileWrapper
from mylogger import Logger

logger = Logger()


# -----------------------POSTS-----------------------

class PostListView(ListView):
    """ Displays all posts """
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    ordering = ["-created_at"]
    paginate_by = settings.PAGINATE_BY   # pagination

    def get_queryset(self):
        """ Returns filtered queryset based on query parameters """
        queryset = super().get_queryset()
        queryset = filter_posts(queryset, self.request.GET)
        logger.debug(f"Query params received: {self.request.GET.dict()}")
        logger.info(f"User {self.request.user} fetched post list")
        return queryset
    

class PostDetailView(DetailView):
    """ Displays a single post along with comments and like info """
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = (
            Post.objects
            .select_related("author")    # join post author
            .prefetch_related(
                "comments__author",               # prefetch top-level comment authors
                "comments__replied_to",           # prefetch replied-to users
                "comments__replies__author",      # prefetch nested reply authors
                "comments__replies__replied_to",  # prefetch nested reply replied-to
                "likes__user"                     # prefetch users who liked the post
            )
            .get(pk=self.object.pk)
        )

        # Top-level comments: newest to oldest
        top_comments = post.comments.filter(parent__isnull=True).order_by("-created_at")
        # Prefetch nested replies: oldest to newest
        for comment in top_comments:
            comment.replies_ordered = comment.replies.all().order_by("created_at")

        context["comments"] = top_comments
        context["comment_form"] = CommentForm()
        context["comment_count"] = post.comments.count()

        # likes
        context["like_count"] = post.likes.count()
        context["user_has_liked"] = (
            self.request.user.is_authenticated
            and post.likes.filter(user=self.request.user).exists()
        )
        logger.info(f"User {self.request.user} viewed post {self.object.pk}")
        logger.debug(f"Prefetched data for post {post.pk} (comments={post.comments.count()}, likes={post.likes.count()})")
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """ Allow logged-in users to create posts """
    model = Post
    form_class = PostForm
    template_name = "posts/post_creation_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user    # attach logged-in user as the author
        logger.info(f"User {self.request.user} created a new post")
        messages.success(self.request, "Post created successfully!")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        content_errors = form.errors.get("content", [])
        if any("at most 10000" in str(e) for e in content_errors):
            logger.debug(f"User {self.request.user} attempted to create post exceeding 10,000 chars")
            logger.warning(f"User {self.request.user} failed to create post due to content length")
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy("post_detail", kwargs={"pk": self.object.pk})
    

class PostUpdateView(LoginRequiredMixin, UpdateView):
    """ Allow users to edit their own posts """
    model = Post
    form_class = PostForm
    template_name = "posts/post_creation_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        return context

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if post.author != self.request.user:         # only author can edit
            logger.warning(f"User {self.request.user} tried to edit post {post.pk} without permission")
            raise PermissionDenied("You are not allowed to edit this post.")
        logger.info(f"User {self.request.user} accessed post {post.pk} for editing")
        return post
    
    def form_valid(self, form):
        response = super().form_valid(form)
        logger.debug(f"Post {form.instance.pk} updated fields: {form.changed_data}")
        logger.info(f"User {self.request.user} successfully updated post {form.instance.pk}")
        messages.success(self.request, "Post updated successfully!")
        return response
    
    def form_invalid(self, form):
        content_errors = form.errors.get("content", [])
        if any("at most 10000" in str(e) for e in content_errors):
            logger.debug(f"User {self.request.user} attempted to update post exceeding 10,000 chars")
            logger.warning(f"User {self.request.user} failed to update post due to content length")
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy("post_detail", kwargs={"pk": self.object.pk})
    

class PostDeleteView(LoginRequiredMixin, DeleteView):
    """ Allow users to delete their own posts """
    model = Post
    template_name = "posts/post_confirm_delete.html"
    success_url = reverse_lazy("post_list")

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if post.author != self.request.user:         # only author can delete
            logger.warning(f"User {self.request.user} tried to delete post {post.pk} without permission")
            raise PermissionDenied("You are not allowed to delete this post.")
        logger.info(f"User {self.request.user} accessed post {post.pk} for deletion")
        return post


@login_required
@logger.log_execution(level="DEBUG") 
def generate_pdf(request, pk):
    """
    Allow logged-in users to generate PDFs of posts

    Hybrid behavior:
    - If synchronous generation finishes within PDF_SYNC_TIMEOUT_SECONDS, return the PDF in the response
    - Otherwise, dispatch Celery task to generate PDF and email it to the user
    """
    post = get_object_or_404(Post, pk=pk)
    timeout = getattr(settings, "PDF_SYNC_TIMEOUT_SECONDS", 2)
    logger.info(f"User {request.user} requested PDF for post {pk}")

    # Run generation in thread and wait with timeout
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(generate_post_pdf_bytes, post)
        try:
            pdf_bytes = future.result(timeout=timeout)
            # Return as downloadable pdf to browser if completed within timeout
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            filename = f"{post.title}.pdf"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            logger.info(f"PDF generated for post {pk} by {request.user}")
            return response

        except TimeoutError:
            # Dispatch background Celery task if takes too long
            recipient_email = request.user.email
            generate_post_pdf_task_and_email.delay(post.pk, recipient_email)
            logger.warning(f"PDF generation timed out for post {pk}")
            logger.info(f"Dispatched background Celery task for {request.user}. User will receive an email with the download link once ready.")
            messages.info(request, "PDF is being generated in the background. We will email you a link when it's ready.")
            return redirect("post_detail", pk=pk)
       

def download_generated_pdf(request, uid):
    """
    Serve a generated PDF saved temporarily in the project under PDFs
    After serving, delete the file to avoid storage buildup
    """
    pdfs_dir = getattr(settings, "PDFS_TEMP_ROOT")
    file_path = os.path.join(pdfs_dir, f"{uid}.pdf")
    template_name = "posts/pdf_expired.html"

    if not os.path.exists(file_path):
        expiry_minutes = getattr(settings, "PDF_LINK_EXPIRY_MINUTES", 15)
        logger.warning(f"User {request.user} tried to download missing or expired PDF {uid}")
        context = {"expiry_minutes": expiry_minutes}
        return render(request, template_name, context, status=410)

    # Stream file to user
    f = open(file_path, "rb")
    response = FileResponse(f, as_attachment=True, filename=f"{uid}.pdf")

    # Only delete when the response is closed
    original_close = response.close
    def cleanup():
        try:
            original_close()
        finally:
            try:
                os.remove(file_path)
                logger.info(f"User {request.user} downloaded and removed PDF {uid}")
            except Exception as e:
                logger.warning(f"Failed to delete PDF {uid}: {e}")
    response.close = cleanup
    return response


# -----------------------COMMENTS-----------------------

@login_required
def add_comment(request, pk):
    """ 
    Allow logged-in users to add a comment 
    
    Supports a two-level structure:
    - Top-level comments are direct responses to the post.
    - Replies are nested under the top-level comment (the parent),
      but tagged to the specific user being replied to via `replied_to`.
    """
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user

            parent_id = request.POST.get("parent_id")
            if parent_id:
                parent_comment = Comment.objects.filter(id=parent_id, post=post).first()
                if parent_comment:
                    comment.parent = parent_comment.parent or parent_comment # Attach to root comment (two-level nesting)
                    comment.replied_to = parent_comment.author               # Tag the user being replied to

            comment.save()

            # Send async email notifications
            notify_comment_emails(comment, post, request.user)
            logger.info(f"User {request.user} added comment {comment.pk} to post {pk}")
            messages.success(request, "Comment added successfully!")
        else:
            if "content" in form.errors:
                content_errors = form.errors.get("content")
                if any("at most 1000 characters" in err for err in content_errors):
                    logger.debug(f"User {request.user} attempted to submit a comment exceeding 1000 chars on post {pk}")
            logger.warning(f"User {request.user} failed to add comment to post {pk}")

    return redirect("post_detail", pk=post.pk)


@login_required
def update_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if request.user != comment.author:                # only author can update
        logger.warning(f"Unauthorized update attempt by {request.user} on comment {pk}")
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        new_content = request.POST.get("content", "").strip()
        if not new_content:
            logger.warning(f"User {request.user} submitted empty content for comment {pk}")
            return JsonResponse({"success": False, "error": "Empty content."}, status=400)

        if len(new_content) > 1000:
            logger.debug(f"User {request.user} attempted to update comment {pk} exceeding 1000 chars")
            logger.warning(f"User {request.user} failed to update comment {pk}")
            return JsonResponse({"success": False, "error": "Comment too long (max 1000 characters)."}, status=400)

        comment.content = new_content
        comment.save()
        logger.info(f"User {request.user} updated comment {pk}")
        return JsonResponse({"success": True, "updated_content": comment.content})

    logger.warning(f"Invalid request for updating comment {pk} by {request.user}")
    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)


@login_required
def delete_comment(request, pk):
    """ Allow users to delete their own comments """
    comment = get_object_or_404(Comment, pk=pk)
    if request.user == comment.author:                 # only author can delete
        comment.delete()
        messages.success(request, "Comment deleted successfully!")
        logger.info(f"User {request.user} deleted comment {pk}")
    else:
        messages.error(request, "You are not allowed to delete this comment.")
        logger.warning(f"Unauthorized delete attempt by {request.user} on comment {pk}")
    return redirect("post_detail", pk=comment.post.pk)


# -----------------------LIKES-----------------------

@login_required
def toggle_like(request, pk):
    """ Allow logged-in users to like/unlike a post """
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()          # user already liked -> unlike
        liked = False
        logger.info(f"User {request.user} unliked post {pk}")
    else:
        liked = True
        logger.info(f"User {request.user} liked post {pk}")

    logger.debug(f"Post {pk} now has {post.likes.count()} likes after {request.user}'s action")

    #  Return JSON for AJAX requests
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "liked": liked,
            "like_count": post.likes.count()
        })
    
    return redirect("post_detail", pk=post.pk)
