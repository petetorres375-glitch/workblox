"""Unit tests for the deterministic cleanup engine.

No mocking anywhere in this file on purpose: the engine makes no network calls
and reads no clock, so every one of these asserts an exact, reproducible
outcome. That's the property that lets the UI show a client a hard number.
"""
import io

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
