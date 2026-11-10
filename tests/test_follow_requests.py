
from app.core.security import create_access_token


def get_auth_headers(user):
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def make_private(client, user):
    response = client.patch(
        "/api/v1/users/me/privacy",
        json={"is_private": True},
        headers=get_auth_headers(user),
    )
    assert response.status_code == 200
    return response


def send_request(client, requester, target):
    return client.post(
        f"/api/v1/users/{target.id}/follow-request",
        headers=get_auth_headers(requester),
    )


def test_user_can_make_account_private(client, normal_user):
    response = make_private(client, normal_user)

    assert response.json()["is_private"] is True


def test_user_can_make_account_public(client, normal_user):
    make_private(client, normal_user)

    response = client.patch(
        "/api/v1/users/me/privacy",
        json={"is_private": False},
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert response.json()["is_private"] is False


def test_send_follow_request(client, normal_user, admin_user):
    make_private(client, admin_user)

    response = send_request(client, normal_user, admin_user)

    assert response.status_code == 201

    data = response.json()
    assert data["requester_id"] == normal_user.id
    assert data["target_id"] == admin_user.id


def test_cannot_send_duplicate_follow_request(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    first = send_request(client, normal_user, admin_user)
    second = send_request(client, normal_user, admin_user)

    assert first.status_code == 201
    assert second.status_code == 409


def test_cannot_send_request_to_public_account(
    client, normal_user, admin_user
):
    response = send_request(client, normal_user, admin_user)

    assert response.status_code == 409


def test_cannot_send_follow_request_to_yourself(
    client, normal_user
):
    make_private(client, normal_user)

    response = send_request(client, normal_user, normal_user)

    assert response.status_code == 409


def test_cannot_request_nonexistent_user(client, normal_user):
    response = client.post(
        "/api/v1/users/999999/follow-request",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 404


def test_get_pending_follow_requests(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    request_response = send_request(
        client, normal_user, admin_user
    )
    assert request_response.status_code == 201

    response = client.get(
        "/api/v1/users/me/follow-requests",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["requester_id"] == normal_user.id


def test_accept_follow_request(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    request_response = send_request(
        client, normal_user, admin_user
    )
    request_id = request_response.json()["id"]

    response = client.post(
        f"/api/v1/follow-requests/{request_id}/accept",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["follower_id"] == normal_user.id
    assert response.json()["following_id"] == admin_user.id

    status_response = client.get(
        f"/api/v1/users/{admin_user.id}/follow-status",
        headers=get_auth_headers(normal_user),
    )

    assert status_response.status_code == 200
    assert status_response.json()["is_following"] is True


def test_reject_follow_request(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    request_response = send_request(
        client, normal_user, admin_user
    )
    request_id = request_response.json()["id"]

    response = client.post(
        f"/api/v1/follow-requests/{request_id}/reject",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 200

    pending = client.get(
        "/api/v1/users/me/follow-requests",
        headers=get_auth_headers(admin_user),
    )

    assert pending.json() == []


def test_cancel_own_follow_request(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    request_response = send_request(
        client, normal_user, admin_user
    )
    request_id = request_response.json()["id"]

    response = client.delete(
        f"/api/v1/follow-requests/{request_id}",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 200

    pending = client.get(
        "/api/v1/users/me/follow-requests",
        headers=get_auth_headers(admin_user),
    )

    assert pending.json() == []


def test_user_cannot_cancel_another_users_request(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    request_response = send_request(
        client, normal_user, admin_user
    )
    request_id = request_response.json()["id"]

    response = client.delete(
        f"/api/v1/follow-requests/{request_id}",
        headers=get_auth_headers(admin_user),
    )

    assert response.status_code == 404


def test_user_cannot_accept_another_users_request(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    request_response = send_request(
        client, normal_user, admin_user
    )
    request_id = request_response.json()["id"]

    response = client.post(
        f"/api/v1/follow-requests/{request_id}/accept",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 404


def test_direct_follow_private_account_is_rejected(
    client, normal_user, admin_user
):
    make_private(client, admin_user)

    response = client.post(
        f"/api/v1/users/{admin_user.id}/follow",
        headers=get_auth_headers(normal_user),
    )

    assert response.status_code == 409


def test_follow_request_requires_authentication(
    client, admin_user
):
    make_private(client, admin_user)

    response = client.post(
        f"/api/v1/users/{admin_user.id}/follow-request",
    )

    assert response.status_code == 401
