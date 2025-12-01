"""
URL routing for users app (API endpoints)

Includes routes for:
- Registering users
- Retrieving, updating and deleting user profiles
- @username autocomplete dropdown
- Viewing notifications
"""

from django.urls import path
from users.api.views import RegisterAPIView, ProfileAPIView, ProfileUpdateAPIView, ProfileDeleteAPIView, UserSearchAPIView, NotificationListAPIView

urlpatterns = [
    path("users/register/", RegisterAPIView.as_view(), name="api_register"),
    path("users/profile/", ProfileAPIView.as_view(), name="api_profile"),
    path("users/profile/update/", ProfileUpdateAPIView.as_view(), name="api_profile_update"),
    path("users/profile/delete/", ProfileDeleteAPIView.as_view(), name="api_profile_delete"),
    path('users/search/', UserSearchAPIView.as_view(), name='api_search'),
    path("users/notifications/", NotificationListAPIView.as_view(), name="api_notifications"),
]
