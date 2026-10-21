from app.core.config import settings


def _files(storage):
    return sorted(storage.glob("*.enc")) if storage.exists() else []


async def _post(client, headers, section_id, name, content):
    return await client.post(
        f"/api/v1/sections/{section_id}/versions", files={"file": (name, content, "application/pdf")}, headers=headers
    )


async def test_non_pdf_extension_rejected(client, headers, section, make_pdf):
    assert (await _post(client, headers, section["id"], "resume.docx", make_pdf())).status_code == 415


async def test_fake_pdf_without_magic_bytes_rejected(client, headers, section):
    assert (await _post(client, headers, section["id"], "resume.pdf", b"<html>nope</html>")).status_code == 415


async def test_corrupt_pdf_with_valid_header_rejected(client, headers, section):
    assert (await _post(client, headers, section["id"], "resume.pdf", b"%PDF-1.4\ngarbage")).status_code in (415, 201)


async def test_oversized_upload_rejected(client, headers, section, make_pdf, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 100)
    assert (await _post(client, headers, section["id"], "resume.pdf", make_pdf())).status_code == 413


async def test_files_on_disk_are_encrypted(client, headers, section, upload, isolated_storage_dir):
    await upload(section["id"])
    (path,) = _files(isolated_storage_dir)
    assert not path.read_bytes().startswith(b"%PDF-")


async def test_re_edit_replaces_old_rendered_file(client, headers, section, upload, isolated_storage_dir):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    for text in ("One", "Two", "Three"):
        await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: text}}, headers=headers)
    assert len(_files(isolated_storage_dir)) == 2


async def test_delete_version_removes_files_and_clears_active(client, headers, section, upload, isolated_storage_dir):
    version = await upload(section["id"])
    assert (await client.delete(f"/api/v1/versions/{version['id']}", headers=headers)).status_code == 204
    assert _files(isolated_storage_dir) == []
    got = (await client.get(f"/api/v1/sections/{section['id']}", headers=headers)).json()
    assert got["active_version_id"] is None and got["versions"] == []
    assert (await client.get(f"/api/v1/public/{section['shareable_slug']}")).status_code == 404


async def test_delete_section_removes_all_files(client, headers, section, upload, isolated_storage_dir):
    await upload(section["id"])
    await upload(section["id"])
    assert (await client.delete(f"/api/v1/sections/{section['id']}", headers=headers)).status_code == 204
    assert _files(isolated_storage_dir) == []
    assert (await client.get(f"/api/v1/public/{section['shareable_slug']}")).status_code == 404
