import fitz
import pytest

from app.core.config import settings


async def test_gdrive_link_can_be_cleared(client, headers, section):
    await client.patch(f"/api/v1/sections/{section['id']}", json={"gdrive_link": "https://drive.google.com/x"}, headers=headers)
    cleared = await client.patch(f"/api/v1/sections/{section['id']}", json={"gdrive_link": None}, headers=headers)
    assert cleared.json()["gdrive_link"] is None


async def test_omitted_gdrive_link_is_left_alone(client, headers, section):
    await client.patch(f"/api/v1/sections/{section['id']}", json={"gdrive_link": "https://drive.google.com/x"}, headers=headers)
    kept = await client.patch(f"/api/v1/sections/{section['id']}", json={"domain_name": "platform"}, headers=headers)
    assert kept.json()["gdrive_link"] == "https://drive.google.com/x"


@pytest.mark.parametrize("bad", ["javascript:alert(1)", "data:text/html,x", "drive.google.com/no-scheme"])
async def test_non_http_gdrive_links_rejected(client, headers, section, bad):
    assert (await client.patch(f"/api/v1/sections/{section['id']}", json={"gdrive_link": bad}, headers=headers)).status_code == 422
    assert (await client.post("/api/v1/sections", json={"domain_name": "other", "gdrive_link": bad}, headers=headers)).status_code == 422


async def test_duplicate_section_name_conflicts_case_insensitively(client, headers, section):
    assert (await client.post("/api/v1/sections", json={"domain_name": "BACKEND"}, headers=headers)).status_code == 409
    other = (await client.post("/api/v1/sections", json={"domain_name": "frontend"}, headers=headers)).json()
    assert (await client.patch(f"/api/v1/sections/{other['id']}", json={"domain_name": "Backend"}, headers=headers)).status_code == 409


async def test_same_section_name_allowed_for_different_users(client, headers, section, register_user):
    other = await register_user("other@example.com")
    assert (await client.post("/api/v1/sections", json={"domain_name": "backend"}, headers=other)).status_code == 201


async def test_blank_section_name_rejected(client, headers):
    assert (await client.post("/api/v1/sections", json={"domain_name": "   "}, headers=headers)).status_code == 422


async def test_section_quota(client, headers, monkeypatch):
    monkeypatch.setattr(settings, "MAX_SECTIONS_PER_USER", 2)
    for name in ("a", "b"):
        assert (await client.post("/api/v1/sections", json={"domain_name": name}, headers=headers)).status_code == 201
    assert (await client.post("/api/v1/sections", json={"domain_name": "c"}, headers=headers)).status_code == 409


async def test_version_quota(client, headers, section, upload, monkeypatch, make_pdf):
    monkeypatch.setattr(settings, "MAX_VERSIONS_PER_SECTION", 2)
    await upload(section["id"])
    await upload(section["id"])
    files = {"file": ("r.pdf", make_pdf(), "application/pdf")}
    assert (await client.post(f"/api/v1/sections/{section['id']}/versions", files=files, headers=headers)).status_code == 409


async def test_rotate_slug_invalidates_old_link(client, headers, section, upload):
    await upload(section["id"])
    old = section["shareable_slug"]
    rotated = (await client.post(f"/api/v1/sections/{section['id']}/rotate-slug", headers=headers)).json()
    assert rotated["shareable_slug"] != old
    assert (await client.get(f"/api/v1/public/{old}")).status_code == 404
    assert (await client.get(f"/api/v1/public/{rotated['shareable_slug']}")).status_code == 200


async def test_rotate_slug_requires_ownership(client, section, register_user):
    other = await register_user("other@example.com")
    assert (await client.post(f"/api/v1/sections/{section['id']}/rotate-slug", headers=other)).status_code == 403


async def test_sharing_can_be_paused_and_resumed(client, headers, section, upload):
    await upload(section["id"])
    url = f"/api/v1/public/{section['shareable_slug']}"
    paused = await client.patch(f"/api/v1/sections/{section['id']}", json={"sharing_enabled": False}, headers=headers)
    assert paused.json()["sharing_enabled"] is False
    assert (await client.get(url)).status_code == 404
    assert (await client.get(f"/api/v1/sections/{section['id']}/active-pdf", headers=headers)).status_code == 200
    await client.patch(f"/api/v1/sections/{section['id']}", json={"sharing_enabled": True}, headers=headers)
    assert (await client.get(url)).status_code == 200


async def test_newlines_in_edits_are_flattened(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    resp = await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: "Line one\nLine two"}}, headers=headers)
    assert resp.status_code == 200 and resp.json()["content"][sid] == "Line one Line two"
    pdf = (await client.get(f"/api/v1/versions/{version['id']}/download", headers=headers)).content
    assert len(fitz.open(stream=pdf, filetype="pdf")[0].get_text().strip().splitlines()) == 1


@pytest.mark.parametrize("text", ["こんにちは", "Hello 😀"])
async def test_unrenderable_characters_rejected_not_silently_corrupted(client, headers, section, upload, text):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    resp = await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: text}}, headers=headers)
    assert resp.status_code == 400 and "can't be drawn" in resp.json()["detail"]
    assert (await client.get(f"/api/v1/versions/{version['id']}", headers=headers)).json()["content"][sid] == "Junior Backend Engineer"


async def test_typographic_characters_are_accepted(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    text = "Café – résumé • “quoted” €"
    assert (await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: text}}, headers=headers)).status_code == 200


async def test_clearing_a_span_to_empty_text_works(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    assert (await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: ""}}, headers=headers)).status_code == 200


async def test_health_and_ready(client):
    assert (await client.get("/health")).json()["status"] == "ok"
    assert (await client.get("/ready")).json() == {"status": "ready"}


async def test_cors_does_not_allow_credentials_or_random_origins(client):
    ok = await client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-credentials" not in ok.headers
    evil = await client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in evil.headers


async def test_oversized_request_returns_413_not_500(client, headers, section, make_pdf, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 10)
    resp = await client.post(
        f"/api/v1/sections/{section['id']}/versions", files={"file": ("r.pdf", make_pdf(), "application/pdf")}, headers=headers
    )
    assert resp.status_code == 413
