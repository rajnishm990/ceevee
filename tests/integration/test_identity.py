import pytest


async def test_empty_profile_returns_defaults(client, headers):
    resp = await client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["linkedin_url"] is None and resp.json()["other_links"] == []


async def test_profile_upsert_and_read_back(client, headers):
    body = {
        "full_name": "Rajnish", "headline": "Backend Developer", "contact_email": "me@example.com",
        "linkedin_url": "https://linkedin.com/in/me", "github_url": "https://github.com/me",
        "other_links": [{"label": "Blog", "url": "https://blog.example.com"}],
        "custom_fields": [{"label": "Notice period", "value": "30 days"}],
    }
    assert (await client.put("/api/v1/profile", json=body, headers=headers)).status_code == 200
    got = (await client.get("/api/v1/profile", headers=headers)).json()
    assert got["github_url"] == "https://github.com/me" and got["custom_fields"][0]["value"] == "30 days"
    await client.put("/api/v1/profile", json={"full_name": "Changed"}, headers=headers)
    again = (await client.get("/api/v1/profile", headers=headers)).json()
    assert again["full_name"] == "Changed" and again["github_url"] is None


@pytest.mark.parametrize("bad", ["javascript:alert(1)", "ftp://x.com/a", "not a url", "data:text/html,hi"])
async def test_non_http_urls_rejected(client, headers, bad):
    assert (await client.put("/api/v1/profile", json={"linkedin_url": bad}, headers=headers)).status_code == 422
    link = {"other_links": [{"label": "x", "url": bad}]}
    assert (await client.put("/api/v1/profile", json=link, headers=headers)).status_code == 422


async def test_profiles_are_per_user(client, headers, register_user):
    await client.put("/api/v1/profile", json={"full_name": "Owner"}, headers=headers)
    other = await register_user("other@example.com")
    assert (await client.get("/api/v1/profile", headers=other)).json()["full_name"] is None


async def test_cover_letter_crud(client, headers):
    created = await client.post("/api/v1/cover-letters", json={"name": "General", "body": "Dear {{company}}"}, headers=headers)
    assert created.status_code == 201
    tid = created.json()["id"]
    upd = await client.patch(f"/api/v1/cover-letters/{tid}", json={"body": "Hi {{company}}"}, headers=headers)
    assert upd.json()["body"] == "Hi {{company}}"
    assert len((await client.get("/api/v1/cover-letters", headers=headers)).json()) == 1
    assert (await client.delete(f"/api/v1/cover-letters/{tid}", headers=headers)).status_code == 204
    assert (await client.get(f"/api/v1/cover-letters/{tid}", headers=headers)).status_code == 404


async def test_only_one_default_template(client, headers):
    a = (await client.post("/api/v1/cover-letters", json={"name": "A", "body": "a", "is_default": True}, headers=headers)).json()
    b = (await client.post("/api/v1/cover-letters", json={"name": "B", "body": "b", "is_default": True}, headers=headers)).json()
    listing = {t["id"]: t["is_default"] for t in (await client.get("/api/v1/cover-letters", headers=headers)).json()}
    assert listing == {a["id"]: False, b["id"]: True}


async def test_duplicate_template_name_conflicts(client, headers):
    await client.post("/api/v1/cover-letters", json={"name": "A", "body": "a"}, headers=headers)
    assert (await client.post("/api/v1/cover-letters", json={"name": "A", "body": "b"}, headers=headers)).status_code == 409


async def test_cannot_access_another_users_template(client, headers, register_user):
    tid = (await client.post("/api/v1/cover-letters", json={"name": "A", "body": "a"}, headers=headers)).json()["id"]
    other = await register_user("other@example.com")
    assert (await client.get(f"/api/v1/cover-letters/{tid}", headers=other)).status_code == 403
    assert (await client.patch(f"/api/v1/cover-letters/{tid}", json={"body": "x"}, headers=other)).status_code == 403
    assert (await client.delete(f"/api/v1/cover-letters/{tid}", headers=other)).status_code == 403
