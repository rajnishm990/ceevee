import fitz

from app.services.pdf_engine import extract_layout, render_pdf


def _make_pdf_with_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), text, fontsize=14)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_extract_layout_finds_text_span():
    original = _make_pdf_with_text("Senior Backend Engineer")
    layout = extract_layout(original)
    assert list(layout["content"].values()) == ["Senior Backend Engineer"]
    assert len(layout["coordinate_map"]) == 1


def test_render_pdf_replaces_text_in_place():
    original = _make_pdf_with_text("Senior Backend Engineer")
    layout = extract_layout(original)
    span_id = next(iter(layout["content"]))
    edited_content = {span_id: "Staff Backend Engineer"}

    rendered = render_pdf(original, layout["coordinate_map"], edited_content)

    doc = fitz.open(stream=rendered, filetype="pdf")
    page_text = doc[0].get_text()
    doc.close()

    assert "Staff Backend Engineer" in page_text
    assert "Senior Backend Engineer" not in page_text
