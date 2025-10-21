"""
Main URL configuration for the Django project

It includes routes for:
- Admin panel
- Home page
- User app (templates and API)
- Posts app (templates and API)
- JWT authentication endpoints
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from users import views as user_views
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,)

urlpatterns = [
    path("admin/", admin.site.urls),                   # Admin panel
    path("", user_views.home, name="home"),            # Home/landing page
    path("users/", include("users.urls")),             # Template-based user views
    path("api/", include("users.api.urls")),           # User-related API endpoints
    path("posts/", include("posts.urls")),             # Template-based post views      
    path("api/", include("posts.api.urls")),           # Post-related API endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),  # JWT obtain token
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # JWT refresh token
]
