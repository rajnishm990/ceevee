import asyncio

import fitz


def _text(pdf_bytes: bytes) -> str:
    return fitz.open(stream=pdf_bytes, filetype="pdf")[0].get_text()


def _enc_files(storage):
    return sorted(storage.glob("*.enc")) if storage.exists() else []


async def _patch(client, headers, version, sid, text, base=None):
    body = {"updated_content": {sid: text}}
    if base is not None:
        body["base_revision"] = base
    return await client.patch(f"/api/v1/versions/{version['id']}", json=body, headers=headers)


async def test_upload_starts_at_revision_one_and_edits_increment_it(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    assert version["revision"] == 1
    first = await _patch(client, headers, version, sid, "One", base=1)
    second = await _patch(client, headers, version, sid, "Two", base=2)
    assert (first.json()["revision"], second.json()["revision"]) == (2, 3)


async def test_stale_revision_is_rejected_and_changes_nothing(client, headers, section, upload, isolated_storage_dir):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    await _patch(client, headers, version, sid, "Winner", base=1)
    files_before = _enc_files(isolated_storage_dir)
    stale = await _patch(client, headers, version, sid, "Loser", base=1)
    assert stale.status_code == 409
    assert _enc_files(isolated_storage_dir) == files_before
    current = (await client.get(f"/api/v1/versions/{version['id']}", headers=headers)).json()
    assert current["content"][sid] == "Winner" and current["revision"] == 2


async def test_omitting_base_revision_still_saves(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    assert (await _patch(client, headers, version, sid, "No base")).status_code == 200


async def test_concurrent_saves_from_same_revision_only_one_wins(client, headers, section, upload, isolated_storage_dir):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    results = await asyncio.gather(
        _patch(client, headers, version, sid, "Tab A", base=1), _patch(client, headers, version, sid, "Tab B", base=1)
    )
    assert sorted(r.status_code for r in results) == [200, 409]
    assert len(_enc_files(isolated_storage_dir)) == 2


async def test_preview_returns_edited_pdf_without_saving(client, headers, section, upload, isolated_storage_dir):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    files_before = _enc_files(isolated_storage_dir)
    resp = await client.post(
        f"/api/v1/versions/{version['id']}/preview", json={"updated_content": {sid: "Previewed Title"}}, headers=headers
    )
    assert resp.status_code == 200 and resp.headers["content-type"] == "application/pdf"
    assert "Previewed Title" in _text(resp.content)
    assert _enc_files(isolated_storage_dir) == files_before
    saved = (await client.get(f"/api/v1/versions/{version['id']}", headers=headers)).json()
    assert saved["revision"] == 1 and saved["content"][sid] == "Junior Backend Engineer"
    public = await client.get(f"/api/v1/public/{section['shareable_slug']}")
    assert "Junior Backend Engineer" in _text(public.content)


async def test_preview_validates_like_save(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    url = f"/api/v1/versions/{version['id']}/preview"
    assert (await client.post(url, json={"updated_content": {"s9999": "x"}}, headers=headers)).status_code == 400
    assert (await client.post(url, json={"updated_content": {sid: "日本語"}}, headers=headers)).status_code == 400


async def test_preview_requires_ownership_and_auth(client, headers, section, upload, register_user):
    version = await upload(section["id"])
    url = f"/api/v1/versions/{version['id']}/preview"
    other = await register_user("other@example.com")
    assert (await client.post(url, json={"updated_content": {}}, headers=other)).status_code == 403
    assert (await client.post(url, json={"updated_content": {}})).status_code == 401


async def test_version_quota_allows_exactly_the_configured_number(client, headers, section, upload, monkeypatch, make_pdf):
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_VERSIONS_PER_SECTION", 3)
    for _ in range(3):
        await upload(section["id"])
    files = {"file": ("r.pdf", make_pdf(), "application/pdf")}
    assert (await client.post(f"/api/v1/sections/{section['id']}/versions", files=files, headers=headers)).status_code == 409
