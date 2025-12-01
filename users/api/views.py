"""
API views for the users app

Includes views for:
- User registration
- User profile: view, update, delete
- @username autocompletion
- View notifications
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model, update_session_auth_hash
from users.serializers import RegisterSerializer, UserSerializer, DeleteSerializer, NotificationSerializer
from rest_framework.views import APIView
from mylogger import Logger

logger = Logger()
User = get_user_model()

class RegisterAPIView(generics.CreateAPIView):
    """ API endpoint for user registration """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """ Validate and create a new user """
        logger.info(f"Registration attempt for username: {request.data.get('username')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        logger.info(f"User registered successfully: {serializer.data.get('username')}")
        return Response(
            {"detail": "User registered successfully."},
            status=status.HTTP_201_CREATED
        )


class ProfileAPIView(generics.RetrieveAPIView):
    """ Retrieve the profile details of the authenticated user """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        logger.info(f"Profile requested by {self.request.user.username}")
        return self.request.user


class ProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
    """ Update profile of the authenticated user """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        new_password = serializer.validated_data.get("new_password")
        if new_password:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(self.request, user)
        logger.info(f"{user.username} updated their profile")


class ProfileDeleteAPIView(generics.DestroyAPIView):
    """ Delete user profile """
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteSerializer

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        logger.info(f"User {user.username} deleted their account")
        user.delete()
        return Response({"detail": "Account deleted successfully."}, status=200)


class UserSearchAPIView(APIView):
    """ Search users for @mentions """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.GET.get("q", "")
        users = User.objects.filter(username__istartswith=q)[:10]
        usernames = [user.username for user in users]
        logger.info(f"User search for '{q}' by {request.user.username}: {usernames}")
        return Response(usernames)


class NotificationListAPIView(generics.ListAPIView):
    """ View all notifications for the authenticated user """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.info(f"{self.request.user.username} requested notifications")
        return self.request.user.notifications.all().order_by('-created_at')