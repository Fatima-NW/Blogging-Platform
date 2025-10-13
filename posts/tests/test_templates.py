import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from posts.models import Post, Comment, Like

User = get_user_model()


# ---------------- FIXTURES ----------------

@pytest.fixture
def user(db):
    """ Creates a test user """
    return User.objects.create_user(
        username="fatima",
        email="fatima@example.com",
        password="testpass"
    )

@pytest.fixture
def another_user(db):
    """ Creates a second user (for testing permission behavior) """
    return User.objects.create_user(
        username="alex",
        email="alex@example.com",
        password="pass123"
    )

@pytest.fixture
def post(user):
    """ Creates a sample post authored by the main user """
    return Post.objects.create(title="Sample Post", content="Post content", author=user)

@pytest.fixture
def comment(user, post):
    """ Creates a comment belonging to the sample post """
    return Comment.objects.create(post=post, author=user, content="A comment")

@pytest.fixture
def client_logged_in(client, user):
    """ Logs the test client in """
    client.login(username="fatima", password="testpass")
    return client


# ---------------- LIST & DETAIL VIEWS ----------------

@pytest.mark.django_db
def test_post_list_view(client, post):
    """ Ensure that the post list view renders correctly and includes the expected post in its context """
    url = reverse("post_list")
    response = client.get(url)
    assert response.status_code == 200
    assert "posts" in response.context
    assert post in response.context["posts"]
    assert "posts/post_list.html" in [t.name for t in response.templates]

@pytest.mark.django_db
def test_post_detail_view_context(client, post, comment, user):
    """ Test that the post detail view returns the correct context data: comments, counts, forms, and like info """
    url = reverse("post_detail", args=[post.pk])
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    context = response.context
    assert context["post"] == post
    assert "comments" in context
    assert comment in context["comments"]
    assert "comment_form" in context
    assert isinstance(context["comment_count"], int)
    assert isinstance(context["like_count"], int)
    assert context["user_has_liked"] is False


# ---------------- POST VIEWS ----------------

# CREATE POST

@pytest.mark.django_db
def test_post_create_view(client_logged_in):
    """ Logged-in users should be able to create posts successfully """
    url = reverse("post_create")
    data = {"title": "New Post", "content": "New content"}
    response = client_logged_in.post(url, data)
    # successful creation should redirect to post_list
    assert response.status_code == 302
    assert Post.objects.filter(title="New Post").exists()

@pytest.mark.django_db
def test_post_create_requires_login(client):
    """ Anonymous users should be redirected to login page when trying to create a post """
    url = reverse("post_create")
    response = client.get(url)
    # should redirect to login page
    assert response.status_code == 302
    assert "/login" in response.url

# UPDATE POST

@pytest.mark.django_db
def test_post_edit_by_author(client_logged_in, post):
    """ The author of a post should be able to edit their own post """
    url = reverse("post_edit", args=[post.pk])
    response = client_logged_in.post(url, {"title": "Updated Title", "content": "Changed"})
    assert response.status_code == 302
    post.refresh_from_db()
    assert post.title == "Updated Title"

@pytest.mark.django_db
def test_post_edit_by_non_author_raises_error(client, another_user, post):
    " A non-author attempting to edit someone else's post should receive a 403 error "
    client.force_login(another_user)
    url = reverse("post_edit", args=[post.pk])
    response = client.post(url, {"title": "Hack", "content": "Unauthorized"})
    assert response.status_code == 403  # PermissionDenied

# DELETE POST

@pytest.mark.django_db
def test_post_delete_by_author(client_logged_in, post):
    """ The author should be able to delete their post successfully """
    url = reverse("post_delete", args=[post.pk])
    response = client_logged_in.post(url)
    assert response.status_code == 302
    assert not Post.objects.filter(pk=post.pk).exists()

@pytest.mark.django_db
def test_post_delete_by_non_author_forbidden(client, another_user, post):
    """ Non-authors should not be allowed to delete someone else's post """
    client.force_login(another_user)
    url = reverse("post_delete", args=[post.pk])
    response = client.post(url)
    assert response.status_code == 403


# ---------------- COMMENT TESTS ----------------

# ADD COMMENT

@pytest.mark.django_db
def test_add_comment(client_logged_in, post, user):
    """ Logged-in users can add comments to a post """
    url = reverse("add_comment", args=[post.pk])
    data = {"content": "Nice post!"}
    response = client_logged_in.post(url, data)
    assert response.status_code == 302
    assert Comment.objects.filter(post=post, author=user, content="Nice post!").exists()

@pytest.mark.django_db
def test_add_comment_requires_login(client, post):
    """ Anonymous users should be redirected to login when trying to comment """
    url = reverse("add_comment", args=[post.pk])
    response = client.post(url, {"content": "Should not work"})
    assert response.status_code == 302
    assert "/login" in response.url
    assert not Comment.objects.filter(content="Should not work").exists()

# DELETE COMMENT 

@pytest.mark.django_db
def test_delete_own_comment(client_logged_in, comment):
    """ A user can delete their own comment """
    url = reverse("delete_comment", args=[comment.pk])
    response = client_logged_in.post(url)
    assert response.status_code == 302
    assert not Comment.objects.filter(pk=comment.pk).exists()

@pytest.mark.django_db
def test_delete_other_user_comment_forbidden(client, another_user, comment):
    """ A user trying to delete someone else's comment should fail — request succeeds but the comment remains """
    client.force_login(another_user)
    url = reverse("delete_comment", args=[comment.pk])
    response = client.post(url)
    # still redirects, but comment should remain
    assert response.status_code == 302
    assert Comment.objects.filter(pk=comment.pk).exists()


# ---------------- LIKE TESTS ----------------

@pytest.mark.django_db
def test_toggle_like_creates_like(client_logged_in, post, user):
    """ First call to toggle_like should create a Like record """
    url = reverse("toggle_like", args=[post.pk])
    response = client_logged_in.post(url)
    assert response.status_code == 302
    assert Like.objects.filter(post=post, user=user).exists()

@pytest.mark.django_db
def test_toggle_like_removes_existing_like(client_logged_in, post, user):
    """ Second call to toggle_like should remove the existing Like record """
    Like.objects.create(post=post, user=user)
    url = reverse("toggle_like", args=[post.pk])
    response = client_logged_in.post(url)
    assert response.status_code == 302
    assert not Like.objects.filter(post=post, user=user).exists()

@pytest.mark.django_db
def test_like_requires_login(client, post):
    """ Anonymous users should be redirected to login when liking """
    url = reverse("toggle_like", args=[post.pk])
    response = client.post(url)
    assert response.status_code == 302
    assert "/login" in response.url

@pytest.mark.django_db
def test_toggle_like_ajax_returns_json(client_logged_in, post):
    """ AJAX (XHR) should return JSON containing `liked` and `like_count` """
    url = reverse("toggle_like", args=[post.pk])
    response = client_logged_in.post(
        url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert response.status_code == 200
    data = response.json()
    assert "liked" in data
    assert "like_count" in data
