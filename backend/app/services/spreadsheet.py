"""Reading and writing .csv / .xlsx / .numbers tables.

Kept separate from file_handler.extract_text() on purpose: that function's
SUPPORTED_EXTENSIONS set is shared by the Contract Analyzer, Batch ATS and Doc
Analyzer, and widening it to spreadsheets would let someone drop a customer
list into the Contract Analyzer and get a confident-sounding nonsense summary
back. Tabular input gets its own door.
"""
import csv
import io
import math
from datetime import date, datetime
from pathlib import Path

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".numbers"}

# Bounds the work a single request can trigger: the whole table is held in
# memory, echoed back to the browser, and posted again for download.
MAX_ROWS = 5000
MAX_COLUMNS = 60


class TableTooLarge(ValueError):
    pass


def read_table(file_storage):
    """Parse an uploaded spreadsheet into (headers, rows).

    Everything comes back as Python scalars -- str for text, real date/datetime
    for .xlsx and .numbers date cells (openpyxl / numbers-parser decode those
    for us, and data_cleaner normalizes them to ISO without counting them as a
    fix, since they were never malformed to begin with)."""
    ext = Path(file_storage.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Upload a .csv, .xlsx or .numbers file.")

    raw = file_storage.read()
    if not raw:
        raise ValueError("That file is empty.")

    if ext == ".xlsx":
        headers, rows = _read_xlsx(raw)
    elif ext == ".numbers":
        headers, rows = _read_numbers(raw)
    else:
        headers, rows = _read_csv(raw)

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


def _read_numbers(raw: bytes):
    """Apple Numbers. Mac and iPhone users have no Excel by default, so this is
    the format their spreadsheets are actually in. numbers-parser needs a real
    path, and the first table on the first sheet is the one people mean."""
    import tempfile

    from numbers_parser import Document

    try:
        with tempfile.NamedTemporaryFile(suffix=".numbers") as tmp:
            tmp.write(raw)
            tmp.flush()
            document = Document(tmp.name)
            table = document.sheets[0].tables[0]
            grid = [list(row) for row in table.rows(values_only=True)]
    except Exception as exc:
        raise ValueError(f"Could not read that .numbers file: {exc}") from None

    headers = []
    rows = []
    for values in grid:
        if not any(v is not None and str(v).strip() for v in values):
            continue
        if not headers:
            headers = [str(v).strip() if v is not None else "" for v in values]
            continue
        rows.append([_tidy_number(v) for v in values])

    # A Numbers table is a fixed grid, so the blank cells to the right of the
    # data always come through; trim them the same way the .xlsx reader does.
    while headers and not headers[-1]:
        headers.pop()
    return _dedupe_headers(headers), rows


def _tidy_number(value):
    """numbers-parser hands every numeric cell back as a float, artefacts
    included (12.5 arrives as 12.500000000000002). openpyxl gives int for
    whole numbers, and the cleaner works in text, so line the two up or a
    Qty of 3 reads "3.0" from Numbers and "3" from Excel."""
    if isinstance(value, float) and math.isfinite(value):
        value = float(f"{value:.15g}")
        if value.is_integer():
            return int(value)
    return value


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


WRITE_FORMATS = {
    "csv": ("text/csv", "csv"),
    "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    "numbers": ("application/vnd.apple.numbers", "numbers"),
}


def write_table(headers, rows, fmt: str = "csv") -> bytes:
    if fmt == "xlsx":
        return _write_xlsx(headers, rows)
    if fmt == "numbers":
        return _write_numbers(headers, rows)
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


def _write_numbers(headers, rows) -> bytes:
    """Native Apple Numbers output, so a client who uploaded a .numbers file
    gets a .numbers file back rather than an Excel file with a strange icon.

    The table is sized to the data exactly (no blank 12x8 default grid), row 1
    is a real Numbers header row, and there's no header column -- the first
    column is ordinary data, not row labels."""
    import tempfile

    from numbers_parser import Document

    document = Document(
        sheet_name="Sheet 1", table_name="Table 1",
        num_header_rows=1, num_header_cols=0,
        num_rows=len(rows) + 1, num_cols=max(len(headers), 1),
    )
    table = document.sheets[0].tables[0]
    for col, header in enumerate(headers):
        table.write(0, col, str(header))
    for row_index, row in enumerate(rows, start=1):
        for col, cell in enumerate(row[:len(headers)]):
            if cell is None or cell == "":
                continue  # an untouched cell is already blank
            table.write(row_index, col, _numbers_cell(cell))

    # Numbers stores widths in points; roughly 7pt per character, same
    # heuristic as the .xlsx writer's column sizing.
    for col, header in enumerate(headers):
        longest = max(
            [len(str(header))] + [len(str(r[col])) for r in rows[:200] if col < len(r)]
        )
        table.col_width(col, min(max(longest * 7 + 16, 70), 350))

    with tempfile.NamedTemporaryFile(suffix=".numbers") as tmp:
        document.save(tmp.name)
        return Path(tmp.name).read_bytes()


def _numbers_cell(cell):
    """numbers-parser accepts str, int, float, bool, datetime and timedelta.
    Anything else (a date without a time, Decimal, ...) goes in as text."""
    if isinstance(cell, datetime):
        return cell
    if isinstance(cell, date):
        return datetime(cell.year, cell.month, cell.day)
    if isinstance(cell, (bool, int, float, str)):
        return cell
    return str(cell)


def format_for_filename(filename: str) -> str:
    """Download format for a cleaned file: whatever the client uploaded, so a
    Numbers user gets Numbers back and an Excel user gets Excel."""
    ext = Path(filename or "").suffix.lower()
    if ext == ".xlsx":
        return "xlsx"
    if ext == ".numbers":
        return "numbers"
    return "csv"
