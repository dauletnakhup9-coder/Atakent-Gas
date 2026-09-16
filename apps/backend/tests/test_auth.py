def test_login_success(client, super_admin):
    resp = client.post("/api/auth/login", json={"email": "super@example.com", "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["admin"]["email"] == "super@example.com"
    assert body["access_token"]


def test_login_wrong_password(client, super_admin):
    resp = client.post("/api/auth/login", json={"email": "super@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client, super_admin):
    from tests.conftest import auth_header

    headers = auth_header(client, "super@example.com", "password123")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "super@example.com"
