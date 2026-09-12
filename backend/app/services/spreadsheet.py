"""Reading and writing .csv / .xlsx tables.

Kept separate from file_handler.extract_text() on purpose: that function's
SUPPORTED_EXTENSIONS set is shared by the Contract Analyzer, Batch ATS and Doc
Analyzer, and widening it to spreadsheets would let someone drop a customer
list into the Contract Analyzer and get a confident-sounding nonsense summary
back. Tabular input gets its own door.
"""
import csv
import io
from datetime import date, datetime
from pathlib import Path

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}

# Bounds the work a single request can trigger: the whole table is held in
# memory, echoed back to the browser, and posted again for download.
MAX_ROWS = 5000
MAX_COLUMNS = 60


class TableTooLarge(ValueError):
    pass


def read_table(file_storage):
    """Parse an uploaded spreadsheet into (headers, rows).

    Everything comes back as Python scalars -- str for text, real date/datetime
    for .xlsx date cells (openpyxl decodes those for us, and data_cleaner
    normalizes them to ISO without counting them as a fix, since they were
    never malformed to begin with)."""
    ext = Path(file_storage.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Upload a .csv or .xlsx file.")

    raw = file_storage.read()
    if not raw:
        raise ValueError("That file is empty.")

    headers, rows = _read_xlsx(raw) if ext == ".xlsx" else _read_csv(raw)

    if not headers:
        raise ValueError("Could not find a header row in that file.")
    if len(headers) > MAX_COLUMNS:
        raise TableTooLarge(f"That file has {len(headers)} columns — {MAX_COLUMNS} is the maximum.")
    if len(rows) > MAX_ROWS:
        raise TableTooLarge(f"That file has {len(rows):,} rows — {MAX_ROWS:,} is the maximum.")
    return headers, rows


def _decode(raw: bytes) -> str:
    # Spreadsheets exported from Excel on Windows are routinely cp1252 rather
    # than UTF-8, and a BOM is common either way. Try the likely encodings in
    # order instead of mangling accented names with errors="replace".
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _read_csv(raw: bytes):
    text = _decode(raw)
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel  # single-column files give the sniffer nothing to go on
    reader = csv.reader(io.StringIO(text), dialect)

    headers = []
    for row in reader:
        if any(str(cell).strip() for cell in row):
            headers = [str(cell).strip() for cell in row]
            break

    rows = [row for row in reader if any(str(cell).strip() for cell in row)]
    return _dedupe_headers(headers), rows


def _read_xlsx(raw: bytes):
    from openpyxl import load_workbook

    try:
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError(f"Could not read that .xlsx file: {exc}") from None

    try:
        sheet = workbook.worksheets[0]
        headers = []
        rows = []
        for values in sheet.iter_rows(values_only=True):
            if not any(v is not None and str(v).strip() for v in values):
                continue
            if not headers:
                headers = [str(v).strip() if v is not None else "" for v in values]
                continue
            rows.append(list(values))
    finally:
        workbook.close()

    # read_only mode can report trailing all-empty columns; drop them so the
    # header row doesn't end in a run of "Column 5", "Column 6" placeholders.
    while headers and not headers[-1]:
        headers.pop()
    return _dedupe_headers(headers), rows


def _dedupe_headers(headers):
    """Blank and repeated header cells become distinct, stable names -- the
    cleanup engine keys columns by header, so collisions would silently merge
    two different columns."""
    seen = {}
    result = []
    for index, header in enumerate(headers):
        name = (header or "").strip() or f"Column {index + 1}"
        if name in seen:
            seen[name] += 1
            name = f"{name} ({seen[name]})"
        else:
            seen[name] = 1
        result.append(name)
    return result


def write_table(headers, rows, fmt: str = "csv") -> bytes:
    if fmt == "xlsx":
        return _write_xlsx(headers, rows)
    return _write_csv(headers, rows)


def _write_csv(headers, rows) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if cell is None else cell for cell in row])
    # utf-8-sig so Excel opens accented characters correctly on a double-click
    # instead of showing mojibake.
    return buf.getvalue().encode("utf-8-sig")


def _write_xlsx(headers, rows) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(list(headers))
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(["" if cell is None else cell for cell in row])
    sheet.freeze_panes = "A2"

    for index, header in enumerate(headers, start=1):
        longest = max(
            [len(str(header))] + [len(str(r[index - 1])) for r in rows[:200] if index - 1 < len(r)]
        )
        sheet.column_dimensions[sheet.cell(row=1, column=index).column_letter].width = min(max(longest + 2, 10), 50)

    buf = io.BytesIO()
    workbook.save(buf)
    return buf.getvalue()


def format_for_filename(filename: str) -> str:
    return "xlsx" if Path(filename or "").suffix.lower() == ".xlsx" else "csv"
