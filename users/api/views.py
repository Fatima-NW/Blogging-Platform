"""
API views for the users app

Includes views for:
- User registration
- User profile
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from users.serializers import RegisterSerializer, UserSerializer

User = get_user_model()

class RegisterAPIView(generics.CreateAPIView):
    """ API endpoint for user registration """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """ Validate and create a new user """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"detail": "User registered successfully."},
            status=status.HTTP_201_CREATED
        )


class ProfileAPIView(generics.RetrieveAPIView):
    """ Retrieve the profile details of the authenticated user """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
