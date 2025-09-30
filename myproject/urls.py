"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from users import views as user_views

# simple home view just for testing
def home_view(request):
    return HttpResponse("<h1>Welcome Home!</h1>")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", user_views.home, name="home"),   # home/landing page
    path("users/", include("users.urls")),
    path("posts/", include("posts.urls")),   
]
