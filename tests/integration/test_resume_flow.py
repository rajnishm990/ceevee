import fitz


def _tiny_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), text, fontsize=14)
    data = doc.tobytes()
    doc.close()
    return data


async def _auth_headers(client, email="flow@example.com", password="supersecret123"):
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_full_resume_flow(client):
    """Registers a user, creates a section, uploads a resume, edits it, and
    confirms the public share link serves the edited PDF - i.e. the whole
    loop this project is built around."""
    headers = await _auth_headers(client)

    section_resp = await client.post("/api/v1/sections", json={"domain_name": "backend"}, headers=headers)
    assert section_resp.status_code == 201
    section = section_resp.json()

    pdf_bytes = _tiny_pdf("Junior Backend Engineer")
    files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    version_resp = await client.post(f"/api/v1/sections/{section['id']}/versions", files=files, headers=headers)
    assert version_resp.status_code == 201
    version = version_resp.json()

    span_id = next(iter(version["content"]))
    edit_resp = await client.patch(
        f"/api/v1/versions/{version['id']}",
        json={"updated_content": {span_id: "Senior Backend Engineer"}},
        headers=headers,
    )
    assert edit_resp.status_code == 200

    public_resp = await client.get(f"/api/v1/public/{section['shareable_slug']}")
    assert public_resp.status_code == 200
    assert public_resp.headers["content-type"] == "application/pdf"

    doc = fitz.open(stream=public_resp.content, filetype="pdf")
    text = doc[0].get_text()
    doc.close()
    assert "Senior Backend Engineer" in text
