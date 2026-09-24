"""Unit tests for the deterministic cleanup engine.

No mocking anywhere in this file on purpose: the engine makes no network calls
and reads no clock, so every one of these asserts an exact, reproducible
outcome. That's the property that lets the UI show a client a hard number.
"""
import io
from pathlib import Path

import pytest

from app.services import spreadsheet
from app.services.data_cleaner import (
    FLAG_AMBIGUOUS_DATE,
    FLAG_DUPLICATE,
    FLAG_UNPARSEABLE_DATE,
    clean_table,
    parse_date,
    resolve_date_order,
)

HEADERS = ["Name", "Email", "Signup Date", "Notes"]


def _flags(result):
    return [meta["flags"] for meta in result["row_meta"]]


# ── Date order resolution ─────────────────────────────────────────────────────

def test_single_unambiguous_value_settles_the_whole_column():
    # 25 can only be a day, so every other row in this column is D/M/Y too.
    assert resolve_date_order(["03/04/2024", "25/03/2024", "01/02/2024"]) == "dmy"


def test_day_over_twelve_in_first_position_means_mdy():
    assert resolve_date_order(["04/25/2024", "03/04/2024"]) == "mdy"


def test_column_with_no_evidence_is_undecidable():
    assert resolve_date_order(["03/04/2024", "05/06/2024"]) == "unknown"


def test_contradictory_column_is_undecidable():
    # 25/03 is only valid as D/M, 04/25 only as M/D -- the column disagrees
    # with itself, so guessing either way would corrupt half the rows.
    assert resolve_date_order(["25/03/2024", "04/25/2024"]) == "unknown"


def test_explicit_mode_overrides_the_evidence():
    assert resolve_date_order(["03/04/2024", "25/03/2024"], "mdy") == "mdy"


def test_undecidable_column_flags_instead_of_guessing():
    rows = [["A", "a@x.co", "03/04/2024", ""], ["B", "b@x.co", "05/06/2024", ""]]
    result = clean_table(HEADERS, rows, date_format="auto")
    assert result["counts"]["dates_fixed"] == 0
    assert all(FLAG_AMBIGUOUS_DATE in f for f in _flags(result))
    # The original text is left exactly as the client typed it.
    assert [r[2] for r in result["rows"]] == ["03/04/2024", "05/06/2024"]


def test_forced_formats_produce_opposite_readings():
    rows = [["A", "a@x.co", "03/04/2024", ""]]
    assert clean_table(HEADERS, rows, date_format="dmy")["rows"][0][2] == "2024-04-03"
    assert clean_table(HEADERS, rows, date_format="mdy")["rows"][0][2] == "2024-03-04"


def test_textual_and_iso_dates_normalize():
    rows = [["A", "a@x.co", "Mar 5, 2024", ""], ["B", "b@x.co", "5 March 2024", ""],
            ["C", "c@x.co", "2024-03-05", ""]]
    result = clean_table(HEADERS, rows, date_format="auto")
    assert [r[2] for r in result["rows"]] == ["2024-03-05"] * 3
    # The already-ISO row was correct on arrival and must not be counted.
    assert result["counts"]["dates_fixed"] == 2


def test_two_digit_years_use_the_excel_pivot():
    assert parse_date("01/02/99")[1][2] == 1999
    assert parse_date("01/02/24")[1][2] == 2024


def test_unparseable_date_is_flagged_and_left_alone():
    # The column needs real dates in it to BE a date column -- one stray value
    # among valid ones is the actual failure mode, and the bad cell is left
    # exactly as typed rather than blanked.
    rows = [["A", "a@x.co", "2024-03-05", ""],
            ["B", "b@x.co", "2024-03-06", ""],
            ["C", "c@x.co", "sometime last spring", ""]]
    result = clean_table(HEADERS, rows, date_format="auto")
    assert FLAG_UNPARSEABLE_DATE in result["row_meta"][2]["flags"]
    assert result["rows"][2][2] == "sometime last spring"
    assert result["row_meta"][0]["flags"] == []


def test_impossible_date_is_not_silently_accepted():
    # Feb 31 parses structurally but isn't a real day -- it must not become
    # Mar 2 or get clamped to Feb 29.
    rows = [["A", "a@x.co", "2024-03-05", ""],
            ["B", "b@x.co", "2024-03-06", ""],
            ["C", "c@x.co", "2024-02-31", ""]]
    result = clean_table(HEADERS, rows, date_format="auto")
    assert FLAG_UNPARSEABLE_DATE in result["row_meta"][2]["flags"]
    assert result["rows"][2][2] == "2024-02-31"


