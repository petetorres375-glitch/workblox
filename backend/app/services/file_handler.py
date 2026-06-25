from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def extract_text(file_storage) -> str:
    filename = file_storage.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: PDF, TXT, MD")

    raw = file_storage.read()
    if ext == ".pdf":
        return _read_pdf_bytes(raw)
    return raw.decode("utf-8", errors="replace")


def _read_pdf_bytes(data: bytes) -> str:
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)
