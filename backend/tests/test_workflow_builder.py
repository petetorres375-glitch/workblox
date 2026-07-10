from unittest.mock import patch

import pytest

MOCK_RESPONSE = {
    "filename": "rename_photos.py",
    "script": "# renames photos\nprint('done')",
}


@pytest.fixture(autouse=True)
def _bypass_tool_entitlement():
    # TESTING mode skips auth entirely, so g.user is never set — require_tool()
    # would blow up reading it. These tests are about the workflow-builder
    # logic, not access control, so bypass require_tool() and require_personal().
    with patch("app.routes.workflow_builder.require_tool", return_value=None), \
         patch("app.routes.workflow_builder.require_personal", return_value=None):
        yield


def test_workflow_builder_success(client):
    with patch("app.routes.workflow_builder.claude_client.call", return_value=MOCK_RESPONSE):
        rv = client.post("/api/workflow", json={"task": "rename all photos by date"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["filename"].endswith(".py")
    assert "script" in data


def test_workflow_builder_missing_task(client):
    rv = client.post("/api/workflow", json={})
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_workflow_builder_empty_task(client):
    rv = client.post("/api/workflow", json={"task": "   "})
    assert rv.status_code == 400
