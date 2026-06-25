import io
from unittest.mock import patch

MOCK_RESPONSE = {
    "summary": "A test document.",
    "key_data_points": ["Item 1"],
    "action_items": ["None identified."],
    "red_flags": ["None identified."],
}


def test_doc_analyzer_txt(client):
    data = {"file": (io.BytesIO(b"This is a test document."), "test.txt")}
    with patch("app.routes.doc_analyzer.claude_client.call", return_value=MOCK_RESPONSE):
        rv = client.post("/api/doc", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    result = rv.get_json()
    assert "summary" in result
    assert "key_data_points" in result
    assert "action_items" in result
    assert "red_flags" in result


def test_doc_analyzer_md(client):
    content = b"# Heading\n\nSome markdown content."
    data = {"file": (io.BytesIO(content), "notes.md")}
    with patch("app.routes.doc_analyzer.claude_client.call", return_value=MOCK_RESPONSE):
        rv = client.post("/api/doc", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200


def test_doc_analyzer_no_file(client):
    rv = client.post("/api/doc", data={}, content_type="multipart/form-data")
    assert rv.status_code == 400


def test_doc_analyzer_unsupported_type(client):
    data = {"file": (io.BytesIO(b"data"), "image.jpg")}
    rv = client.post("/api/doc", data=data, content_type="multipart/form-data")
    assert rv.status_code == 415


def test_doc_analyzer_empty_file(client):
    data = {"file": (io.BytesIO(b"   "), "blank.txt")}
    rv = client.post("/api/doc", data=data, content_type="multipart/form-data")
    assert rv.status_code == 422


def test_doc_email_no_api_key(client):
    payload = {"email": "test@example.com", "filename": "doc.txt", "result": MOCK_RESPONSE}
    rv = client.post("/api/doc/email", json=payload)
    assert rv.status_code == 503
    assert "not configured" in rv.get_json()["error"]


def test_doc_email_invalid_email(client):
    payload = {"email": "notanemail", "filename": "doc.txt", "result": MOCK_RESPONSE}
    rv = client.post("/api/doc/email", json=payload)
    assert rv.status_code == 400


def test_doc_email_missing_result(client):
    payload = {"email": "test@example.com", "filename": "doc.txt"}
    rv = client.post("/api/doc/email", json=payload)
    assert rv.status_code == 400


def test_doc_email_sends(client):
    import os
    from unittest.mock import MagicMock, patch
    payload = {"email": "pete@example.com", "filename": "report.txt", "result": MOCK_RESPONSE}
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = b'{"id":"abc"}'
    with patch.dict(os.environ, {"RESEND_API_KEY": "re_test"}), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        rv = client.post("/api/doc/email", json=payload)
    assert rv.status_code == 200
    assert rv.get_json()["success"] is True
