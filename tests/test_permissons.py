def test_admin_can_access_dashboard(client, admin_token):
    response = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_normal_user_cannot_access_dashboard(client, user_token):
    response = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_access_dashboard(client):
    response = client.get("/api/v1/admin/dashboard")

    assert response.status_code == 401