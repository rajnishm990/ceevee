async def test_delete_account_removes_everything(client, headers, section, upload, isolated_storage_dir, register_user):
    await client.put("/api/v1/profile", json={"full_name": "Me"}, headers=headers)
    await client.post("/api/v1/cover-letters", json={"name": "A", "body": "a"}, headers=headers)
    await upload(section["id"])
    await upload(section["id"])
    assert len(list(isolated_storage_dir.glob("*.enc"))) == 2

    resp = await client.request("DELETE", "/api/v1/auth/me", json={"password": "supersecret123"}, headers=headers)
    assert resp.status_code == 204
    assert list(isolated_storage_dir.glob("*.enc")) == []
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
    assert (await client.get(f"/api/v1/public/{section['shareable_slug']}")).status_code == 404
    login = await client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "supersecret123"})
    assert login.status_code == 401


async def test_delete_account_requires_correct_password(client, headers, section):
    resp = await client.request("DELETE", "/api/v1/auth/me", json={"password": "wrong-password"}, headers=headers)
    assert resp.status_code == 403
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 200


async def test_delete_account_leaves_other_users_untouched(client, headers, section, upload, register_user):
    other = await register_user("other@example.com")
    other_section = (await client.post("/api/v1/sections", json={"domain_name": "ml"}, headers=other)).json()
    await upload(other_section["id"], hdrs=other)
    await client.request("DELETE", "/api/v1/auth/me", json={"password": "supersecret123"}, headers=headers)
    assert (await client.get(f"/api/v1/public/{other_section['shareable_slug']}")).status_code == 200