def test_a_column_of_junk_is_not_treated_as_dates_at_all():
    # The mirror image: when nothing in the column parses, it simply isn't a
    # date column, so nothing is flagged and nothing is touched.
    rows = [["A", "a@x.co", "whenever", ""], ["B", "b@x.co", "TBD", ""]]
    result = clean_table(HEADERS, rows, date_format="auto")
    assert result["column_types"]["Signup Date"] == "text"
    assert result["counts"]["rows_flagged"] == 0


# ── Cell normalization ────────────────────────────────────────────────────────

def test_whitespace_and_placeholders_are_cleaned_and_counted():
    rows = [["  Alice   Smith ", "a@x.co", "2024-03-05", "N/A"]]
    result = clean_table(HEADERS, rows)
    assert result["rows"][0][0] == "Alice Smith"
    assert result["rows"][0][3] == ""
    assert result["counts"]["cells_trimmed"] == 2


def test_none_is_preserved_as_a_real_value():
    # "None" is a plausible answer in a status or category column; blanking it
    # would be data loss, unlike "N/A" or "-".
    rows = [["A", "a@x.co", "2024-03-05", "None"]]
    assert clean_table(HEADERS, rows)["rows"][0][3] == "None"


# ── Duplicate handling ────────────────────────────────────────────────────────

def _dupe_rows():
    return [
        ["Alice Smith", "alice@x.co", "2024-03-05", "first note"],
        ["Bob Jones", "bob@x.co", "2024-03-06", ""],
        ["Alice Smith", "alice@x.co", "2024-03-05", ""],
    ]


def test_flag_mode_keeps_every_row():
    result = clean_table(HEADERS, _dupe_rows(), duplicate_handling="flag")
    assert result["total_rows_out"] == 3
    assert result["counts"]["duplicates_merged"] == 0
    assert result["counts"]["rows_flagged"] == 2
    assert _flags(result)[0] == [FLAG_DUPLICATE]
    assert _flags(result)[1] == []


def test_merge_mode_collapses_exact_matches():
    result = clean_table(HEADERS, _dupe_rows(), duplicate_handling="merge")
    assert result["total_rows_out"] == 2
    assert result["counts"]["duplicates_merged"] == 1
    assert result["row_meta"][0]["merged_count"] == 1


def test_merge_fills_blanks_but_never_overwrites():
    rows = [
        ["Alice Smith", "alice@x.co", "", "kept"],
        ["Alice Smith", "alice@x.co", "2024-03-05", "discarded"],
    ]
    result = clean_table(HEADERS, rows, duplicate_handling="merge")
    assert result["rows"][0][2] == "2024-03-05"   # blank filled from the duplicate
    assert result["rows"][0][3] == "kept"         # existing value survives


def test_near_matches_are_never_auto_merged():
    # Same person, different email spelling -- strict matching leaves this for
    # a human, which is the whole point of the strict setting.
    rows = [
        ["Alice Smith", "alice@x.co", "2024-03-05", ""],
        ["Alice Smith", "alice.smith@x.co", "2024-03-05", ""],
    ]
    result = clean_table(HEADERS, rows, duplicate_handling="merge")
    assert result["total_rows_out"] == 2
    assert result["counts"]["duplicates_merged"] == 0


def test_phone_formatting_differences_still_match():
    headers = ["Name", "Phone"]
    rows = [["Alice", "(555) 123-4567"], ["Alice", "555-123-4567"]]
    result = clean_table(headers, rows, duplicate_handling="merge")
    assert result["counts"]["duplicates_merged"] == 1
    # Comparison normalization must not leak into the output.
    assert result["rows"][0][1] == "(555) 123-4567"


def test_rows_with_an_entirely_blank_identity_are_not_duplicates():
    # Two rows that share nothing but emptiness aren't evidence of a duplicate.
    rows = [["", "", "2024-03-05", "a"], ["", "", "2024-03-06", "b"]]
    result = clean_table(HEADERS, rows, duplicate_handling="merge")
    assert result["total_rows_out"] == 2


