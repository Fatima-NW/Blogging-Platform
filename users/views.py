"""
Template-based views for the users app

Includes views for:
- User registration
- Login 
- Logout 
- Home page
- User profile: view, edit, delete
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from .forms import CustomUserCreationForm, ProfileForm
from .models import CustomUser
from posts.filters import filter_posts
from posts.models import Post, Comment, Like 
from mylogger import Logger

logger = Logger()

def register_view(request):
    """ Display and process the user registration form """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"New user registered: {user.username}")
            messages.success(request, "Registration successful! You can now log in.")
            return redirect("login")  
        else:
            logger.warning(f"Failed registration attempt: {form.errors.as_json()}")
    else:
        form = CustomUserCreationForm()
        logger.info(f"User accessed registration page")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """ Authenticate and log in a user using the login form """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"User {user.username} logged in")
            return redirect("post_list")
        else:
            logger.warning(f"Failed login attempt for username {request.POST.get('username')}")
    else:
        form = AuthenticationForm()
        logger.info(f"User accessed login page")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    """ Log out the current user and redirect to the homepage """
    username = request.user.username if request.user.is_authenticated else "AnonymousUser"
    logout(request)
    logger.info(f"User {username} logged out")
    messages.info(request, "User logged out")
    return redirect("home")  


def home(request):
    """ Render the home page """
    username = request.user.username if request.user.is_authenticated else "AnonymousUser"
    logger.info(f"{username} accessed home page ")
    return render(request, "home.html")


@login_required
def profile_view(request, username):
    """ Display a user's profile """
    profile_user = get_object_or_404(CustomUser, username=username)
    posts = profile_user.post_set.all().order_by('-created_at')
    posts = filter_posts(posts, request.GET)
    logger.info(f"{request.user} viewed profile of {profile_user.username}")
    return render(request, "users/profile.html", {"profile_user": profile_user, "posts": posts})


@login_required
def profile_edit(request, username):
    """ Allow a user to edit their own profile """
    profile_user = get_object_or_404(CustomUser, username=username)

    if request.user != profile_user:
        logger.warning(f"{request.user} attempted to edit {profile_user.username}'s profile")
        messages.warning(request, f"You are not allowed to edit {profile_user.username}'s profile.")
        return redirect("profile", username=profile_user.username)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile_user)
        if form.is_valid():
            form.save()
            logger.info(f"{request.user} updated their profile")
            messages.success(request, "Profile updated successfully!")
            return redirect("profile", username=profile_user.username)
        else:
            logger.warning(f"{request.user} tried submitting invalid profile form")
    else:
        form = ProfileForm(instance=profile_user)
        logger.info(f"{request.user} accessed profile edit page.")

    return render(request, "users/profile_edit.html", {
        "form": form,
        "profile_user": profile_user
    })


@login_required
def profile_delete(request):
    """ Confirmation page for deleting account """
    current_user = request.user

    # Post count
    user_posts = Post.objects.filter(author=current_user)
    post_count = user_posts.count()

    # Comment count
    post_ids = user_posts.values_list("id", flat=True)
    comments_on_posts = Comment.objects.filter(post__in=post_ids).values_list("id", flat=True)
    top_ids = Comment.objects.filter(author=current_user, parent__isnull=True).values_list("id", flat=True)
    replies_to_top = Comment.objects.filter(parent__in=top_ids).values_list("id", flat=True)
    replies_by_user = Comment.objects.filter(author=current_user, parent__isnull=False).values_list("id", flat=True)
    comment_ids = set(
        list(comments_on_posts) + list(top_ids) + list(replies_to_top) + list(replies_by_user)
    )
    total_comments = len(comment_ids)

    # Like count
    likes_on_user_posts = Like.objects.filter(post__in=user_posts).count()
    likes_by_user = Like.objects.filter(user=current_user).exclude(post__in=user_posts).count()
    total_likes = likes_on_user_posts + likes_by_user

    context = {
        "user": current_user,
        "post_count": post_count,
        "total_likes": total_likes,
        "total_comments": total_comments,
    }

    if request.method == "POST":
        logout(request)
        current_user.delete()
        messages.success(request, "Account deleted permanently.")
        return redirect("home")

    return render(request, "users/profile_confirm_delete.html", context)
