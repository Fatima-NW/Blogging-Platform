from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm
from django.urls import reverse_lazy
from django.http import JsonResponse

class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    ordering = ["-created_at"]  # newest first

class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # comments
        context["comments"] = post.comments.filter(parent__isnull=True).order_by("-created_at")
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
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"
    success_url = reverse_lazy("post_list")

    def form_valid(self, form):
        # attach logged-in user as the author
        form.instance.author = self.request.user
        return super().form_valid(form)
    
class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"
    success_url = reverse_lazy("post_list")

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if post.author != self.request.user:
            raise PermissionDenied("You are not allowed to edit this post.")
        return post

@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user

            parent_id = request.POST.get("parent_id")
            if parent_id:
                parent = Comment.objects.filter(id=parent_id, post=post).first()
                if parent:
                    # If parent itself has a parent it means it is a reply, so keep the root parent
                    if parent.parent:
                        comment.parent = parent.parent   # root comment
                        comment.replied_to = parent.author
                    else:
                        comment.parent = parent          # top-level comment
                        comment.replied_to = parent.author

            comment.save()
    return redirect("post_detail", pk=post.pk)

@login_required
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "liked": liked,
            "like_count": post.likes.count()
        })

    return redirect("post_detail", pk=post.pk)
