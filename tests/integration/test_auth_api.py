import jwt

from app.core.config import settings


async def test_register_and_login(client):
    reg = await client.post("/api/v1/auth/register", json={"email": "dev@example.com", "password": "supersecret123"})
    assert reg.status_code == 201
    login = await client.post("/api/v1/auth/login", json={"email": "dev@example.com", "password": "supersecret123"})
    assert login.status_code == 200
    assert {"access_token", "refresh_token"} <= set(login.json())


async def test_duplicate_email_conflicts(client):
    body = {"email": "dup@example.com", "password": "supersecret123"}
    await client.post("/api/v1/auth/register", json=body)
    assert (await client.post("/api/v1/auth/register", json=body)).status_code == 409


async def test_wrong_password_and_unknown_user_look_identical(client):
    await client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "supersecret123"})
    wrong = await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "nope-nope-nope"})
    unknown = await client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_short_password_rejected(client):
    resp = await client.post("/api/v1/auth/register", json={"email": "s@example.com", "password": "short"})
    assert resp.status_code == 422


async def test_me_returns_current_user_without_password(client, headers):
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "owner@example.com"
    assert "hashed_password" not in resp.json()


async def test_protected_route_requires_token(client):
    assert (await client.get("/api/v1/sections")).status_code == 401
    assert (await client.get("/api/v1/sections", headers={"Authorization": "Bearer junk"})).status_code == 401


async def test_refresh_token_cannot_be_used_as_access_token(client):
    await client.post("/api/v1/auth/register", json={"email": "r@example.com", "password": "supersecret123"})
    tokens = (await client.post("/api/v1/auth/login", json={"email": "r@example.com", "password": "supersecret123"})).json()
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert resp.status_code == 401


async def test_access_token_cannot_be_used_to_refresh(client):
    await client.post("/api/v1/auth/register", json={"email": "r2@example.com", "password": "supersecret123"})
    tokens = (await client.post("/api/v1/auth/login", json={"email": "r2@example.com", "password": "supersecret123"})).json()
    assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})).status_code == 401


async def test_refresh_issues_working_tokens(client):
    await client.post("/api/v1/auth/register", json={"email": "r3@example.com", "password": "supersecret123"})
    tokens = (await client.post("/api/v1/auth/login", json={"email": "r3@example.com", "password": "supersecret123"})).json()
    new = (await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})).json()
    assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new['access_token']}"})).status_code == 200


async def test_token_signed_with_wrong_key_rejected(client):
    forged = jwt.encode({"sub": "1", "type": "access"}, "some-other-key", algorithm=settings.JWT_ALGORITHM)
    assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})).status_code == 401


async def test_login_is_rate_limited(client):
    body = {"email": "x@example.com", "password": "wrong-password"}
    codes = [(await client.post("/api/v1/auth/login", json=body)).status_code for _ in range(12)]
    assert codes[:10] == [401] * 10 and 429 in codes[10:]
