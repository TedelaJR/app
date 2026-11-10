
from app.core.security import create_access_token


def get_auth_headers(user):
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def create_test_post(client, user):
    response = client.post(
        "/api/v1/posts",
        json={"content": "Test post"},
        headers=get_auth_headers(user),
    )
    assert response.status_code == 201
    return response.json()


def test_create_comment(client, normal_user):
    post = create_test_post(client, normal_user)

    response = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "This is my first comment"},
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["content"] == "This is my first comment"
    assert data["user_id"] == normal_user.id
    assert data["post_id"] == post["id"]


def test_create_comment_on_nonexistent_post(client, normal_user):
    response = client.post(
        "/api/v1/posts/999999/comments",
        json={"content": "Hello"},
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 404


def test_get_post_comments(client, normal_user):
    post = create_test_post(client, normal_user)
    headers = get_auth_headers(normal_user)

    client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "First comment"},
        headers=headers,
    )

    client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "Second comment"},
        headers=headers,
    )

    response = client.get(
        f"/api/v1/posts/{post['id']}/comments",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["content"] == "First comment"
    assert data[1]["content"] == "Second comment"


def test_get_comments_for_nonexistent_post(client, normal_user):
    response = client.get(
        "/api/v1/posts/999999/comments",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 404


def test_update_own_comment(client, normal_user):
    post = create_test_post(client, normal_user)
    headers = get_auth_headers(normal_user)

    comment_response = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "Original comment"},
        headers=headers,
    )

    comment_id = comment_response.json()["id"]

    response = client.patch(
        f"/api/v1/posts/comments/{comment_id}",
        json={"content": "Updated comment"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated comment"


def test_cannot_update_another_users_comment(
    client, normal_user, admin_user
):
    post = create_test_post(client, normal_user)

    comment_response = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "My comment"},
        headers=get_auth_headers(normal_user),
    )

    comment_id = comment_response.json()["id"]

    response = client.patch(
        f"/api/v1/posts/comments/{comment_id}",
        json={"content": "Unauthorized update"},
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 404


def test_delete_own_comment(client, normal_user):
    post = create_test_post(client, normal_user)
    headers = get_auth_headers(normal_user)

    comment_response = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "Comment to delete"},
        headers=headers,
    )

    comment_id = comment_response.json()["id"]

    response = client.delete(
        f"/api/v1/posts/comments/{comment_id}",
        headers=headers,
    )

    assert response.status_code == 204

    comments_response = client.get(
        f"/api/v1/posts/{post['id']}/comments",
        headers=headers,
    )

    assert comments_response.status_code == 200
    assert comments_response.json() == []


def test_cannot_delete_another_users_comment(
    client, normal_user, admin_user
):
    post = create_test_post(client, normal_user)

    comment_response = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "My comment"},
        headers=get_auth_headers(normal_user),
    )

    comment_id = comment_response.json()["id"]

    response = client.delete(
        f"/api/v1/posts/comments/{comment_id}",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 404


def test_create_comment_with_empty_content(client, normal_user):
    post = create_test_post(client, normal_user)

    response = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "   "},
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 422


def test_comments_require_authentication(client, normal_user):
    post = create_test_post(client, normal_user)

    response = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "Unauthorized comment"},
    )

    assert response.status_code == 401
