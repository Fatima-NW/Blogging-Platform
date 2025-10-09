from django.urls import path
from users.api.views import RegisterAPIView, ProfileAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api_register"),
    path("profile/", ProfileAPIView.as_view(), name="api_profile"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
