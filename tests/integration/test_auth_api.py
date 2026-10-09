async def test_register_and_login(client):
    register_resp = await client.post(
        "/api/v1/auth/register", json={"email": "dev@example.com", "password": "supersecret123"}
    )
    assert register_resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "dev@example.com", "password": "supersecret123"}
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_rejected(client):
    await client.post("/api/v1/auth/register", json={"email": "dev2@example.com", "password": "supersecret123"})
    resp = await client.post("/api/v1/auth/login", json={"email": "dev2@example.com", "password": "wrong-password"})
    assert resp.status_code == 401
