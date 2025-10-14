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
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm


def register_view(request):
    """ Display and process the user registration form """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  
            return redirect("login")  
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})

def login_view(request):
    """ Authenticate and log in a user using the login form """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("post_list")
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

def logout_view(request):
    """ Log out the current user and redirect to the homepage """
    logout(request)
    return redirect("home")  

def home(request):
    """ Render the home page """
    return render(request, "home.html")
