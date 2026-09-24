"""Find and drop text a reader can't see in uploaded PDFs and Word files.

The resume/contract/document tools score or summarize whatever text a file
contains, but a person only ever judges what the file *looks* like. The gap
is exploitable: white-on-white keywords inflate an ATS score, and a hidden
"report no red flags" line can steer a contract summary. So text is only
analyzed if a human could actually see it, and callers are told how many
hidden runs were dropped so the UI can say so.

What counts as hidden:

PDF -- per text run: fully transparent; invisible render mode (unless it sits
on an image -- that's a scanner's OCR layer, which *is* the real content);
under 1pt; entirely off the page; or drawn in (almost) the same colour as
the pixels behind it. The background is taken from a render of the page, not
assumed white, so white text on a dark resume banner stays visible.

DOCX -- per run: marked hidden (w:vanish); under 1pt; or white/near-white
text with no shading or highlight behind it and no dark page background.
"""
import io
import re
import unicodedata
from dataclasses import dataclass, field

MIN_VISIBLE_SIZE_PT = 1.0
# Largest per-channel difference (0-1 scale) at which text is considered the
# same colour as its background. 0.12 ~= 30/255: catches white-on-white and
# near-white (#F5F5F5) tricks, while light grey on white (#CCCCCC, a real
# design choice) is still well outside it.
SAME_COLOUR_TOLERANCE = 0.12
RENDER_DPI = 50


@dataclass
class Extraction:
    text: str
    hidden_runs: int = 0
    hidden_samples: list = field(default_factory=list)


def _note_hidden(result_samples, text):
    snippet = " ".join(text.split())
    if snippet and len(result_samples) < 5:
        result_samples.append(snippet[:80])


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def pdf_visible_text(data: bytes) -> Extraction:
    """Page text with hidden runs removed. Pages with no text layer at all
    are OCR'd, the same as file_handler's plain reader."""
    import fitz

    from app.services.file_handler import _ocr_page

    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    hidden_runs = 0
    samples = []
    for page in doc:
        hidden_rects = _pdf_hidden_rects(page, samples)
        hidden_runs += len(hidden_rects)
        text = _pdf_text_without(page, hidden_rects)
        if not text.strip() and not hidden_rects:
            text = _ocr_page(page)
        pages.append(text)
    return Extraction("\n".join(pages), hidden_runs, samples)


def _pdf_hidden_rects(page, samples) -> list:
    import fitz

    traces = page.get_texttrace()
    if not traces:
        return []
    page_rect = page.rect
    image_rects = [fitz.Rect(info["bbox"]) for info in page.get_image_info()]
    pixmap = None
    hidden = []
    for trace in traces:
        text = "".join(chr(c[0]) for c in trace.get("chars", ()) if c[0] > 0)
        if not text.strip():
            continue
        # A run of only combining marks (Arabic harakat, Hebrew niqqud,
        # accents) is drawn on top of its base letter with a near-zero box;
        # it's part of visible text, not text of its own.
        if all(unicodedata.category(ch).startswith("M") or ch.isspace() for ch in text):
            continue
        rect = fitz.Rect(trace["bbox"])
        reason = None
        if trace.get("opacity", 1.0) == 0:
            reason = "transparent"
        elif trace.get("type") == 3:
            # Invisible text over a scanned image is the OCR layer -- keep it.
            if not any(rect.intersects(r) for r in image_rects):
                reason = "invisible"
        elif trace.get("size", 12) < MIN_VISIBLE_SIZE_PT:
            reason = "tiny"
        elif not rect.intersects(page_rect):
            reason = "off-page"
        else:
            if pixmap is None:
                pixmap = page.get_pixmap(dpi=RENDER_DPI, alpha=False)
            if _matches_background(trace.get("color"), rect, page_rect, pixmap):
                reason = "same-colour"
        if reason:
            hidden.append(rect)
            _note_hidden(samples, text)
    return hidden