def test_case_and_spacing_differences_are_treated_as_duplicates():
    rows = [["Alice Smith", "ALICE@X.CO", "2024-03-05", ""],
            ["alice  smith", "alice@x.co", "2024-03-05", ""]]
    result = clean_table(HEADERS, rows, duplicate_handling="merge")
    assert result["counts"]["duplicates_merged"] == 1
    # The kept row keeps its original casing -- we dedupe, we don't rewrite.
    assert result["rows"][0][1] == "ALICE@X.CO"


# ── Column plan handling ──────────────────────────────────────────────────────

def test_supplied_column_plan_overrides_heuristics():
    rows = [["Alice", "a@x.co", "2024-03-05", ""], ["Bob", "a@x.co", "2024-03-06", ""]]
    plan = {"types": {h: "text" for h in HEADERS}, "identity": ["Email"]}
    result = clean_table(HEADERS, rows, duplicate_handling="merge", column_plan=plan)
    # Identity is Email alone, so these two different names are one record.
    assert result["counts"]["duplicates_merged"] == 1
    # And "Signup Date" was typed as text, so no date normalization ran.
    assert result["counts"]["dates_fixed"] == 0


def test_partial_plan_is_completed_by_heuristics():
    rows = [["Alice", "a@x.co", "03/04/2024", ""], ["Bob", "b@x.co", "25/03/2024", ""]]
    plan = {"types": {"Name": "name"}, "identity": ["Email"]}
    result = clean_table(HEADERS, rows, date_format="auto", column_plan=plan)
    # "Signup Date" wasn't in the plan, so detection filled it in and ran.
    assert result["counts"]["dates_fixed"] == 2


def test_iso_dates_are_typed_as_dates_not_phone_numbers():
    # "2024-03-05" matches a loose phone pattern too. If phone wins, the column
    # never gets normalized and -- worse -- becomes part of the dedupe identity
    # key, because phone counts as an identifying type.
    rows = [["A", "a@x.co", "2024-03-05", ""], ["B", "b@x.co", "2024-03-06", ""]]
    result = clean_table(HEADERS, rows)
    assert result["column_types"]["Signup Date"] == "date"
    assert "Signup Date" not in result["identity_columns"]


def test_short_digit_strings_are_numbers_not_phones():
    headers = ["Name", "Qty"]
    rows = [["A", "12"], ["B", "3400"]]
    assert clean_table(headers, rows)["column_types"]["Qty"] == "number"


def test_ragged_rows_are_padded_not_dropped():
    result = clean_table(HEADERS, [["Alice"], ["Bob", "b@x.co"]])
    assert result["total_rows_out"] == 2
    assert all(len(r) == len(HEADERS) for r in result["rows"])


# ── Spreadsheet I/O round-trip ────────────────────────────────────────────────

class _Upload:
    """Minimal stand-in for a Werkzeug FileStorage."""
    def __init__(self, data, filename):
        self._data = data
        self.filename = filename

    def read(self):
        return self._data


def test_csv_round_trip_preserves_values():
    raw = "Name,Email\nAlice,a@x.co\nBob,b@x.co\n".encode()
    headers, rows = spreadsheet.read_table(_Upload(raw, "in.csv"))
    assert headers == ["Name", "Email"]
    assert len(rows) == 2
    out = spreadsheet.write_table(headers, rows, "csv")
    headers2, rows2 = spreadsheet.read_table(_Upload(out, "out.csv"))
    assert headers2 == headers and [list(r) for r in rows2] == [list(r) for r in rows]


def test_semicolon_delimited_csv_is_detected():
    raw = "Name;Email\nAlice;a@x.co\nBob;b@x.co\n".encode()
    headers, rows = spreadsheet.read_table(_Upload(raw, "in.csv"))
    assert headers == ["Name", "Email"]
    assert len(rows) == 2


def test_cp1252_csv_decodes_without_mojibake():
    raw = "Name,City\nRené,Köln\n".encode("cp1252")
    headers, rows = spreadsheet.read_table(_Upload(raw, "in.csv"))
    assert rows[0][0] == "René"


def test_blank_and_duplicate_headers_are_made_distinct():
    raw = "Name,,Name\nA,B,C\n".encode()
    headers, _ = spreadsheet.read_table(_Upload(raw, "in.csv"))
    assert len(set(headers)) == 3


