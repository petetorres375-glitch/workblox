"""Route tests for Data Cleanup and Expense Organizer.

Claude is patched throughout -- what's under test is the plumbing around it:
validation of model output, the deterministic fallbacks when the model is
unavailable, date-range filtering, and per-file error isolation.
"""
import io
from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def _bypass_guards():
    # Same shape as test_biz_tools.py: TESTING mode skips auth, so g.user is
    # never set and both guards would blow up reading it.
    with patch("app.routes.biz_tools._require_business", return_value=None), \
         patch("app.routes.biz_tools.require_tool", return_value=None):
        yield


def _csv(text, name="data.csv"):
    return {"file": (io.BytesIO(text.encode()), name)}


CUSTOMERS_CSV = (
    "Name,Email,Signup Date\n"
    "  Alice  Smith ,alice@x.co,03/04/2024\n"
    "Bob Jones,bob@x.co,25/03/2024\n"
    "Alice Smith,alice@x.co,03/04/2024\n"
)


# ── Data Cleanup ──────────────────────────────────────────────────────────────

def test_data_cleanup_uses_the_ai_column_plan(client):
    plan = {"types": {"Name": "name", "Email": "email", "Signup Date": "date"},
            "identity": ["Email"]}
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", return_value=plan):
        rv = client.post("/api/biz/data-cleanup",
                         data={**_csv(CUSTOMERS_CSV), "duplicate_handling": "merge"},
                         content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ai_plan_used"] is True
    assert body["counts"]["duplicates_merged"] == 1
    assert body["total_rows_out"] == 2
    # 25/03 settles the column as D/M/Y, so 03/04 is the 3rd of April.
    assert body["rows"][0][2] == "2024-04-03"
    assert body["source_format"] == "csv"


def test_data_cleanup_falls_back_when_the_ai_call_fails(client):
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", side_effect=RuntimeError("upstream down")):
        rv = client.post("/api/biz/data-cleanup",
                         data={**_csv(CUSTOMERS_CSV), "duplicate_handling": "merge"},
                         content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ai_plan_used"] is False
    # The cleanup itself is unaffected -- it never needed the model.
    assert body["counts"]["duplicates_merged"] == 1
    assert body["counts"]["dates_fixed"] == 3


def test_data_cleanup_rejects_a_hallucinated_column_plan(client):
    # Columns that aren't in the file, and a bogus type, must not reach the engine.
    plan = {"types": {"Totally Made Up": "date", "Email": "banana"},
            "identity": ["Also Invented"]}
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", return_value=plan):
        rv = client.post("/api/biz/data-cleanup", data=_csv(CUSTOMERS_CSV),
                         content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ai_plan_used"] is False
    assert set(body["column_types"]) == {"Name", "Email", "Signup Date"}


def test_data_cleanup_requires_a_file(client):
    with _bypass_guards():
        rv = client.post("/api/biz/data-cleanup", data={}, content_type="multipart/form-data")
    assert rv.status_code == 400


def test_data_cleanup_rejects_unsupported_file_types(client):
    with _bypass_guards():
        rv = client.post("/api/biz/data-cleanup",
                         data={"file": (io.BytesIO(b"not a sheet"), "contract.docx")},
                         content_type="multipart/form-data")
    assert rv.status_code == 415


def test_data_cleanup_rejects_a_header_only_file(client):
    with _bypass_guards(), patch("app.routes.biz_tools.claude_client.call", return_value={}):
        rv = client.post("/api/biz/data-cleanup", data=_csv("Name,Email\n"),
                         content_type="multipart/form-data")
    assert rv.status_code == 422


def test_data_cleanup_download_returns_a_csv(client):
    with _bypass_guards():
        rv = client.post("/api/biz/data-cleanup/download", json={
            "headers": ["Name", "Email"],
            "rows": [["Alice", "a@x.co"]],
            "filename": "cleaned",
            "format": "csv",
        })
    assert rv.status_code == 200
    assert rv.mimetype == "text/csv"
    assert "cleaned.csv" in rv.headers["Content-Disposition"]
    assert b"Alice" in rv.data


def test_data_cleanup_download_returns_an_xlsx(client):
    with _bypass_guards():
        rv = client.post("/api/biz/data-cleanup/download", json={
            "headers": ["Name"], "rows": [["Alice"]], "format": "xlsx",
        })
    assert rv.status_code == 200
    assert rv.data[:2] == b"PK"  # xlsx is a zip container


def test_data_cleanup_download_validates_its_input(client):
    with _bypass_guards():
        rv = client.post("/api/biz/data-cleanup/download", json={"rows": []})
    assert rv.status_code == 400


# ── Expense Organizer ─────────────────────────────────────────────────────────

STATEMENT_CSV = (
    "Date,Description,Amount\n"
    "2024-03-05,SQ *BLUE BOTTLE COFFEE 0123,-12.50\n"
    "2024-03-07,ADOBE  *CREATIVE CLOUD,-52.99\n"
    "2024-04-02,DELTA AIR LINES,-341.20\n"
)

CATEGORIZED = {"entries": [
    {"index": 0, "vendor": "Blue Bottle Coffee", "category": "Meals", "confidence": "high", "reason": "", "notes": ""},
    {"index": 1, "vendor": "Adobe Creative Cloud", "category": "Software", "confidence": "high", "reason": "", "notes": ""},
    {"index": 2, "vendor": "Delta Air Lines", "category": "Travel", "confidence": "high", "reason": "", "notes": ""},
]}


def _statement(text=STATEMENT_CSV, name="statement.csv"):
    return {"files": (io.BytesIO(text.encode()), name)}


def test_expenses_categorizes_a_bank_statement(client):
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", return_value=CATEGORIZED):
        rv = client.post("/api/biz/expenses", data=_statement(),
                         content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert len(body["entries"]) == 3
    assert body["entries"][0]["vendor"] == "Blue Bottle Coffee"
    # Amounts are reported as positive spend regardless of the export's sign.
    assert body["entries"][0]["amount"] == 12.50
    assert body["totals"] == {"Meals": 12.5, "Software": 52.99, "Travel": 341.2}
    assert body["grand_total"] == 406.69


def test_expenses_filters_by_custom_date_range(client):
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", return_value=CATEGORIZED):
        rv = client.post("/api/biz/expenses", data={
            **_statement(),
            "date_range": "custom",
            "start_date": "2024-03-01",
            "end_date": "2024-03-31",
        }, content_type="multipart/form-data")
    body = rv.get_json()
    assert len(body["entries"]) == 2          # the April flight is out of range
    assert body["filtered_out"] == 1
    assert body["grand_total"] == 65.49


def test_expenses_keeps_entries_whose_date_could_not_be_read(client):
    # Dropping a receipt because its date was unreadable is the worst possible
    # failure for this tool -- it must survive filtering and be flagged instead.
    statement = "Date,Description,Amount\nsmudged,CORNER STORE,-8.00\n"
    one = {"entries": [{"index": 0, "vendor": "Corner Store", "category": "Meals",
                        "confidence": "high", "reason": "", "notes": ""}]}
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", return_value=one):
        rv = client.post("/api/biz/expenses", data={
            **_statement(statement),
            "date_range": "custom",
            "start_date": "2024-03-01",
            "end_date": "2024-03-31",
        }, content_type="multipart/form-data")
    body = rv.get_json()
    assert len(body["entries"]) == 1
    assert body["entries"][0]["confidence"] == "low"
    assert "date" in body["entries"][0]["reason"].lower()


def test_expenses_flags_money_coming_in(client):
    statement = ("Date,Description,Amount\n"
                 "2024-03-05,COFFEE,-12.50\n"
                 "2024-03-06,REFUND FROM VENDOR,40.00\n")
    two = {"entries": [
        {"index": 0, "vendor": "Coffee", "category": "Meals", "confidence": "high", "reason": "", "notes": ""},
        {"index": 1, "vendor": "Refund", "category": "Other", "confidence": "high", "reason": "", "notes": ""},
    ]}
    with _bypass_guards(), patch("app.routes.biz_tools.claude_client.call", return_value=two):
        rv = client.post("/api/biz/expenses", data=_statement(statement),
                         content_type="multipart/form-data")
    entries = rv.get_json()["entries"]
    assert entries[1]["confidence"] == "low"
    assert "coming in" in entries[1]["reason"]


def test_expenses_survives_a_failed_categorization(client):
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", side_effect=RuntimeError("upstream down")):
        rv = client.post("/api/biz/expenses", data=_statement(),
                         content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    # The transactions are still extracted deterministically; they just fall
    # back to the catch-all category and are marked for review.
    assert len(body["entries"]) == 3
    assert all(e["confidence"] == "low" for e in body["entries"])
    assert body["entries"][0]["category"] == "Other"


def test_expenses_uses_custom_categories(client):
    single = {"entries": [{"index": 0, "vendor": "X", "category": "Coffee Budget",
                           "confidence": "high", "reason": "", "notes": ""}]}
    statement = "Date,Description,Amount\n2024-03-05,COFFEE,-12.50\n"
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", return_value=single) as mock_call:
        rv = client.post("/api/biz/expenses", data={
            **_statement(statement),
            "categories": "Coffee Budget, Rent, Gear",
        }, content_type="multipart/form-data")
    body = rv.get_json()
    assert body["categories"] == ["Coffee Budget", "Rent", "Gear"]
    assert "Coffee Budget" in mock_call.call_args.kwargs["user_message"]


def test_expenses_isolates_a_bad_file_from_the_good_ones(client):
    with _bypass_guards(), \
         patch("app.routes.biz_tools.claude_client.call", return_value=CATEGORIZED):
        rv = client.post("/api/biz/expenses", data={"files": [
            (io.BytesIO(STATEMENT_CSV.encode()), "statement.csv"),
            (io.BytesIO(b"whatever"), "notes.docx"),
        ]}, content_type="multipart/form-data")
    body = rv.get_json()
    assert len(body["entries"]) == 3            # the good file still worked
    assert len(body["errors"]) == 1
    assert body["errors"][0]["filename"] == "notes.docx"


def test_expenses_requires_at_least_one_file(client):
    with _bypass_guards():
        rv = client.post("/api/biz/expenses", data={}, content_type="multipart/form-data")
    assert rv.status_code == 400


def test_expenses_caps_the_file_count(client):
    files = [(io.BytesIO(b"x"), f"r{i}.jpg") for i in range(11)]
    with _bypass_guards():
        rv = client.post("/api/biz/expenses", data={"files": files},
                         content_type="multipart/form-data")
    assert rv.status_code == 400


def test_receipt_image_goes_through_vision(client):
    receipt = {"date": "2024-03-05", "vendor": "Blue Bottle", "amount": 12.5,
               "currency": "USD", "category": "Meals", "confidence": "high",
               "reason": "", "notes": ""}
    with _bypass_guards(), \
         patch("app.routes.biz_tools.prepare_image", return_value=b"jpeg-bytes"), \
         patch("app.routes.biz_tools.claude_client.call", return_value=receipt) as mock_call:
        rv = client.post("/api/biz/expenses",
                         data={"files": (io.BytesIO(b"fake-jpeg"), "receipt.jpg")},
                         content_type="multipart/form-data")
    assert rv.status_code == 200
    assert len(mock_call.call_args.kwargs["images"]) == 1
    assert rv.get_json()["entries"][0]["vendor"] == "Blue Bottle"


def test_unreadable_receipt_does_not_fail_the_request(client):
    with _bypass_guards(), \
         patch("app.routes.biz_tools.prepare_image", side_effect=ValueError("Could not read that photo")):
        rv = client.post("/api/biz/expenses",
                         data={"files": (io.BytesIO(b"garbage"), "receipt.jpg")},
                         content_type="multipart/form-data")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["entries"] == []
    assert body["errors"][0]["filename"] == "receipt.jpg"


def test_expenses_export_returns_an_xlsx(client):
    with _bypass_guards():
        rv = client.post("/api/biz/expenses/export", json={"entries": [
            {"date": "2024-03-05", "vendor": "Blue Bottle", "amount": 12.5,
             "category": "Meals", "source": "receipt.jpg", "notes": ""},
        ]})
    assert rv.status_code == 200
    assert rv.data[:2] == b"PK"
    assert "expenses.xlsx" in rv.headers["Content-Disposition"]


def test_expenses_export_requires_entries(client):
    with _bypass_guards():
        rv = client.post("/api/biz/expenses/export", json={"entries": []})
    assert rv.status_code == 400
