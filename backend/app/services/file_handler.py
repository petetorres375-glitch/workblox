from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def extract_text(file_storage) -> str:
    filename = file_storage.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: PDF, DOCX, TXT, MD")

    raw = file_storage.read()
    if ext == ".pdf":
        return _read_pdf_bytes(raw)
    if ext == ".docx":
        return _read_docx_bytes(raw)
    return raw.decode("utf-8", errors="replace")


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