def test_xlsx_round_trip_and_date_cells():
    from datetime import datetime as dt

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Name", "Signup Date"])
    ws.append(["Alice", dt(2024, 3, 5)])
    buf = io.BytesIO()
    wb.save(buf)

    headers, rows = spreadsheet.read_table(_Upload(buf.getvalue(), "in.xlsx"))
    assert headers == ["Name", "Signup Date"]
    result = clean_table(headers, rows)
    # A real .xlsx date cell arrives already correct -- normalized, not "fixed".
    assert result["rows"][0][1] == "2024-03-05"
    assert result["counts"]["dates_fixed"] == 0
    assert spreadsheet.write_table(headers, result["rows"], "xlsx")[:2] == b"PK"


def _numbers_bytes(cells):
    """Build a real .numbers file the way a Mac user's would arrive."""
    import tempfile

    from numbers_parser import Document

    doc = Document()
    table = doc.sheets[0].tables[0]
    for r, row in enumerate(cells):
        for c, value in enumerate(row):
            table.write(r, c, value)
    with tempfile.NamedTemporaryFile(suffix=".numbers") as tmp:
        doc.save(tmp.name)
        return Path(tmp.name).read_bytes()


def test_numbers_reads_like_xlsx():
    from datetime import datetime as dt

    raw = _numbers_bytes([
        ["Name", "Signup Date", "Qty", "Price"],
        ["  Alice ", dt(2024, 3, 5), 3, 12.5],
        ["", "", "", ""],
        ["Bob", "March 4, 2024", 10, 0.1],
    ])
    headers, rows = spreadsheet.read_table(_Upload(raw, "in.numbers"))
    # Numbers pads the default table out to a wide blank grid; none of that
    # padding should show up as "Column 5" headers or empty rows.
    assert headers == ["Name", "Signup Date", "Qty", "Price"]
    assert len(rows) == 2
    # Whole numbers arrive as int and decimals lose numbers-parser's float
    # noise, so the cleaner sees exactly what an .xlsx upload would give it.
    assert rows[0][2] == 3 and isinstance(rows[0][2], int)
    assert rows[0][3] == 12.5
    result = clean_table(headers, rows)
    assert result["rows"][0][:3] == ["Alice", "2024-03-05", "3"]
    assert result["counts"]["dates_fixed"] == 1  # only Bob's typed-in date
    # A Numbers upload downloads as a native .numbers file.
    assert spreadsheet.format_for_filename("in.numbers") == "numbers"
    assert spreadsheet.format_for_filename("in.xlsx") == "xlsx"
    assert spreadsheet.format_for_filename("in.csv") == "csv"
    out = spreadsheet.write_table(headers, result["rows"], "numbers")
    assert out[:2] == b"PK"  # .numbers is a zip container too
    headers2, rows2 = spreadsheet.read_table(_Upload(out, "out.numbers"))
    assert headers2 == headers
    assert rows2 == result["rows"]


def test_numbers_writer_keeps_typed_cells_and_blanks():
    from datetime import date as d, datetime as dt

    headers = ["Name", "Qty", "When", "Note"]
    rows = [["Alice", 3, dt(2024, 3, 5), None], ["Bob", 2.5, d(2024, 4, 1), ""]]
    out = spreadsheet.write_table(headers, rows, "numbers")
    headers2, rows2 = spreadsheet.read_table(_Upload(out, "out.numbers"))
    assert headers2 == headers
    assert rows2[0] == ["Alice", 3, dt(2024, 3, 5), None]
    # Plain dates go in as midnight datetimes; blanks stay blank (None), not "".
    assert rows2[1] == ["Bob", 2.5, dt(2024, 4, 1), None]


def test_numbers_writer_styles_the_table():
    import tempfile

    from numbers_parser import RGB, Document

    headers = ["Name", "Email Address", "City"]
    rows = [["Alice", "alice@x.co", "Austin"], ["Bob", None, "Boston"], ["Cy", "cy@x.co", ""]]
    out = spreadsheet.write_table(headers, rows, "numbers", title="customers_cleaned")
    with tempfile.NamedTemporaryFile(suffix=".numbers") as tmp:
        tmp.write(out)
        tmp.flush()
        document = Document(tmp.name)
    sheet = document.sheets[0]
    table = sheet.tables[0]

    assert sheet.name == "Cleaned Data"
    assert table.name == "customers_cleaned"
    assert (table.num_rows, table.num_cols) == (4, 3)

    header = table.cell(0, 0).style
    assert header.bold
    assert header.bg_color == RGB(37, 99, 235)
    assert header.font_color == RGB(255, 255, 255)
    assert table.row_height(0) == 28

    # Every other row is banded -- including its blank cells, so the band
    # has no gaps where a value was missing.
    assert table.cell(1, 0).style.bg_color is None
    assert table.cell(2, 0).style.bg_color == RGB(243, 246, 251)
    assert table.cell(2, 1).style.bg_color == RGB(243, 246, 251)
    assert table.cell(3, 2).style.bg_color is None
    assert all(not table.cell(r, c).style.text_wrap for r in range(4) for c in range(3))


