import io
from contextlib import contextmanager
from unittest.mock import patch

from app.services.claude_client import MAX_IMAGES

MOCK_CONTRACT_RESPONSE = {
    "document_type": "Service Agreement",
    "summary": "A test contract.",
    "key_obligations": ["Pay on time"],
    "important_dates": [],
    "payment_terms": "Net 30",
    "termination_clauses": [],
    "red_flags": ["None identified."],
    "missing_standard_clauses": [],
    "overall_risk": "low",
    "recommendation": "Looks fine.",
}


@contextmanager
def _bypass_business_guard():
    # TESTING mode skips auth entirely (see app/__init__.py::require_auth), so
    # g.user is never set — _require_business() and require_tool() would both
    # blow up reading it. Patching both guards isolates these tests to the
    # photo-handling logic being added here, not the unrelated business-plan
    # or per-tool entitlement checks.
    with patch("app.routes.biz_tools._require_business", return_value=None), \
         patch("app.routes.biz_tools.require_tool", return_value=None):
        yield


def test_contract_analyzer_photo_single(client):
    data = {"images": (io.BytesIO(b"fake-jpeg-bytes"), "photo-1.jpg")}
    with _bypass_business_guard(), \
         patch("app.routes.biz_tools.prepare_image", return_value=b"normalized-jpeg-bytes"), \
         patch("app.routes.biz_tools.claude_client.call", return_value=MOCK_CONTRACT_RESPONSE) as mock_call:
        rv = client.post("/api/biz/contract", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert rv.get_json()["document_type"] == MOCK_CONTRACT_RESPONSE["document_type"]
    _, kwargs = mock_call.call_args
    assert len(kwargs["images"]) == 1
    assert kwargs["images"][0]["media_type"] == "image/jpeg"


def test_contract_analyzer_photo_multiple_pages(client):
    data = {"images": [
        (io.BytesIO(b"page-1"), "photo-1.jpg"),
        (io.BytesIO(b"page-2"), "photo-2.jpg"),
        (io.BytesIO(b"page-3"), "photo-3.jpg"),
    ]}
    with _bypass_business_guard(), \
         patch("app.routes.biz_tools.prepare_image", return_value=b"normalized-jpeg-bytes"), \
         patch("app.routes.biz_tools.claude_client.call", return_value=MOCK_CONTRACT_RESPONSE) as mock_call:
        rv = client.post("/api/biz/contract", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    _, kwargs = mock_call.call_args
    assert len(kwargs["images"]) == 3


def test_contract_analyzer_photo_and_file_rejected(client):
    data = {
        "file": (io.BytesIO(b"Some contract text."), "contract.txt"),
        "images": (io.BytesIO(b"fake-jpeg-bytes"), "photo-1.jpg"),
    }
    with _bypass_business_guard():
        rv = client.post("/api/biz/contract", data=data, content_type="multipart/form-data")
    assert rv.status_code == 400


def test_contract_analyzer_photo_too_many(client):
    data = {"images": [
        (io.BytesIO(f"page-{i}".encode()), f"photo-{i}.jpg") for i in range(MAX_IMAGES + 1)
    ]}
    with _bypass_business_guard():
        rv = client.post("/api/biz/contract", data=data, content_type="multipart/form-data")
    assert rv.status_code == 400


def test_contract_analyzer_photo_unreadable(client):
    data = {"images": (io.BytesIO(b"not-an-image"), "photo-1.jpg")}
    with _bypass_business_guard(), \
         patch("app.routes.biz_tools.prepare_image",
               side_effect=ValueError("Could not read 'photo-1.jpg' as an image.")):
        rv = client.post("/api/biz/contract", data=data, content_type="multipart/form-data")
    assert rv.status_code == 415


def test_contract_analyzer_no_file_or_images(client):
    with _bypass_business_guard():
        rv = client.post("/api/biz/contract", data={}, content_type="multipart/form-data")
    assert rv.status_code == 400
