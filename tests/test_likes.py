from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.user import User


def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def create_test_post(client: TestClient, user: User) -> int:
    response = client.post(
        "/api/v1/posts",
        json={"content": "Test post for likes"},
        headers=get_auth_headers(user),
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_like_post(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)
    post_id = create_test_post(client, normal_user)

    response = client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["message"] == "Post liked successfully."


def test_cannot_like_post_twice(
    client: TestClient,
    normal_user: User,
):
    headers = get_auth_headers(normal_user)
    post_id = create_test_post(client, normal_user)

    first_response = client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=headers,
    )

    second_response = client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_unlike_post(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)
    post_id = create_test_post(client, normal_user)

    client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=headers,
    )

    response = client.delete(
        f"/api/v1/posts/{post_id}/like",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Post unliked successfully."


def test_like_count(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)
    post_id = create_test_post(client, normal_user)

    client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=headers,
    )

    response = client.get(
        f"/api/v1/posts/{post_id}/likes/count",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["like_count"] == 1


def test_like_status(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)
    post_id = create_test_post(client, normal_user)

    client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=headers,
    )

    response = client.get(
        f"/api/v1/posts/{post_id}/likes/me",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["liked"] is True


def test_unliked_status(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)
    post_id = create_test_post(client, normal_user)

    response = client.get(
        f"/api/v1/posts/{post_id}/likes/me",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["liked"] is False


def test_user_cannot_unlike_another_users_like(
    client: TestClient,
    normal_user: User,
    admin_user: User,
):
    owner_headers = get_auth_headers(normal_user)
    other_user_headers = get_auth_headers(admin_user)

    post_id = create_test_post(client, normal_user)

    client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=owner_headers,
    )

    response = client.delete(
        f"/api/v1/posts/{post_id}/like",
        headers=other_user_headers,
    )

    assert response.status_code == 404

    # The original user's like must still exist.
    count_response = client.get(
        f"/api/v1/posts/{post_id}/likes/count",
        headers=owner_headers,
    )

    assert count_response.json()["like_count"] == 1


def test_like_nonexistent_post(
    client: TestClient,
    normal_user: User,
):
    response = client.post(
        "/api/v1/posts/999999/like",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 404


def test_like_requires_authentication(client: TestClient):
    response = client.post("/api/v1/posts/1/like")

    assert response.status_code == 401