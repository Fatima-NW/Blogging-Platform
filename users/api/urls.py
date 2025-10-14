"""
URL routing for users app (API endpoints)

Includes routes for:
- Registering users
- Retrieving user profile
"""

from django.urls import path
from users.api.views import RegisterAPIView, ProfileAPIView

urlpatterns = [
    path("users/register/", RegisterAPIView.as_view(), name="api_register"),
    path("users/profile/", ProfileAPIView.as_view(), name="api_profile"),
]
