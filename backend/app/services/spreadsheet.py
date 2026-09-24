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
import re
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


def write_table(headers, rows, fmt: str = "csv", title: str = None, money_columns=None) -> bytes:
    """title labels the table inside a .numbers file (Numbers shows it above
    the table); the other formats have no equivalent and ignore it.
    money_columns maps column index -> currency symbol ("$", "€", "£") or
    None; those columns are shown with two decimals and thousands separators
    in .xlsx/.numbers so amounts line up. CSV has no formatting."""
    money_columns = _money_map(money_columns)
    if fmt == "xlsx":
        return _write_xlsx(headers, rows, money_columns)
    if fmt == "numbers":
        return _write_numbers(headers, rows, title, money_columns)
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


def _write_xlsx(headers, rows, money_columns=None) -> bytes:
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
    for col, symbol in (money_columns or {}).items():
        number_format = f'"{symbol}"#,##0.00' if symbol else "#,##0.00"
        for (cell,) in sheet.iter_rows(min_row=2, min_col=col + 1, max_col=col + 1):
            if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                cell.number_format = number_format

    for index, header in enumerate(headers, start=1):
        longest = max(
            [len(str(header))] + [len(str(r[index - 1])) for r in rows[:200] if index - 1 < len(r)]
        )
        sheet.column_dimensions[sheet.cell(row=1, column=index).column_letter].width = min(max(longest + 2, 10), 50)

    buf = io.BytesIO()
    workbook.save(buf)
    return buf.getvalue()


# Brand blue header with white bold text, and a very light blue-grey band on
# every other row so long tables stay easy to follow across the columns.
_NUMBERS_HEADER_BG = (37, 99, 235)
_NUMBERS_HEADER_TEXT = (255, 255, 255)
_NUMBERS_BAND_BG = (243, 246, 251)
_NUMBERS_HEADER_HEIGHT = 28


