"""
Template view tests for the posts app

Includes tests for:
- Post views: list, detail, create, update, delete, download
- Comment views: add, delete, email
- Like views: toggle like/unlike, permission checks, AJAX response

Uses pytest fixtures to create test users, posts, and comments
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from posts.models import Post, Comment, Like
from unittest.mock import patch

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

# DOWNLOAD POST

@pytest.mark.django_db
def test_generate_post_pdf_sync(client_logged_in, post):
    """ Test synchronous PDF generation returns PDF response with correct headers """
    url = reverse("generate_post_pdf", args=[post.pk])
    response = client_logged_in.post(url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert f"{post.title}.pdf" in response["Content-Disposition"]
    assert isinstance(response.content, bytes)

@pytest.mark.django_db
def test_generate_post_pdf_async_dispatch(client_logged_in, post, user):
    """ Test that when PDF generation times out, a Celery task is dispatched """
    url = reverse("generate_post_pdf", args=[post.pk])
    with patch("posts.views.generate_post_pdf_bytes", side_effect=TimeoutError):
        with patch("posts.views.generate_post_pdf_task_and_email.delay") as mock_task:
            response = client_logged_in.post(url, follow=True)
            assert response.redirect_chain[-1][0] == reverse("post_detail", args=[post.pk])
            assert response.status_code == 200 
            mock_task.assert_called_once_with(post.pk, user.email)
            messages = list(response.context["messages"])
            assert any("PDF is being generated" in m.message for m in messages)


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

# UPDATE COMMENT

@pytest.mark.django_db
def test_edit_own_comment(client_logged_in, comment):
    """ Authors should be able to edit their own comment """
    url = reverse("update_comment", args=[comment.pk])
    response = client_logged_in.post(url, {"content": "Edited comment"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    comment.refresh_from_db()
    assert comment.content == "Edited comment"


@pytest.mark.django_db
def test_edit_other_users_comment_forbidden(client, another_user, comment):
    """ Non-authors cannot update another author's comment """
    client.force_login(another_user)
    url = reverse("update_comment", args=[comment.pk])
    response = client.post(url, {"content": "Hacked!"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "Unauthorized" in data["error"]
    comment.refresh_from_db()
    assert comment.content != "Hacked!"

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

# SEND EMAIL ON COMMENT

@pytest.mark.django_db
def test_comment_triggers_email_task(client_logged_in, post, user):
    """ Ensure that when a comment is added, the Celery email task is triggered """
    url = reverse("add_comment", args=[post.pk])
    data = {"content": "This is a test comment"}

    with patch("posts.views.notify_comment") as mock_notify:
        response = client_logged_in.post(url, data)
        assert response.status_code == 302  # Redirect to post detail

        mock_notify.assert_called_once()
        comment = Comment.objects.filter(post=post, content="This is a test comment").first()
        assert comment is not None
        assert comment.author == user


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
