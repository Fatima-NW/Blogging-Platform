import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

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
