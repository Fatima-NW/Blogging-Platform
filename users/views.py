"""
Template-based views for the users app

Includes views for:
- User registration
- Login 
- Logout 
- Home page
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
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
    messages.info(request, "You have been logged out.")
    return redirect("home")  


def home(request):
    """ Render the home page """
    username = request.user.username if request.user.is_authenticated else "AnonymousUser"
    logger.info(f"{username} accessed home page ")
    return render(request, "home.html")
