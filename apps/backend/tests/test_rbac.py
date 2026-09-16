from tests.conftest import auth_header


def test_operator_cannot_create_admin(client, operator_admin):
    headers = auth_header(client, "operator@example.com", "password123")
    resp = client.post(
        "/api/admins",
        json={"name": "New", "email": "new@example.com", "password": "pass1234", "role": "OPERATOR"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_super_admin_can_create_admin(client, super_admin):
    headers = auth_header(client, "super@example.com", "password123")
    resp = client.post(
        "/api/admins",
        json={"name": "New", "email": "new@example.com", "password": "pass1234", "role": "OPERATOR"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"


def test_operator_cannot_assign_application(client, operator_admin):
    headers = auth_header(client, "operator@example.com", "password123")
    resp = client.patch("/api/applications/1/assign", json={"admin_id": 1}, headers=headers)
    assert resp.status_code == 403


def test_unauthenticated_cannot_list_applications(client):
    resp = client.get("/api/applications")
    assert resp.status_code == 401
