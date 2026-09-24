import datetime
import io
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.file_handler import extract_text
from app.services.pages_reader import PASSWORD_ERROR, UNREADABLE_ERROR, read_pages

FIXTURES = Path(__file__).parent / "fixtures" / "pages"


def _fixture(name):
    return (FIXTURES / name).read_bytes()


def _zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


class _Upload:
    """Stand-in for werkzeug's FileStorage: extract_text() only uses these two."""

    def __init__(self, data, filename):
        self.filename = filename
        self._data = data

    def read(self):
        return self._data


# ── Pages 5+ (IWA) ────────────────────────────────────────────────────────────

def test_modern_body_text():
    text = read_pages(_fixture("modern.pages"))
    assert text.startswith("Sample pages document")
    assert "Some plain text to parse." in text
    assert "A second page...." in text


def test_modern_text_box():
    assert "A text box with text." in read_pages(_fixture("modern.pages"))


def test_modern_table_rows_keep_their_structure():
    text = read_pages(_fixture("modern.pages"))
    assert "Column one | Column two | Column three\n" \
           "Cell one | Cell two | Cell three\n" \
           "Cell four | Cell five | Cell six\n" \
           "Cell seven | Cell eight | Cell nine" in text


def test_modern_strips_object_placeholders_and_blank_runs():
    text = read_pages(_fixture("modern.pages"))
    assert "￼" not in text
    assert "\n\n\n" not in text


def test_current_table_layout(tmp_path):
    # Pages since ~2019 stores cells in the same layout numbers-parser writes,
    # so a Numbers table stands in for a table from a current Mac.
    from numbers_parser import Document

    from app.services import pages_reader

    doc = Document()
    table = doc.sheets[0].tables[0]
    rows = [
        ["Skill", "Years", "Since"],
        ["Python", 5, datetime.datetime(2021, 3, 1)],
        ["SQL", 2.5, None],
        ["Kubernetes & Docker", None, "ongoing"],
    ]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value is not None:
                table.write(r, c, value)
    path = tmp_path / "table.numbers"
    doc.save(path)

    archive = zipfile.ZipFile(path)
    objects = {}
    for name in archive.namelist():
        if name.endswith(".iwa"):
            objects.update(pages_reader._decode_iwa(archive.read(name)))
    tables = [obj for kind, obj in objects.values() if kind == pages_reader._TYPE_TABLE_MODEL]

    assert pages_reader._table_text(tables[0], objects).splitlines()[1:] == [
        "Skill | Years | Since",
        "Python | 5 | 2021-03-01",
        "SQL | 2.5",
        "Kubernetes & Docker |  | ongoing",
    ]


def test_modern_password_protected():
    data = _zip({".iwph": b"hint", "Index.zip": b"encrypted"})
    with pytest.raises(ValueError, match="password-protected"):
        read_pages(data)


def test_modern_damaged_iwa():
    data = _zip({"Index/Document.iwa": b"\x00\x05\x00\x00garbage"})
    with pytest.raises(ValueError) as exc:
        read_pages(data)
    assert str(exc.value) == UNREADABLE_ERROR


# ── Pages '09 ─────────────────────────────────────────────────────────────────

def test_legacy_reads_preview_pdf():
    text = read_pages(_fixture("legacy.pages"))
    assert text.startswith("Sample pages document")
    assert "Cell nine" in text


def test_legacy_ligatures_are_expanded():
    # The preview PDF renders "five" with an "fi" ligature glyph.
    text = read_pages(_fixture("legacy.pages"))
    assert "Cell five" in text
    assert "ﬁ" not in text


def test_legacy_without_preview_falls_back_to_index_xml():
    with zipfile.ZipFile(io.BytesIO(_fixture("legacy.pages"))) as src:
        data = _zip({"index.xml": src.read("index.xml")})
    text = read_pages(data)
    assert "Sample pages document" in text
    assert "Some plain text to parse." in text


def test_legacy_password_protected():
    with pytest.raises(ValueError) as exc:
        read_pages(_fixture("legacy_password.pages"))
    assert str(exc.value) == PASSWORD_ERROR


# ── Not a Pages file ──────────────────────────────────────────────────────────

def test_not_a_zip():
    with pytest.raises(ValueError) as exc:
        read_pages(b"%PDF-1.4 renamed to .pages")
    assert str(exc.value) == UNREADABLE_ERROR


def test_zip_without_pages_content():
    with pytest.raises(ValueError) as exc:
        read_pages(_zip({"readme.txt": b"hello"}))
    assert str(exc.value) == UNREADABLE_ERROR


# ── Wiring into the upload paths ──────────────────────────────────────────────

def test_extract_text_accepts_pages():
    text = extract_text(_Upload(_fixture("modern.pages"), "Resume.PAGES"))
    assert "Sample pages document" in text


MOCK_DOC_RESPONSE = {
    "summary": "A test document.",
    "key_data_points": [],
    "action_items": [],
    "red_flags": [],
}


def test_doc_analyzer_pages(client):
    data = {"file": (io.BytesIO(_fixture("modern.pages")), "notes.pages")}
    with patch("app.routes.doc_analyzer.require_tool", return_value=None), \
         patch("app.routes.doc_analyzer.require_personal", return_value=None), \
         patch("app.routes.doc_analyzer.claude_client.call", return_value=MOCK_DOC_RESPONSE) as call:
        rv = client.post("/api/doc", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "Cell one | Cell two" in call.call_args.kwargs["user_message"]


def test_doc_analyzer_password_pages_explains_why(client):
    data = {"file": (io.BytesIO(_fixture("legacy_password.pages")), "locked.pages")}
    with patch("app.routes.doc_analyzer.require_tool", return_value=None), \
         patch("app.routes.doc_analyzer.require_personal", return_value=None):
        rv = client.post("/api/doc", data=data, content_type="multipart/form-data")
    assert rv.status_code == 415
    assert rv.get_json()["error"] == PASSWORD_ERROR


def _bypass_business_guard():
    return patch("app.routes.biz_tools._require_business", return_value=None), \
           patch("app.routes.biz_tools.require_tool", return_value=None)


def test_contract_analyzer_pages(client):
    guard, tool = _bypass_business_guard()
    data = {"file": (io.BytesIO(_fixture("modern.pages")), "contract.pages")}
    with guard, tool, patch("app.routes.biz_tools.claude_client.call", return_value={"summary": "ok"}) as call:
        rv = client.post("/api/biz/contract", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "Some plain text to parse." in call.call_args.kwargs["user_message"]


def test_batch_ats_pages_and_per_file_errors(client):
    guard, tool = _bypass_business_guard()
    data = {
        "resumes": [
            (io.BytesIO(_fixture("modern.pages")), "good.pages"),
            (io.BytesIO(_fixture("legacy_password.pages")), "locked.pages"),
        ],
        "job_description": "Writer",
    }
    with guard, tool, patch("app.routes.biz_tools.claude_client.call", return_value={"score": 70}):
        rv = client.post("/api/biz/batch-ats", data=data, content_type="multipart/form-data")
    results = rv.get_json()["results"]
    assert results[0] == {"score": 70, "filename": "good.pages"}
    assert results[1] == {"filename": "locked.pages", "error": PASSWORD_ERROR}


def test_ats_analyzer_pages(client):
    data = {"resume": (io.BytesIO(_fixture("modern.pages")), "resume.pages")}
    with patch("app.routes.ats_analyzer.require_tool", return_value=None), \
         patch("app.routes.ats_analyzer.require_personal", return_value=None):
        rv = client.post("/api/ats", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "score" in rv.get_json()["results"]
