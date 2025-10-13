import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

# ---------------- FIXTURES ----------------

@pytest.fixture
def user(db):
    """ Creates a default test user """
    return User.objects.create_user(
        username="fatima",
        email="fatima@example.com",
        password="testpass123",
        bio="Hello, I am Fatima"
    )

@pytest.fixture
def another_user(db):
    """ Creates a second user for uniqueness tests """
    return User.objects.create_user(
        username="alex",
        email="alex@example.com",
        password="pass123"
    )

# ---------------- MODEL TESTS ----------------

@pytest.mark.django_db
def test_user_creation(user):
    """ Check that user object is created correctly """
    assert user.username == "fatima"
    assert user.email == "fatima@example.com"
    assert user.bio == "Hello, I am Fatima"
    assert str(user) == "fatima"

@pytest.mark.django_db
def test_email_unique_constraint(user):
    """ Ensure that two users cannot have the same email """
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            username="fatima2",
            email="fatima@example.com",
            password="newpass"
        )

@pytest.mark.django_db
def test_username_unique_constraint(user):
    """ Ensure that two users cannot have the same username """
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            username="fatima",
            email="fatima2@example.com",
            password="newpass"
        )

@pytest.mark.django_db
def test_bio_optional_field():
    """ User bio can be blank or null """
    user = User.objects.create_user(
        username="user2",
        email="user2@example.com",
        password="pass123",
        bio=""
    )
    assert user.bio == ""
    
    user2 = User.objects.create_user(
        username="user3",
        email="user3@example.com",
        password="pass123"
    )
    assert user2.bio is None
