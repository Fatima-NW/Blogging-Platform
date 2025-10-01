from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm

# Registration view
def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  
            return redirect("login")  
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
            return redirect("post_list")
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

# Logout view
def logout_view(request):
    logout(request)
    return redirect("home")  

# Home view
def home(request):
    return render(request, "home.html")
