import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


# ---------------- FIXTURES ----------------

@pytest.fixture
def api_client():
    """ Return DRF API client """
    return APIClient()

@pytest.fixture
def user(db):
    """ Create a test user """
    return User.objects.create_user(
        username="fatima",
        email="fatima@example.com",
        password="testpass123"
    )

@pytest.fixture
def auth_client(api_client, user):
    """ Return authenticated API client (with JWT token) """
    token_url = reverse("token_obtain_pair")
    response = api_client.post(token_url, {"username": "fatima", "password": "testpass123"})
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ---------------- REGISTER TESTS ----------------

@pytest.mark.django_db
def test_register_api_success(api_client):
    """ Valid registration should create a new user and return 201 """
    url = reverse("api_register")
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "User registered successfully" in response.data["detail"]
    assert User.objects.filter(username="newuser").exists()

@pytest.mark.django_db
def test_register_api_password_mismatch(api_client):
    """ Registration fails when passwords don't match """
    url = reverse("api_register")
    data = {
        "username": "mismatchuser",
        "email": "mismatch@example.com",
        "password": "Password123",
        "password2": "Different123"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username="mismatchuser").exists()

@pytest.mark.django_db
def test_register_api_weak_password(api_client):
    """ Registration fails if the password is too weak """
    url = reverse("api_register")
    data = {
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "123",
        "password2": "123"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username="weakuser").exists()

@pytest.mark.django_db
def test_register_api_duplicate_username(api_client, user):
    """ Registration fails when username already exists """
    url = reverse("api_register")
    data = {
        "username": "fatima",
        "email": "duplicate@example.com",
        "password": "AnotherStrong123",
        "password2": "AnotherStrong123"
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in response.data or "non_field_errors" in response.data


# ---------------- PROFILE TESTS ----------------

@pytest.mark.django_db
def test_profile_api_authenticated(auth_client, user):
    """ Authenticated users can retrieve their profile """
    url = reverse("api_profile")
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == user.username
    assert response.data["email"] == user.email

@pytest.mark.django_db
def test_profile_api_requires_auth(api_client):
    """Unauthenticated users should receive 403 when accessing profile"""
    url = reverse("api_profile")
    response = api_client.get(url)
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

