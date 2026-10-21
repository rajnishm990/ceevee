import fitz


def _text(pdf_bytes: bytes) -> str:
    return fitz.open(stream=pdf_bytes, filetype="pdf")[0].get_text()


async def test_full_resume_flow(client, headers, section, upload):
    version = await upload(section["id"])
    span_id = next(iter(version["content"]))
    edit = await client.patch(
        f"/api/v1/versions/{version['id']}", json={"updated_content": {span_id: "Senior Backend Engineer"}}, headers=headers
    )
    assert edit.status_code == 200
    public = await client.get(f"/api/v1/public/{section['shareable_slug']}")
    assert public.status_code == 200 and public.headers["content-type"] == "application/pdf"
    assert "Senior Backend Engineer" in _text(public.content)


async def test_first_upload_becomes_active_later_ones_do_not(client, headers, section, upload):
    first = await upload(section["id"], ["First"])
    second = await upload(section["id"], ["Second"])
    assert second["version_number"] == 2
    got = (await client.get(f"/api/v1/sections/{section['id']}", headers=headers)).json()
    assert got["active_version_id"] == first["id"]
    assert len(got["versions"]) == 2


async def test_switching_active_version_changes_public_link_but_not_slug(client, headers, section, upload):
    first = await upload(section["id"], ["First resume"])
    second = await upload(section["id"], ["Second resume"])
    url = f"/api/v1/public/{section['shareable_slug']}"
    assert "First resume" in _text((await client.get(url)).content)
    resp = await client.post(f"/api/v1/sections/{section['id']}/active-version", json={"version_id": second["id"]}, headers=headers)
    assert resp.status_code == 200 and resp.json()["shareable_slug"] == section["shareable_slug"]
    assert "Second resume" in _text((await client.get(url)).content)


async def test_cannot_activate_version_from_another_section(client, headers, section, upload):
    other = (await client.post("/api/v1/sections", json={"domain_name": "frontend"}, headers=headers)).json()
    foreign = await upload(other["id"])
    resp = await client.post(f"/api/v1/sections/{section['id']}/active-version", json={"version_id": foreign["id"]}, headers=headers)
    assert resp.status_code == 404


async def test_public_link_404_without_active_version_or_unknown_slug(client, section):
    assert (await client.get(f"/api/v1/public/{section['shareable_slug']}")).status_code == 404
    assert (await client.get("/api/v1/public/does-not-exist")).status_code == 404


async def test_public_response_has_no_cache_and_only_pdf(client, section, upload):
    await upload(section["id"])
    resp = await client.get(f"/api/v1/public/{section['shareable_slug']}")
    assert resp.headers["cache-control"] == "private, no-store"
    assert resp.content.startswith(b"%PDF-")


async def test_unedited_version_serves_original_bytes(client, headers, section, upload, make_pdf):
    version = await upload(section["id"])
    resp = await client.get(f"/api/v1/versions/{version['id']}/download", headers=headers)
    assert resp.status_code == 200 and "Junior Backend Engineer" in _text(resp.content)


async def test_download_original_after_edit(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: "Edited"}}, headers=headers)
    original = await client.get(f"/api/v1/versions/{version['id']}/download?source=original", headers=headers)
    current = await client.get(f"/api/v1/versions/{version['id']}/download", headers=headers)
    assert "Junior Backend Engineer" in _text(original.content)
    assert "Edited" in _text(current.content)


async def test_get_version_returns_editor_payload(client, headers, section, upload):
    version = await upload(section["id"])
    got = (await client.get(f"/api/v1/versions/{version['id']}", headers=headers)).json()
    assert got["content"] and got["coordinate_map"] and got["page_info"][0]["width"] > 0


async def test_active_pdf_endpoint_for_extension(client, headers, section, upload):
    assert (await client.get(f"/api/v1/sections/{section['id']}/active-pdf", headers=headers)).status_code == 404
    await upload(section["id"])
    resp = await client.get(f"/api/v1/sections/{section['id']}/active-pdf", headers=headers)
    assert resp.status_code == 200 and resp.content.startswith(b"%PDF-")


async def test_edit_with_unknown_span_id_rejected(client, headers, section, upload):
    version = await upload(section["id"])
    resp = await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {"s9999": "x"}}, headers=headers)
    assert resp.status_code == 400


async def test_edit_text_too_long_rejected(client, headers, section, upload):
    version = await upload(section["id"])
    sid = next(iter(version["content"]))
    resp = await client.patch(f"/api/v1/versions/{version['id']}", json={"updated_content": {sid: "x" * 501}}, headers=headers)
    assert resp.status_code == 422


async def test_label_update(client, headers, section, upload):
    version = await upload(section["id"])
    resp = await client.patch(f"/api/v1/versions/{version['id']}/label", json={"label": "For Stripe"}, headers=headers)
    assert resp.json()["label"] == "For Stripe"


async def test_gdrive_link_round_trips(client, headers, section):
    resp = await client.patch(f"/api/v1/sections/{section['id']}", json={"gdrive_link": "https://drive.google.com/x"}, headers=headers)
    assert resp.json()["gdrive_link"] == "https://drive.google.com/x"
    listing = (await client.get("/api/v1/sections", headers=headers)).json()
    assert listing[0]["gdrive_link"] == "https://drive.google.com/x"
