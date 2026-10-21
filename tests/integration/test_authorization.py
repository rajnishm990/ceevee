import pytest


@pytest.fixture()
async def intruder(register_user):
    return await register_user("intruder@example.com")


async def test_other_user_cannot_touch_section(client, section, intruder):
    sid = section["id"]
    assert (await client.get(f"/api/v1/sections/{sid}", headers=intruder)).status_code == 403
    assert (await client.patch(f"/api/v1/sections/{sid}", json={"domain_name": "x"}, headers=intruder)).status_code == 403
    assert (await client.delete(f"/api/v1/sections/{sid}", headers=intruder)).status_code == 403
    assert (await client.get(f"/api/v1/sections/{sid}/active-pdf", headers=intruder)).status_code == 403
    assert (await client.post(f"/api/v1/sections/{sid}/active-version", json={"version_id": 1}, headers=intruder)).status_code == 403


async def test_other_user_cannot_upload_into_section(client, section, intruder, make_pdf):
    files = {"file": ("r.pdf", make_pdf(), "application/pdf")}
    assert (await client.post(f"/api/v1/sections/{section['id']}/versions", files=files, headers=intruder)).status_code == 403


async def test_other_user_cannot_read_edit_or_delete_version(client, section, upload, intruder):
    version = await upload(section["id"])
    vid = version["id"]
    sid = next(iter(version["content"]))
    assert (await client.get(f"/api/v1/versions/{vid}", headers=intruder)).status_code == 403
    assert (await client.get(f"/api/v1/versions/{vid}/download", headers=intruder)).status_code == 403
    assert (await client.patch(f"/api/v1/versions/{vid}", json={"updated_content": {sid: "pwn"}}, headers=intruder)).status_code == 403
    assert (await client.patch(f"/api/v1/versions/{vid}/label", json={"label": "x"}, headers=intruder)).status_code == 403
    assert (await client.delete(f"/api/v1/versions/{vid}", headers=intruder)).status_code == 403


async def test_section_list_only_contains_own_sections(client, headers, section, intruder):
    assert (await client.get("/api/v1/sections", headers=intruder)).json() == []
    assert len((await client.get("/api/v1/sections", headers=headers)).json()) == 1


async def test_unauthenticated_cannot_access_anything_private(client, section):
    for path in (f"/api/v1/sections/{section['id']}", "/api/v1/profile", "/api/v1/cover-letters", "/api/v1/versions/1"):
        assert (await client.get(path)).status_code == 401
