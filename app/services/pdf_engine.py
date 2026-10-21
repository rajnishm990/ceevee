from typing import Any, Dict, List, Tuple

import fitz

_FONT_FAMILIES = {
    "sans": ("helv", "hebo", "heit", "hebi"),
    "serif": ("tiro", "tibo", "tiit", "tibi"),
    "mono": ("cour", "cobo", "coit", "cobi"),
}
_SERIF_HINTS = ("times", "georgia", "garamond", "cambria", "palatino", "minion")
_RIGHT_MARGIN = 36.0
_NEIGHBOUR_GAP = 6.0


class PdfReadError(Exception):
    pass


def pick_font(flags: int, font_name: str) -> str:
    name = font_name.lower()
    if flags & 8 or "mono" in name or "courier" in name:
        family = "mono"
    elif flags & 4 or any(h in name for h in _SERIF_HINTS):
        family = "serif"
    else:
        family = "sans"
    bold = bool(flags & 16) or "bold" in name
    italic = bool(flags & 2) or "italic" in name or "oblique" in name
    index = 3 if bold and italic else 1 if bold else 2 if italic else 0
    return _FONT_FAMILIES[family][index]


def extract_layout(pdf_bytes: bytes) -> Dict[str, Any]:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise PdfReadError("Could not read this PDF.") from exc

    try:
        if doc.needs_pass:
            raise PdfReadError("Password-protected PDFs are not supported.")

        coordinate_map: Dict[str, Any] = {}
        content: Dict[str, str] = {}
        page_info: List[Dict[str, float]] = []
        counter = 0

        for page_index in range(len(doc)):
            page = doc[page_index]
            page_info.append({"width": page.rect.width, "height": page.rect.height})
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        if not span["text"].strip():
                            continue
                        counter += 1
                        span_id = f"s{counter:04d}"
                        coordinate_map[span_id] = {
                            "page": page_index,
                            "bbox": list(span["bbox"]),
                            "origin": list(span["origin"]),
                            "font": span["font"],
                            "flags": span["flags"],
                            "size": span["size"],
                            "color": span["color"],
                            "text": span["text"],
                        }
                        content[span_id] = span["text"]
    finally:
        doc.close()

    return {"coordinate_map": coordinate_map, "content": content, "page_info": page_info}


def render_pdf(base_pdf_bytes: bytes, coordinate_map: Dict[str, Any], content: Dict[str, str]) -> bytes:
    changed = [
        (span_id, meta, content[span_id])
        for span_id, meta in coordinate_map.items()
        if span_id in content and content[span_id] != meta.get("text")
    ]
    if not changed:
        return base_pdf_bytes

    doc = fitz.open(stream=base_pdf_bytes, filetype="pdf")
    try:
        pages = set()
        for _, meta, _ in changed:
            x0, y0, x1, y1 = meta["bbox"]
            inset = (y1 - y0) * 0.2
            rect = fitz.Rect(x0, y0 + inset, x1, y1 - inset)
            doc[meta["page"]].add_redact_annot(rect, fill=False)
            pages.add(meta["page"])

        for page_index in pages:
            doc[page_index].apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_NONE,
            )

        for span_id, meta, new_text in changed:
            page = doc[meta["page"]]
            font = pick_font(meta["flags"], meta["font"])
            max_width = _available_width(span_id, meta, coordinate_map, page.rect.width)
            size = _fit_font_size(new_text, font, meta["size"], max_width)
            page.insert_text(
                tuple(meta["origin"]),
                new_text,
                fontsize=size,
                color=_unpack_color(meta["color"]),
                fontname=font,
            )

        return doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()


def _available_width(span_id: str, meta: Dict[str, Any], coordinate_map: Dict[str, Any], page_width: float) -> float:
    x0, y0, x1, y1 = meta["bbox"]
    height = y1 - y0
    limit = page_width - _RIGHT_MARGIN
    for other_id, other in coordinate_map.items():
        if other_id == span_id or other["page"] != meta["page"]:
            continue
        ox0, oy0, _, oy1 = other["bbox"]
        overlap = min(y1, oy1) - max(y0, oy0)
        if overlap > height * 0.5 and ox0 >= x1 - 1:
            limit = min(limit, ox0 - _NEIGHBOUR_GAP)
    return max(x1 - x0, limit - x0)


def _fit_font_size(text: str, font: str, size: float, max_width: float, min_size: float = 6.0) -> float:
    width = fitz.get_text_length(text, fontname=font, fontsize=size)
    if width <= max_width or width == 0:
        return size
    return max(min_size, size * max_width / width)


def _unpack_color(color_int: int) -> Tuple[float, float, float]:
    return (((color_int >> 16) & 255) / 255, ((color_int >> 8) & 255) / 255, (color_int & 255) / 255)