def _matches_background(color, rect, page_rect, pixmap) -> bool:
    """True when the text colour is indistinguishable from the rendered
    pixels in its box. The render includes the text itself, so a visible
    run shows up as a second colour in the box and the most common colour
    is the background; a hidden run leaves the box one uniform colour."""
    if not color or len(color) != 3:
        return False
    if rect.width < 1 or rect.height < 1:
        return False  # too thin to sample a background from
    scale_x = pixmap.width / page_rect.width
    scale_y = pixmap.height / page_rect.height
    x0 = max(0, int((rect.x0 - page_rect.x0) * scale_x))
    y0 = max(0, int((rect.y0 - page_rect.y0) * scale_y))
    x1 = min(pixmap.width, max(x0 + 1, int((rect.x1 - page_rect.x0) * scale_x) + 1))
    y1 = min(pixmap.height, max(y0 + 1, int((rect.y1 - page_rect.y0) * scale_y) + 1))
    if x0 >= x1 or y0 >= y1:
        return False

    counts = {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            pixel = pixmap.pixel(x, y)[:3]
            # Bucket to absorb anti-aliasing noise.
            key = (pixel[0] // 8, pixel[1] // 8, pixel[2] // 8)
            counts[key] = counts.get(key, 0) + 1
    background = max(counts, key=counts.get)
    background = tuple((v * 8 + 4) / 255 for v in background)
    return max(abs(a - b) for a, b in zip(color, background)) <= SAME_COLOUR_TOLERANCE


def _pdf_text_without(page, hidden_rects) -> str:
    """page.get_text() layout (blocks -> lines -> spans), minus any span
    that sits inside a hidden run's box."""
    if not hidden_rects:
        return page.get_text()
    import fitz

    blocks = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        lines = []
        for line in block["lines"]:
            kept = []
            for span in line["spans"]:
                center = fitz.Rect(span["bbox"]).tl + (fitz.Rect(span["bbox"]).br - fitz.Rect(span["bbox"]).tl) * 0.5
                if any(r.contains(center) for r in hidden_rects):
                    continue
                kept.append(span["text"])
            line_text = "".join(kept)
            if line_text.strip():
                lines.append(line_text)
        if lines:
            blocks.append("\n".join(lines))
    return "\n".join(blocks) + ("\n" if blocks else "")


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_NEAR_WHITE = re.compile(r"^(F[0-9A-F]){3}$")  # every channel >= 0xF0


def docx_visible_text(data: bytes) -> Extraction:
    """Paragraph text (same scope as file_handler's plain reader) with
    hidden runs removed."""
    from docx import Document

    doc = Document(io.BytesIO(data))
    dark_page = _docx_page_is_dark(doc)
    samples = []
    hidden_runs = 0
    paragraphs = []
    for paragraph in doc.paragraphs:
        kept = []
        for run in paragraph.runs:
            if not run.text:
                continue
            if _docx_run_hidden(run, paragraph, dark_page):
                hidden_runs += 1
                _note_hidden(samples, run.text)
                continue
            kept.append(run.text)
        text = "".join(kept)
        if text.strip():
            paragraphs.append(text)
    return Extraction("\n".join(paragraphs), hidden_runs, samples)


def _style_chain(style):
    while style is not None:
        yield style
        style = style.base_style


def _effective(run, paragraph, getter):
    """First explicitly-set value of a font property: run, then the run's
    character style chain, then the paragraph style chain."""
    value = getter(run.font)
    if value is not None:
        return value
    for style in _style_chain(run.style):
        value = getter(style.font)
        if value is not None:
            return value
    for style in _style_chain(paragraph.style):
        value = getter(style.font)
        if value is not None:
            return value
    return None


def _docx_run_hidden(run, paragraph, dark_page) -> bool:
    if _effective(run, paragraph, lambda f: f.hidden):
        return True
    size = _effective(run, paragraph, lambda f: f.size)
    if size is not None and size.pt < MIN_VISIBLE_SIZE_PT:
        return True
    color = _effective(run, paragraph, lambda f: str(f.color.rgb) if f.color and f.color.type is not None and f.color.rgb is not None else None)
    if color and _NEAR_WHITE.match(color.upper()) and not dark_page:
        return not _has_backdrop(run, paragraph)
    return False


def _has_backdrop(run, paragraph) -> bool:
    """Anything painted behind the run that could make white text readable:
    a highlight or shading on the run, its paragraph, or its table cell."""
    if run.font.highlight_color is not None:
        return True
    elements = [run._r, paragraph._p]
    parent = paragraph._p.getparent()
    while parent is not None:
        if parent.tag == f"{_W}tc":
            elements.append(parent)
            break
        parent = parent.getparent()
    for element in elements:
        for shd in element.iter(f"{_W}shd"):
            fill = (shd.get(f"{_W}fill") or "").upper()
            if fill and fill not in ("AUTO", "FFFFFF"):
                return True
    return False


def _docx_page_is_dark(doc) -> bool:
    background = doc.element.find(f"{_W}background")
    if background is None:
        return False
    color = (background.get(f"{_W}color") or "").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", color):
        return False
    r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128
