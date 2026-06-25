from unittest.mock import patch

MOCK_RESPONSE = {
    "filename": "rename_photos.py",
    "script": "# renames photos\nprint('done')",
}


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
