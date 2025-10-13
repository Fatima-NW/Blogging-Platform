import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from posts.models import Post, Comment, Like

User = get_user_model()


# ---------------- FIXTURES ----------------

@pytest.fixture
def user(db):
    """ Create a main test user """
    return User.objects.create_user(
        username="fatima",
        email="fatima@example.com",
        password="testpass123"
    )

@pytest.fixture
def another_user(db):
    """ Create a second user for permission checks """
    return User.objects.create_user(
        username="alex",
        email="alex@example.com",
        password="pass123"
    )

@pytest.fixture
def api_client():
    """ Return DRF APIClient instance """
    return APIClient()

@pytest.fixture
def auth_client(api_client, user):
    """ Return an authenticated API client with JWT token """
    # get JWT access token
    token_url = reverse("token_obtain_pair")
    response = api_client.post(token_url, {"username": "fatima", "password": "testpass123"})
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client

@pytest.fixture
def post(user):
    """ Create a post by the main user """
    return Post.objects.create(title="Sample Post", content="Sample content", author=user)

@pytest.fixture
def comment(user, post):
    """ Create a comment on a post """
    return Comment.objects.create(post=post, author=user, content="A comment")

@pytest.fixture
def comment_factory():
    """ Factory to create comments flexibly """
    def create_comment(**kwargs):
        defaults = {"content": "Default comment"}
        defaults.update(kwargs)
        return Comment.objects.create(**defaults)
    return create_comment


# ---------------- LIST & DETAIL VIEWS ----------------

@pytest.mark.django_db
def test_post_list_api(api_client, post):
    """ Anyone can view the list of posts """
    url = reverse("api_post_list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data["results"], list)
    assert response.data["results"][0]["title"] == post.title

@pytest.mark.django_db
def test_post_detail_api(api_client, post):
    """ Anyone can view a single post """
    url = reverse("api_post_detail", args=[post.pk])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == post.id
    assert "likes_count" in response.data


# ---------------- POST TESTS ----------------

# CREATE POST

@pytest.mark.django_db
def test_post_create_api(auth_client):
    """ Authenticated users can create posts """
    url = reverse("api_post_create")
    data = {"title": "My Post", "content": "Something cool"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert Post.objects.filter(title="My Post").exists()

@pytest.mark.django_db
def test_post_create_api_requires_auth(api_client):
    """ Anonymous users cannot create posts """
    url = reverse("api_post_create")
    data = {"title": "New Post", "content": "Test content"}
    response = api_client.post(url, data)
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

# UPDATE POST

@pytest.mark.django_db
def test_post_update_api_by_author(auth_client, post):
    """ Author can update their own post """
    url = reverse("api_post_update", args=[post.pk])
    data = {"title": "Updated Title"}
    response = auth_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    post.refresh_from_db()
    assert post.title == "Updated Title"

@pytest.mark.django_db
def test_post_update_api_by_non_author(api_client, another_user, post):
    """ Non-authors cannot update posts they didn't create """
    token_url = reverse("token_obtain_pair")
    response = api_client.post(token_url, {"username": "alex", "password": "pass123"})
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("api_post_update", args=[post.pk])
    response = api_client.patch(url, {"title": "Hacked"})
    assert response.status_code == status.HTTP_404_NOT_FOUND  # queryset filtered by author

# DELETE POSTS

@pytest.mark.django_db
def test_post_delete_api_by_author(auth_client, post):
    """ Author can delete their own post """
    url = reverse("api_post_delete", args=[post.pk])
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    assert not Post.objects.filter(pk=post.pk).exists()

@pytest.mark.django_db
def test_post_delete_api_forbidden_for_non_author(api_client, another_user, post):
    """ Non-author should not be able to delete someone else's post """
    token_url = reverse("token_obtain_pair")
    response = api_client.post(token_url, {"username": "alex", "password": "pass123"})
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("api_post_delete", args=[post.pk])
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND or response.status_code == status.HTTP_403_FORBIDDEN
    assert Post.objects.filter(pk=post.pk).exists()


# ---------------- COMMENT TESTS ----------------

# ADD COMMENT

@pytest.mark.django_db
def test_create_comment_api(auth_client, post):
    """ Authenticated users can comment on posts """
    url = reverse("api_comment_create", args=[post.pk])
    data = {"content": "Nice post!"}
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert Comment.objects.filter(post=post, content="Nice post!").exists()

@pytest.mark.django_db
def test_comment_create_requires_auth(api_client, post):
    """ Anonymous users cannot add comments """
    url = reverse("api_comment_create", args=[post.id])
    data = {"content": "I shouldn’t be allowed!"}
    response = api_client.post(url, data)
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

# UPDATE COMMENT

@pytest.mark.django_db
def test_update_comment_api(auth_client, comment):
    """ Authors can update their own comments """
    url = reverse("api_comment_update", args=[comment.pk])
    data = {"content": "Edited comment"}
    response = auth_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    comment.refresh_from_db()
    assert comment.content == "Edited comment"

@pytest.mark.django_db
def test_comment_update_forbidden_for_non_author(api_client, user, another_user, post, comment_factory):
    """ Non-authors cannot update another author's comment """
    comment = comment_factory(post=post, author=another_user)
    api_client.force_authenticate(user=user)
    url = reverse("api_comment_update", args=[comment.id])
    response = api_client.put(url, {"content": "Edited!"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

# DELETE COMMENT

@pytest.mark.django_db
def test_delete_comment_api(auth_client, comment):
    """ Authors can delete their own comments """
    url = reverse("api_comment_delete", args=[comment.pk])
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    assert not Comment.objects.filter(pk=comment.pk).exists()

@pytest.mark.django_db
def test_comment_delete_forbidden_for_non_author(api_client, user, another_user, post, comment_factory):
    """ Non-authors cannot delete another author's comment """
    comment = comment_factory(post=post, author=another_user)
    api_client.force_authenticate(user=user)
    url = reverse("api_comment_delete", args=[comment.id])
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------- LIKE TESTS ----------------

@pytest.mark.django_db
def test_toggle_like_api(auth_client, post, user):
    """ Authenticated users can like/unlike a post """
    url = reverse("api_toggle_like", args=[post.pk])

    # Like
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["liked"] is True
    assert Like.objects.filter(post=post, user=user).exists()

    # Unlike
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["liked"] is False
    assert not Like.objects.filter(post=post, user=user).exists()

@pytest.mark.django_db
def test_toggle_like_api_requires_auth(api_client, post):
    """ Anonymous users cannot like/unlike a post """
    url = reverse("api_toggle_like", args=[post.id])
    response = api_client.post(url)
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

