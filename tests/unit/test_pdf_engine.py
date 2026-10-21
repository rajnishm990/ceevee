import fitz
import pytest

from app.services.pdf_engine import PdfReadError, extract_layout, pick_font, render_pdf


def _pdf(draw) -> bytes:
    doc = fitz.open()
    draw(doc.new_page())
    data = doc.tobytes()
    doc.close()
    return data


def _spans(pdf_bytes: bytes):
    page = fitz.open(stream=pdf_bytes, filetype="pdf")[0]
    return {s["text"]: s for b in page.get_text("dict")["blocks"] for ln in b["lines"] for s in ln["spans"]}


def _id_of(layout, text):
    return next(k for k, v in layout["content"].items() if v == text)


def test_extract_layout_records_geometry_and_pages():
    pdf = _pdf(lambda p: p.insert_text((72, 100), "Senior Backend Engineer", fontsize=14))
    layout = extract_layout(pdf)
    assert list(layout["content"].values()) == ["Senior Backend Engineer"]
    meta = next(iter(layout["coordinate_map"].values()))
    assert meta["text"] == "Senior Backend Engineer" and meta["origin"] and "flags" in meta
    assert layout["page_info"] == [{"width": 595.0, "height": 842.0}]


def test_render_replaces_text():
    pdf = _pdf(lambda p: p.insert_text((72, 100), "Senior Backend Engineer", fontsize=14))
    layout = extract_layout(pdf)
    sid = next(iter(layout["content"]))
    out = render_pdf(pdf, layout["coordinate_map"], {sid: "Staff Backend Engineer"})
    text = fitz.open(stream=out, filetype="pdf")[0].get_text()
    assert "Staff Backend Engineer" in text and "Senior Backend Engineer" not in text


def test_unchanged_content_returns_original_bytes():
    pdf = _pdf(lambda p: p.insert_text((72, 100), "Hello", fontsize=14))
    layout = extract_layout(pdf)
    assert render_pdf(pdf, layout["coordinate_map"], layout["content"]) == pdf


def test_only_changed_span_is_repainted():
    def draw(p):
        p.insert_text((72, 100), "Title", fontsize=14, fontname="hebo")
        p.insert_text((72, 130), "Untouched line", fontsize=12, fontname="tiro")

    pdf = _pdf(draw)
    layout = extract_layout(pdf)
    out = render_pdf(pdf, layout["coordinate_map"], {**layout["content"], _id_of(layout, "Title"): "New Title"})
    spans = _spans(out)
    assert spans["Untouched line"]["font"] == "Times-Roman"
    assert spans["New Title"]["font"] == "Helvetica-Bold"


@pytest.mark.parametrize("size,gap", [(11, 14), (12, 13), (10, 12)])
def test_adjacent_lines_survive_an_edit(size, gap):
    pdf = _pdf(lambda p: [p.insert_text((72, 100 + i * gap), f"Line {i}", fontsize=size) for i in range(3)])
    layout = extract_layout(pdf)
    out = render_pdf(pdf, layout["coordinate_map"], {_id_of(layout, "Line 1"): "Edited"})
    assert {"Line 0", "Edited", "Line 2"} <= set(_spans(out))


def test_background_colour_is_preserved():
    def draw(p):
        p.draw_rect(fitz.Rect(50, 80, 400, 120), color=None, fill=(0.2, 0.5, 0.9))
        p.insert_text((60, 100), "On blue", fontsize=14, color=(1, 1, 1))

    pdf = _pdf(draw)
    layout = extract_layout(pdf)
    out = render_pdf(pdf, layout["coordinate_map"], {next(iter(layout["content"])): "Changed on blue"})
    r, g, b = fitz.open(stream=out, filetype="pdf")[0].get_pixmap().pixel(55, 85)
    assert (r, g, b) != (255, 255, 255) and b > r


def test_long_text_does_not_run_into_right_neighbour():
    def draw(p):
        p.insert_text((72, 100), "Title", fontsize=14)
        p.insert_text((400, 100), "2020-2024", fontsize=14)

    pdf = _pdf(draw)
    layout = extract_layout(pdf)
    out = render_pdf(pdf, layout["coordinate_map"], {_id_of(layout, "Title"): "A much longer replacement title here"})
    spans = _spans(out)
    assert spans["A much longer replacement title here"]["bbox"][2] <= spans["2020-2024"]["bbox"][0]


@pytest.mark.parametrize(
    "flags,name,expected",
    [(0, "Arial", "helv"), (16, "Arial-Bold", "hebo"), (2, "Arial-Italic", "heit"),
     (4, "Whatever", "tiro"), (16 | 4, "X", "tibo"), (8, "Consolas", "cour"), (0, "Times-Roman", "tiro")],
)
def test_pick_font(flags, name, expected):
    assert pick_font(flags, name) == expected


def test_garbage_bytes_raise_pdf_read_error():
    with pytest.raises(PdfReadError):
        extract_layout(b"not a pdf at all")