def _write_numbers(headers, rows, title=None, money_columns=None) -> bytes:
    """Native Apple Numbers output, so a client who uploaded a .numbers file
    gets a .numbers file back rather than an Excel file with a strange icon.

    The table is sized to the data exactly (no blank 12x8 default grid), row 1
    is a real Numbers header row, and there's no header column -- the first
    column is ordinary data, not row labels. Styling is applied through named
    styles, so it shows up in Numbers' own style list rather than as
    per-cell overrides."""
    import tempfile

    from numbers_parser import RGB, Alignment, Document

    num_cols = max(len(headers), 1)
    document = Document(
        sheet_name="Cleaned Data", table_name=(title or "Cleaned Data")[:255],
        num_header_rows=1, num_header_cols=0,
        num_rows=len(rows) + 1, num_cols=num_cols,
    )
    table = document.sheets[0].tables[0]

    # text_wrap off keeps every record on one line; long values are still
    # fully visible in the cell editor and widths below cover most of them.
    header_style = document.add_style(
        name="Workblox Header", bold=True, font_size=12.0,
        font_color=RGB(*_NUMBERS_HEADER_TEXT), bg_color=RGB(*_NUMBERS_HEADER_BG),
        alignment=Alignment("left", "middle"), text_wrap=False,
    )
    body_style = document.add_style(
        name="Workblox Row", alignment=Alignment("auto", "middle"), text_wrap=False,
    )
    band_style = document.add_style(
        name="Workblox Row Alt", bg_color=RGB(*_NUMBERS_BAND_BG),
        alignment=Alignment("auto", "middle"), text_wrap=False,
    )

    for col, header in enumerate(headers):
        table.write(0, col, str(header))
        table.set_cell_style(0, col, header_style)
    table.row_height(0, _NUMBERS_HEADER_HEIGHT)

    for row_index, row in enumerate(rows, start=1):
        for col, cell in enumerate(row[:len(headers)]):
            if cell is not None and cell != "":
                value = _numbers_cell(cell)
                table.write(row_index, col, value)
                if col in money_columns and isinstance(value, (int, float)) and not isinstance(value, bool):
                    currency = _CURRENCY_CODES.get(money_columns[col])
                    if currency:
                        table.set_cell_formatting(
                            row_index, col, "currency", currency_code=currency,
                            decimal_places=2, show_thousands_separator=True,
                        )
                    else:
                        table.set_cell_formatting(
                            row_index, col, "number",
                            decimal_places=2, show_thousands_separator=True,
                        )
        # Style blank cells too, or the banding shows gaps wherever a value
        # was missing.
        style = band_style if row_index % 2 == 0 else body_style
        for col in range(num_cols):
            table.set_cell_style(row_index, col, style)

    # Numbers stores widths in points; roughly 7pt per character, same
    # heuristic as the .xlsx writer's column sizing. The header is measured
    # at its larger bold size so it never gets clipped.
    for col, header in enumerate(headers):
        longest = max(
            [int(len(str(header)) * 1.25)] + [len(str(r[col])) for r in rows[:200] if col < len(r)]
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
    if isinstance(cell, float):
        # numbers-parser keeps 15 significant digits and logs a warning for
        # every value with float noise (3.3000000000000003) -- round first so
        # a large download doesn't flood the server logs.
        return float(f"{cell:.15g}") if math.isfinite(cell) else str(cell)
    if isinstance(cell, (bool, int, str)):
        return cell
    return str(cell)


_CURRENCY_CODES = {"$": "USD", "€": "EUR", "£": "GBP"}

# One amount in US/UK notation: optional sign or accounting parentheses, an
# optional $/€/£, then either plain digits or properly grouped thousands, and
# an optional decimal part. "1.204,00" / "12,5" (comma decimals) deliberately
# don't match -- whether "1,204" means 1204 or 1.204 can't be known, and
# guessing wrong would silently change someone's money.
_MONEY_RE = re.compile(
    r"^(?P<open>\()?\s*(?P<neg1>-)?\s*(?P<sym>[$€£])?\s*(?P<neg2>-)?\s*"
    r"(?P<num>\d{1,3}(?:,\d{3})+|\d+)(?P<dec>\.\d+)?\s*(?P<close>\))?$"
)


def _money_map(money_columns):
    if not money_columns:
        return {}
    if isinstance(money_columns, dict):
        return dict(money_columns)
    return {col: None for col in money_columns}


def _parse_money(text):
    """Return (value, symbol) for an unambiguous amount, else None."""
    match = _MONEY_RE.match(text.strip())
    if not match or bool(match["open"]) != bool(match["close"]):
        return None
    value = float(match["num"].replace(",", "") + (match["dec"] or ""))
    if match["open"] or match["neg1"] or match["neg2"]:
        value = -value
    return value, match["sym"]


def convert_money_columns(headers, rows, column_types):
    """Turn Data Cleanup's text amounts into real numbers for the columns the
    column plan typed as "currency", so they can be formatted and summed.

    All-or-nothing per column: a column converts only if every non-blank
    value parses and at most one currency symbol appears. Otherwise it stays
    exactly as the cleaner left it, so a stray note or a comma-decimal value
    can never be half-converted. Returns (rows, money_columns)."""
    column_types = column_types if isinstance(column_types, dict) else {}
    rows = [list(row) for row in rows]
    money_columns = {}
    for col, header in enumerate(headers):
        if column_types.get(header) != "currency":
            continue
        parsed = {}
        symbols = set()
        for index, row in enumerate(rows):
            cell = row[col] if col < len(row) else None
            if cell is None or (isinstance(cell, str) and not cell.strip()):
                continue
            if isinstance(cell, (int, float)) and not isinstance(cell, bool):
                parsed[index] = float(cell)
                continue
            result = _parse_money(str(cell))
            if result is None:
                parsed = None
                break
            parsed[index] = result[0]
            if result[1]:
                symbols.add(result[1])
        if not parsed or len(symbols) > 1:
            continue
        for index, value in parsed.items():
            rows[index][col] = value
        money_columns[col] = next(iter(symbols), None)
    return rows, money_columns


def format_for_filename(filename: str) -> str:
    """Download format for a cleaned file: the same format that was uploaded,
    so a Numbers user gets a .numbers file back and never sees an Excel icon."""
    ext = Path(filename or "").suffix.lower()
    if ext == ".numbers":
        return "numbers"
    return "xlsx" if ext == ".xlsx" else "csv"
