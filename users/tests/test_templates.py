"""
Template view tests for the users app

Tests include:
- Registration page rendering and form submission
- Login page rendering and authentication
- Logout functionality
- Home view rendering
- Profile page rendering, editing and deletion
- Notification page rendering and proper redirection
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from posts.models import Post
from users.models import Notification

User = get_user_model()


# ---------- FIXTURES ----------

@pytest.fixture
def user(db):
    """ Creates a test user """
    return User.objects.create_user(
        username="fatima",
        email="fatima@example.com",
        password="testpass123"
    )

@pytest.fixture
def another_user(db):
    """ Creates a second user (for testing permission behavior) """
    return User.objects.create_user(
        username="alex",
        email="alex@example.com",
        password="pass1234"
    )

@pytest.fixture
def post(user):
    """ Creates a sample post authored by the main user """
    return Post.objects.create(title="Sample Post", content="Post content", author=user)

@pytest.fixture
def notification(user, post):
    """ Creates a notification for the test user """
    return Notification.objects.create(user=user, message="Test notification", post=post)

@pytest.fixture
def client_logged_in(client, user):
    """ Login test client """
    client.login(username="fatima", password="testpass123")
    return client


# ---------- REGISTRATION TESTS ----------

@pytest.mark.django_db
def test_register_view_renders_form(client):
    """ GET request to register page should return 200 and render the registration form """
    url = reverse("register")
    response = client.get(url)
    assert response.status_code == 200
    assert "form" in response.context
    assert "users/register.html" in [t.name for t in response.templates]

@pytest.mark.django_db
def test_register_view_creates_user(client):
    """ POST valid data to register view should create a new user and redirect to the login page """
    url = reverse("register")
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password1": "StrongPass123",
        "password2": "StrongPass123"
    }
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse("login")
    assert User.objects.filter(username="newuser").exists()

@pytest.mark.django_db
def test_register_view_rejects_weak_password(client):
    """ The registration form should reject weak passwords and re-render the same page with errors """
    url = reverse("register")
    data = {
        "username": "weakuser",
        "email": "weak@example.com",
        "password1": "123",
        "password2": "123"
    }
    response = client.post(url, data)
    assert response.status_code == 200  # stays on the same page
    assert not User.objects.filter(username="weakuser").exists()
    assert "This password is too short" in str(response.content) or "password" in str(response.content).lower()


# ---------- LOGIN TESTS ----------

@pytest.mark.django_db
def test_login_view_renders_form(client):
    """ GET login page should load successfully with form """
    url = reverse("login")
    response = client.get(url)
    assert response.status_code == 200
    assert "users/login.html" in [t.name for t in response.templates]
    assert "form" in response.context

@pytest.mark.django_db
def test_login_view_success(client, user):
    """ POST valid credentials should log user in and redirect to post list page """
    url = reverse("login")
    data = {"username": "fatima", "password": "testpass123"}
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse("post_list")

@pytest.mark.django_db
def test_login_view_invalid_credentials(client):
    """ Invalid login should stay on same page and display error messages """
    url = reverse("login")
    data = {"username": "unknown", "password": "wrong"}
    response = client.post(url, data)
    assert response.status_code == 200
    assert "Please enter a correct" in str(response.content)


# ---------- LOGOUT TEST ----------

@pytest.mark.django_db
def test_logout_view_redirects_home(client_logged_in):
    """ Logout should clear the session and redirect to home """
    url = reverse("logout")
    response = client_logged_in.get(url)
    assert response.status_code == 302
    assert response.url == reverse("home")


# ---------- HOME VIEW TEST----------

@pytest.mark.django_db
def test_home_view_renders(client):
    """ Home view should return 200 and use home.html """
    url = reverse("home")
    response = client.get(url)
    assert response.status_code == 200
    assert "home.html" in [t.name for t in response.templates]


# ---------------- PROFILE VIEW TESTS ----------------

@pytest.mark.django_db
def test_profile_view_renders(client_logged_in, user, post):
    """ Profile view should return 200, render profile template, and include user's posts """
    url = reverse("profile", args=[user.username])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert "profile_user" in response.context
    assert response.context["profile_user"] == user
    assert "posts" in response.context
    assert post in response.context["posts"]
    assert "users/profile.html" in [t.name for t in response.templates]

@pytest.mark.django_db
def test_profile_edit_by_owner_updates_profile(client_logged_in, user):
    """ Profile owner should be able to edit their own profile """
    url = reverse("profile_edit", args=[user.username])
    data = { "username": user.username, "first_name": "Fatima", "last_name": "Test",  "new_password1": "", "new_password2": "", "current_password": "", "bio": "",}
    response = client_logged_in.post(url, data)
    user.refresh_from_db()
    assert response.status_code == 302
    assert user.first_name == "Fatima"
    assert user.last_name == "Test"

@pytest.mark.django_db
def test_profile_edit_by_non_owner_redirects(client, user, another_user):
    """ Non-owner attempting to edit another user's profile should be redirected """
    client.login(username="alex", password="pass1234")
    url = reverse("profile_edit", args=[user.username])
    response = client.post(url, {"first_name": "Hack"})
    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("profile", args=[user.username])
    assert user.first_name != "Hack"

@pytest.mark.django_db
def test_profile_delete_get_and_post(client_logged_in, user):
    """ Profile delete should render confirmation page and POST deletes user """
    url = reverse("profile_delete")
    # GET request
    response_get = client_logged_in.get(url)
    assert response_get.status_code == 200
    assert "post_count" in response_get.context
    assert "users/profile_confirm_delete.html" in [t.name for t in response_get.templates]
    # POST request deletes user
    response_post = client_logged_in.post(url)
    assert response_post.status_code == 302
    assert response_post.url == reverse("home")
    assert not User.objects.filter(pk=user.pk).exists()

@pytest.mark.django_db
def test_profile_delete_by_non_owner_forbidden(client, user, another_user):
    """ Non-owner attempting to delete another user's profile should not succeed """
    client.login(username="alex", password="pass1234")
    url = reverse("profile_delete")
    response = client.post(url, follow=True)
    assert User.objects.filter(pk=user.pk).exists()
    assert response.status_code in (200, 403, 302) 


# ---------------- NOTIFICATIONS VIEW TESTS ----------------

@pytest.mark.django_db
def test_notifications_view_renders(client_logged_in, user, notification):
    """ Notifications view should return 200 and include user's notifications """
    url = reverse("notifications")
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert "notifications" in response.context
    assert notification in response.context["notifications"]
    assert "users/notifications.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_open_notification_marks_read_and_redirects(client_logged_in, user, notification):
    """ Accessing a notification should mark it as read and redirect to its post """
    url = reverse("open_notification", args=[notification.pk])
    response = client_logged_in.get(url)
    notification.refresh_from_db()
    assert notification.read is True
    assert response.status_code == 302
    assert response.url == reverse("post_detail", args=[notification.post.pk])