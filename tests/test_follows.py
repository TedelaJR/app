
from app.core.security import create_access_token


def get_auth_headers(user):
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_follow_user(client, normal_user, admin_user):
    response = client.post(
        f"/api/v1/users/{admin_user.id}/follow",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 201

    data = response.json()
    assert data["follower_id"] == normal_user.id
    assert data["following_id"] == admin_user.id


def test_cannot_follow_same_user_twice(client, normal_user, admin_user):
    headers = get_auth_headers(normal_user)
    url = f"/api/v1/users/{admin_user.id}/follow"

    first_response = client.post(url, headers=headers)
    second_response = client.post(url, headers=headers)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_cannot_follow_yourself(client, normal_user):
    response = client.post(
        f"/api/v1/users/{normal_user.id}/follow",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 409


def test_follow_nonexistent_user(client, normal_user):
    response = client.post(
        "/api/v1/users/999999/follow",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 404


def test_unfollow_user(client, normal_user, admin_user):
    headers = get_auth_headers(normal_user)
    url = f"/api/v1/users/{admin_user.id}/follow"

    follow_response = client.post(url, headers=headers)
    assert follow_response.status_code == 201

    response = client.delete(url, headers=headers)

    assert response.status_code == 204


def test_cannot_unfollow_if_not_following(
    client, normal_user, admin_user
):
    response = client.delete(
        f"/api/v1/users/{admin_user.id}/follow",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 404


def test_get_followers(client, normal_user, admin_user):
    response = client.post(
        f"/api/v1/users/{admin_user.id}/follow",
        headers=get_auth_headers(normal_user),
    )
    assert response.status_code == 201

    response = client.get(
        f"/api/v1/users/{admin_user.id}/followers",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["follower_id"] == normal_user.id


def test_get_following(client, normal_user, admin_user):
    response = client.post(
        f"/api/v1/users/{admin_user.id}/follow",
        headers=get_auth_headers(normal_user),
    )
    assert response.status_code == 201

    response = client.get(
        f"/api/v1/users/{normal_user.id}/following",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["following_id"] == admin_user.id


def test_follow_status(client, normal_user, admin_user):
    headers = get_auth_headers(normal_user)
    url = f"/api/v1/users/{admin_user.id}/follow"

    client.post(url, headers=headers)

    response = client.get(
        f"/api/v1/users/{admin_user.id}/follow-status",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_following"] is True


def test_follow_status_when_not_following(
    client, normal_user, admin_user
):
    response = client.get(
        f"/api/v1/users/{admin_user.id}/follow-status",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert response.json()["is_following"] is False


def test_follow_counts(client, normal_user, admin_user):
    headers = get_auth_headers(normal_user)

    client.post(
        f"/api/v1/users/{admin_user.id}/follow",
        headers=headers,
    )

    response = client.get(
        f"/api/v1/users/{admin_user.id}/follow-counts",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == admin_user.id
    assert data["followers_count"] == 1
    assert data["following_count"] == 0


def test_follow_requires_authentication(client, admin_user):
    response = client.post(
        f"/api/v1/users/{admin_user.id}/follow",
    )

    assert response.status_code == 401
