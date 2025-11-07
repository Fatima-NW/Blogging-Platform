"""
URL routing for users app (API endpoints)

Includes routes for:
- Registering users
- Retrieving user profile
- @username autocomplete dropdown
"""

from django.urls import path
from users.api.views import RegisterAPIView, ProfileAPIView, UserSearchAPIView

urlpatterns = [
    path("users/register/", RegisterAPIView.as_view(), name="api_register"),
    path("users/profile/", ProfileAPIView.as_view(), name="api_profile"),
    path('users/search/', UserSearchAPIView.as_view(), name='api_search'),
]
