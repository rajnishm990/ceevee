import fitz

from app.core.config import settings


def _text(pdf_bytes: bytes) -> str:
    return fitz.open(stream=pdf_bytes, filetype="pdf")[0].get_text()


def _files(storage):
    return sorted(storage.glob("*.enc")) if storage.exists() else []


async def _fork(client, headers, version, text, **extra):
    sid = next(iter(version["content"]))
    return await client.post(
        f"/api/v1/versions/{version['id']}/fork", json={"updated_content": {sid: text}, **extra}, headers=headers
    )


async def test_fork_creates_next_version_and_leaves_source_untouched(client, headers, section, upload):
    v1 = await upload(section["id"])
    resp = await _fork(client, headers, v1, "Senior Backend Engineer")
    assert resp.status_code == 201
    v2 = resp.json()
    assert v2["version_number"] == 2 and v2["revision"] == 1 and v2["label"] == "Edited from v1"
    assert v2["id"] != v1["id"]
    again = (await client.get(f"/api/v1/versions/{v1['id']}", headers=headers)).json()
    assert again["content"] == v1["content"] and again["revision"] == 1
    original = await client.get(f"/api/v1/versions/{v1['id']}/download", headers=headers)
    assert "Junior Backend Engineer" in _text(original.content)


async def test_fork_becomes_active_and_the_same_share_link_serves_it(client, headers, section, upload):
    v1 = await upload(section["id"])
    url = f"/api/v1/public/{section['shareable_slug']}"
    assert "Junior Backend Engineer" in _text((await client.get(url)).content)
    v2 = (await _fork(client, headers, v1, "Senior Backend Engineer")).json()
    got = (await client.get(f"/api/v1/sections/{section['id']}", headers=headers)).json()
    assert got["active_version_id"] == v2["id"] and len(got["versions"]) == 2
    assert "Senior Backend Engineer" in _text((await client.get(url)).content)


async def test_fork_can_leave_the_active_version_alone(client, headers, section, upload):
    v1 = await upload(section["id"])
    await _fork(client, headers, v1, "Draft title", make_active=False)
    got = (await client.get(f"/api/v1/sections/{section['id']}", headers=headers)).json()
    assert got["active_version_id"] == v1["id"] and len(got["versions"]) == 2


async def test_custom_label_is_used(client, headers, section, upload):
    v1 = await upload(section["id"])
    assert (await _fork(client, headers, v1, "X", label="For Stripe")).json()["label"] == "For Stripe"


async def test_deleting_the_source_does_not_break_the_fork(client, headers, section, upload):
    v1 = await upload(section["id"])
    v2 = (await _fork(client, headers, v1, "Kept")).json()
    assert (await client.delete(f"/api/v1/versions/{v1['id']}", headers=headers)).status_code == 204
    cur = await client.get(f"/api/v1/versions/{v2['id']}/download", headers=headers)
    orig = await client.get(f"/api/v1/versions/{v2['id']}/download?source=original", headers=headers)
    assert "Kept" in _text(cur.content) and "Junior Backend Engineer" in _text(orig.content)
    edit = await client.post(f"/api/v1/versions/{v2['id']}/preview", json={"updated_content": {next(iter(v2["content"])): "Still editable"}}, headers=headers)
    assert edit.status_code == 200


async def test_forking_a_fork_chains_correctly(client, headers, section, upload):
    v1 = await upload(section["id"])
    v2 = (await _fork(client, headers, v1, "Second")).json()
    v3 = (await _fork(client, headers, v2, "Third")).json()
    assert v3["version_number"] == 3 and v3["label"] == "Edited from v2"
    assert "Third" in _text((await client.get(f"/api/v1/versions/{v3['id']}/download", headers=headers)).content)
    assert "Second" in _text((await client.get(f"/api/v1/versions/{v2['id']}/download", headers=headers)).content)


async def test_fork_respects_the_version_quota_and_creates_nothing(client, headers, section, upload, monkeypatch, isolated_storage_dir):
    monkeypatch.setattr(settings, "MAX_VERSIONS_PER_SECTION", 2)
    v1 = await upload(section["id"])
    await upload(section["id"])
    before = _files(isolated_storage_dir)
    assert (await _fork(client, headers, v1, "Over quota")).status_code == 409
    assert _files(isolated_storage_dir) == before


async def test_failed_fork_leaves_no_row_and_no_blob(client, headers, section, upload, isolated_storage_dir):
    v1 = await upload(section["id"])
    before = _files(isolated_storage_dir)
    assert (await _fork(client, headers, v1, "日本語")).status_code == 400
    assert (await client.post(f"/api/v1/versions/{v1['id']}/fork", json={"updated_content": {"s9999": "x"}}, headers=headers)).status_code == 400
    assert _files(isolated_storage_dir) == before
    assert len((await client.get(f"/api/v1/sections/{section['id']}", headers=headers)).json()["versions"]) == 1


async def test_fork_blobs_are_encrypted_and_independent(client, headers, section, upload, isolated_storage_dir):
    v1 = await upload(section["id"])
    await _fork(client, headers, v1, "Two")
    files = _files(isolated_storage_dir)
    assert len(files) == 3 and all(not f.read_bytes().startswith(b"%PDF-") for f in files)


async def test_fork_requires_ownership_and_auth(client, headers, section, upload, register_user):
    v1 = await upload(section["id"])
    other = await register_user("other@example.com")
    sid = next(iter(v1["content"]))
    url = f"/api/v1/versions/{v1['id']}/fork"
    assert (await client.post(url, json={"updated_content": {sid: "x"}}, headers=other)).status_code == 403
    assert (await client.post(url, json={"updated_content": {sid: "x"}})).status_code == 401


async def test_fork_with_no_changes_still_creates_an_identical_copy(client, headers, section, upload):
    v1 = await upload(section["id"])
    v2 = (await client.post(f"/api/v1/versions/{v1['id']}/fork", json={"updated_content": {}}, headers=headers)).json()
    assert v2["content"] == v1["content"] and v2["version_number"] == 2


async def test_deleting_the_active_fork_clears_the_pointer(client, headers, section, upload):
    v1 = await upload(section["id"])
    v2 = (await _fork(client, headers, v1, "Active one")).json()
    await client.delete(f"/api/v1/versions/{v2['id']}", headers=headers)
    assert (await client.get(f"/api/v1/sections/{section['id']}", headers=headers)).json()["active_version_id"] is None
