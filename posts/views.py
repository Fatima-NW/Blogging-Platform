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
from django.http import JsonResponse
from django.conf import settings
from .filters import filter_posts
from posts.utils import notify_comment_emails
from .tasks import generate_post_pdf_task


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
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """ Allow logged-in users to create posts """
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user    # attach logged-in user as the author
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy("post_detail", kwargs={"pk": self.object.pk})
    

class PostUpdateView(LoginRequiredMixin, UpdateView):
    """ Allow users to edit their own posts """
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if post.author != self.request.user:         # only author can edit
            raise PermissionDenied("You are not allowed to edit this post.")
        return post
    
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
            raise PermissionDenied("You are not allowed to delete this post.")
        return post


@login_required
def generate_pdf(request, pk):
    """ Generate PDF of a post """
    post = get_object_or_404(Post, pk=pk)
    generate_post_pdf_task.delay(post.pk)
    return redirect("post_detail", pk=pk)


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

        return redirect("post_detail", pk=post.pk)


@login_required
def update_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if request.user != comment.author:                # only author can update
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        new_content = request.POST.get("content", "").strip()
        if not new_content:
            return JsonResponse({"success": False, "error": "Empty content."}, status=400)

        comment.content = new_content
        comment.save()
        return JsonResponse({"success": True, "updated_content": comment.content})

    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)


@login_required
def delete_comment(request, pk):
    """ Allow users to delete their own comments """
    comment = get_object_or_404(Comment, pk=pk)
    if request.user == comment.author:                 # only author can delete
        comment.delete()
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
    else:
        liked = True

    #  Return JSON for AJAX requests
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "liked": liked,
            "like_count": post.likes.count()
        })

    return redirect("post_detail", pk=post.pk)
