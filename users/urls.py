"""
URL routing for users app (template-based views)

Includes routes for:
- User registration
- User login
- Logout
- Profile view + edit
"""

from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("profile/<str:username>/edit/", views.profile_edit, name="profile_edit"),
    path("delete/", views.profile_delete, name="profile_delete"),
]