def test_numbers_writer_handles_a_large_table_quickly():
    import time

    headers = [f"Column {c}" for c in range(spreadsheet.MAX_COLUMNS)]
    rows = [[f"r{r}c{c}" for c in range(spreadsheet.MAX_COLUMNS)] for r in range(1000)]
    started = time.time()
    out = spreadsheet.write_table(headers, rows, "numbers")
    assert out[:2] == b"PK"
    assert time.time() - started < 30


@pytest.mark.parametrize("text, expected", [
    ("1", (1.0, None)),
    ("1,204.00", (1204.0, None)),
    ("$12.50", (12.5, "$")),
    ("(5.00)", (-5.0, None)),
    ("-$3.20", (-3.2, "$")),
    ("€1,000", (1000.0, "€")),
    # Comma decimals are ambiguous (is "1,204" 1204 or 1.204?), so never guessed.
    ("1.204,00", None),
    ("12,50", None),
    ("$1,20", None),
    ("(5.00", None),
    ("n/a", None),
])
def test_parse_money_only_accepts_unambiguous_amounts(text, expected):
    assert spreadsheet._parse_money(text) == expected


def test_convert_money_columns_is_all_or_nothing_per_column():
    headers = ["Name", "Paid", "Mixed", "Messy", "Qty"]
    rows = [
        ["Alice", "$1,204.00", "$1", "10.00", "3"],
        ["Bob", "12.5", "€2", "see note", "4"],
        ["Cy", "", "3", "", "5"],
    ]
    types = {"Paid": "currency", "Mixed": "currency", "Messy": "currency", "Qty": "number"}
    out, money = spreadsheet.convert_money_columns(headers, rows, types)
    assert money == {1: "$"}
    assert [r[1] for r in out] == [1204.0, 12.5, ""]
    assert [r[2] for r in out] == ["$1", "€2", "3"]         # two symbols: untouched
    assert [r[3] for r in out] == ["10.00", "see note", ""]  # a stray note: untouched
    assert [r[4] for r in out] == ["3", "4", "5"]            # not a currency column
    assert rows[0][1] == "$1,204.00"                         # input not mutated


def test_money_columns_show_two_decimals_and_symbol():
    import tempfile

    from numbers_parser import Document
    from openpyxl import load_workbook

    headers = ["Item", "Price", "Fee"]
    rows = [["A", 1.0, 1204.0], ["B", 12.5, 0.5]]
    money = {1: "$", 2: None}

    sheet = load_workbook(io.BytesIO(spreadsheet.write_table(headers, rows, "xlsx", money_columns=money))).active
    assert sheet["B2"].number_format == '"$"#,##0.00'
    assert sheet["C2"].number_format == "#,##0.00"

    with tempfile.NamedTemporaryFile(suffix=".numbers") as tmp:
        tmp.write(spreadsheet.write_table(headers, rows, "numbers", money_columns=money))
        tmp.flush()
        table = Document(tmp.name).sheets[0].tables[0]
    assert table.cell(1, 1).formatted_value == "$1.00"
    assert table.cell(2, 1).formatted_value == "$12.50"
    assert table.cell(1, 2).formatted_value == "1,204.00"
    assert table.cell(2, 2).formatted_value == "0.50"


def test_corrupt_numbers_file_is_a_clean_error():
    import pytest
    with pytest.raises(ValueError, match="Could not read that .numbers file"):
        spreadsheet.read_table(_Upload(b"not a numbers file", "bad.numbers"))


def test_unsupported_extension_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        spreadsheet.read_table(_Upload(b"x", "notes.docx"))


def test_row_limit_is_enforced():
    import pytest
    body = "\n".join(f"Name{i},x@y.co" for i in range(spreadsheet.MAX_ROWS + 5))
    raw = f"Name,Email\n{body}\n".encode()
    with pytest.raises(spreadsheet.TableTooLarge):
        spreadsheet.read_table(_Upload(raw, "big.csv"))
