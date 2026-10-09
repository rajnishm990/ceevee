from typing import Any, Dict, Tuple

import fitz  # PyMuPDF


def extract_layout(pdf_bytes: bytes) -> Dict[str, Any]:
    """Returns {"coordinate_map": {...}, "content": {...}}."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    coordinate_map: Dict[str, Any] = {}
    content: Dict[str, str] = {}

    try:
        span_counter = 0
        for page_index in range(len(doc)):
            page = doc[page_index]
            raw = page.get_text("dict")
            for block in raw["blocks"]:
                if block.get("type") != 0:  # 0 = text block, 1 = image block
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        if not text.strip():
                            continue
                        span_counter += 1
                        span_id = f"s{span_counter:04d}"
                        coordinate_map[span_id] = {
                            "page": page_index,
                            "bbox": list(span["bbox"]),
                            "font": span["font"],
                            "size": span["size"],
                            "color": span["color"],
                        }
                        content[span_id] = text
    finally:
        doc.close()

    return {"coordinate_map": coordinate_map, "content": content}


def render_pdf(base_pdf_bytes: bytes, coordinate_map: Dict[str, Any], content: Dict[str, str]) -> bytes:
    """Applies `content` on top of the ORIGINAL `base_pdf_bytes`, using the
    positions recorded in `coordinate_map`. Only spans present in `content`
    with different text than what's already there get touched."""
    doc = fitz.open(stream=base_pdf_bytes, filetype="pdf")
    try:
        pages_touched = set()
        spans_to_redraw = []

        for span_id, meta in coordinate_map.items():
            new_text = content.get(span_id)
            if new_text is None:
                continue
            page_index = meta["page"]
            rect = fitz.Rect(meta["bbox"])
            doc[page_index].add_redact_annot(rect, fill=(1, 1, 1))
            pages_touched.add(page_index)
            spans_to_redraw.append((span_id, meta, new_text))

        for page_index in pages_touched:
            doc[page_index].apply_redactions()

        for span_id, meta, new_text in spans_to_redraw:
            page = doc[meta["page"]]
            x0, y0, x1, y1 = meta["bbox"]
            box_width = x1 - x0
            box_height = y1 - y0
            original_size = meta["size"]
            fontsize = _fit_font_size(new_text, box_width, original_size)
            color = _unpack_color(meta["color"])
            # insert_text's point is the text baseline; approximate it as
            # sitting a little above the bottom of the original box.
            baseline_y = y1 - (box_height * 0.2)
            page.insert_text((x0, baseline_y), new_text, fontsize=fontsize, color=color, fontname="helv")

        return doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()


def _unpack_color(color_int: int) -> Tuple[float, float, float]:
    """PyMuPDF packs RGB as a single int; unpack to the (r, g, b) 0-1 floats
    insert_text wants."""
    r = ((color_int >> 16) & 255) / 255
    g = ((color_int >> 8) & 255) / 255
    b = (color_int & 255) / 255
    return (r, g, b)


def _fit_font_size(text: str, box_width: float, original_size: float, min_size: float = 6.0) -> float:
    """Crude but effective v1 anti-overflow: shrink the font until the
    (estimated) text width fits the original box. 0.5 is a rough average
    glyph-width-to-fontsize ratio for Helvetica; good enough to avoid
    obvious overflow, not pixel-perfect kerning."""
    if not text:
        return original_size
    estimated_width = len(text) * original_size * 0.5
    if estimated_width <= box_width or original_size <= min_size:
        return original_size
    scale = box_width / estimated_width
    return max(min_size, original_size * scale)
