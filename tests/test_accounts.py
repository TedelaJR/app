def test_user_can_deactivate_account(client, user_token):
    response = client.post(
        "/api/v1/accounts/deactivate",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivated_user_cannot_access_me(client, user_token):
    client.post(
        "/api/v1/accounts/deactivate",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 401


def test_admin_can_reactivate_user(
    client,
    normal_user,
    admin_token,
    db_session,
):
    normal_user.is_active = False
    db_session.commit()

    response = client.post(
        f"/api/v1/accounts/{normal_user.id}/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_user_cannot_reactivate_account(
    client,
    normal_user,
    user_token,
):
    response = client.post(
        f"/api/v1/accounts/{normal_user.id}/reactivate",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


def test_user_can_delete_own_account(client, user_token):
    response = client.delete(
        "/api/v1/accounts/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 204


def test_deleted_user_cannot_login(client, normal_user):
    client.delete(
        "/api/v1/accounts/me",
        headers={
            "Authorization": (
                "Bearer "
                + client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "TestPassword123",
                    },
                ).json()["access_token"]
            )
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 401