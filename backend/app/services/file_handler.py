from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".pages"}


def extract_text(file_storage) -> str:
    """Visible text of an uploaded document (see extract_document)."""
    return extract_document(file_storage).text


def extract_document(file_storage):
    """Read an uploaded document, keeping only text a person could see.

    Returns hidden_text.Extraction: .text is what gets analyzed, and
    .hidden_runs counts text that was dropped for being invisible (white on
    white, microscopic, off the page, marked hidden), so the tool can tell
    the user. .pages/.txt/.md have no hidden-text check -- Pages files are
    rare and plain text has no styling to hide behind."""
    from app.services.hidden_text import Extraction, docx_visible_text, pdf_visible_text

    filename = file_storage.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: PDF, DOCX, PAGES, TXT, MD")

    raw = file_storage.read()
    if ext == ".pdf":
        return pdf_visible_text(raw)
    if ext == ".docx":
        return docx_visible_text(raw)
    if ext == ".pages":
        from app.services.pages_reader import read_pages
        return Extraction(read_pages(raw))
    return Extraction(raw.decode("utf-8", errors="replace"))


OCR_DPI = 300


def _read_pdf_bytes(data: bytes) -> str:
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        text = page.get_text()
        if not text.strip():
            text = _ocr_page(page)
        pages.append(text)
    return "\n".join(pages)


def _ocr_page(page) -> str:
    import io
    import pytesseract
    from PIL import Image

    pix = page.get_pixmap(dpi=OCR_DPI)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)


def _read_docx_bytes(data: bytes) -> str:
    import io
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


IMAGE_MAX_DIMENSION = 2000
IMAGE_JPEG_QUALITY = 85

_heif_registered = False


def _ensure_heif_opener():
    # Registers HEIC/HEIF decoding with Pillow. Needed because neither Chrome
    # (incl. on Android, where some phones default their camera to HEIC the
    # same way iPhones do) nor most non-Safari browsers can decode HEIC
    # themselves — so a phone photo can reach us in a format the browser that
    # sent it can't even preview. Doing the decode here, server-side, means it
    # works regardless of what the browser could or couldn't do with it.
    global _heif_registered
    if not _heif_registered:
        import pillow_heif
        pillow_heif.register_heif_opener()
        _heif_registered = True


def prepare_image(file_storage) -> bytes:
    """Read an uploaded photo of a document and return normalized JPEG bytes.

    Runs every photo through Pillow regardless of its original format (JPEG,
    PNG, HEIC, WEBP, ...) so the caller always gets back a consistent,
    reasonably-sized JPEG to send to Claude.
    """
    import io
    from PIL import Image, ImageOps

    _ensure_heif_opener()

    raw = file_storage.read()
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        raise ValueError(
            f"Could not read '{file_storage.filename or 'photo'}' as an image. "
            "Try a different photo, or a JPEG/PNG file."
        )

    # Camera photos carry an EXIF orientation tag rather than pre-rotated
    # pixels; bake the correct orientation in now since it won't survive
    # re-encoding otherwise.
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > IMAGE_MAX_DIMENSION:
        img.thumbnail((IMAGE_MAX_DIMENSION, IMAGE_MAX_DIMENSION))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=IMAGE_JPEG_QUALITY)
    return buf.getvalue()
