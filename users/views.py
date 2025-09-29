from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm

# Registration view
def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()    
            login(request, user)  # auto login after registration
            return redirect("home") 
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})

# Login view
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

# Logout view
def logout_view(request):
    logout(request)
    return redirect("login")  # after logout, go to login page

# Home view
def home(request):
    return render(request, "home.html")
