"""
URL routing for users app (template-based views)

Includes routes for:
- User registration
- User login
- Logout
"""

from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
