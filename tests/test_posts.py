from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.user import User


def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_create_post(client: TestClient, normal_user: User):
    response = client.post(
        "/api/v1/posts",
        json={
            "content": "My first social media post!",
            "image_url": "https://example.com/image.jpg",
        },
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["content"] == "My first social media post!"
    assert data["user_id"] == normal_user.id
    assert data["image_url"] == "https://example.com/image.jpg"
    assert "id" in data
    assert "created_at" in data


def test_get_posts(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)

    client.post(
        "/api/v1/posts",
        json={"content": "First post"},
        headers=headers,
    )

    client.post(
        "/api/v1/posts",
        json={"content": "Second post"},
        headers=headers,
    )

    response = client.get("/api/v1/posts", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_single_post(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)

    create_response = client.post(
        "/api/v1/posts",
        json={"content": "A post to retrieve"},
        headers=headers,
    )

    post_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/posts/{post_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == post_id
    assert response.json()["content"] == "A post to retrieve"


def test_update_own_post(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)

    create_response = client.post(
        "/api/v1/posts",
        json={"content": "Original content"},
        headers=headers,
    )

    post_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/posts/{post_id}",
        json={"content": "Updated content"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated content"


def test_cannot_update_another_users_post(
    client: TestClient,
    normal_user: User,
    admin_user: User,
):
    owner_headers = get_auth_headers(normal_user)
    other_user_headers = get_auth_headers(admin_user)

    create_response = client.post(
        "/api/v1/posts",
        json={"content": "This belongs to another user"},
        headers=owner_headers,
    )

    post_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/posts/{post_id}",
        json={"content": "Unauthorized update"},
        headers=other_user_headers,
    )

    assert response.status_code == 404


def test_delete_own_post(client: TestClient, normal_user: User):
    headers = get_auth_headers(normal_user)

    create_response = client.post(
        "/api/v1/posts",
        json={"content": "Post to delete"},
        headers=headers,
    )

    post_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/posts/{post_id}",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/posts/{post_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_cannot_delete_another_users_post(
    client: TestClient,
    normal_user: User,
    admin_user: User,
):
    owner_headers = get_auth_headers(normal_user)
    other_user_headers = get_auth_headers(admin_user)

    create_response = client.post(
        "/api/v1/posts",
        json={"content": "Protected post"},
        headers=owner_headers,
    )

    post_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/posts/{post_id}",
        headers=other_user_headers,
    )

    assert response.status_code == 404


def test_create_post_with_empty_content(
    client: TestClient,
    normal_user: User,
):
    response = client.post(
        "/api/v1/posts",
        json={"content": "   "},
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 422


def test_posts_require_authentication(client: TestClient):
    response = client.get("/api/v1/posts")

    assert response.status_code == 401