from unittest.mock import patch

MOCK_RESPONSE = {
    "command": "ls -la",
    "explanation": "Lists all files in long format.",
    "warnings": ["None."],
}


def test_linux_helper_success(client):
    with patch("app.routes.linux_helper.claude_client.call", return_value=MOCK_RESPONSE):
        rv = client.post("/api/linux", json={"problem": "list all files"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["command"] == "ls -la"
    assert "explanation" in data
    assert isinstance(data["warnings"], list)


def test_linux_helper_missing_problem(client):
    rv = client.post("/api/linux", json={})
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_windows_helper_success(client):
    mock = {
        "command": "Get-ChildItem",
        "explanation": "Lists directory contents.",
        "warnings": ["None."],
    }
    with patch("app.routes.windows_helper.claude_client.call", return_value=mock):
        rv = client.post("/api/windows", json={"problem": "list files"})
    assert rv.status_code == 200
    assert rv.get_json()["command"] == "Get-ChildItem"


def test_windows_helper_missing_problem(client):
    rv = client.post("/api/windows", json={})
    assert rv.status_code == 400


def test_mac_helper_success(client):
    mock = {
        "command": "ls -la",
        "explanation": "Lists all files.",
        "warnings": ["None."],
    }
    with patch("app.routes.mac_helper.claude_client.call", return_value=mock):
        rv = client.post("/api/mac", json={"problem": "list files"})
    assert rv.status_code == 200
    assert rv.get_json()["command"] == "ls -la"


def test_mac_helper_missing_problem(client):
    rv = client.post("/api/mac", json={})
    assert rv.status_code == 400


def test_health(client):
    rv = client.get("/api/health")
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "ok"
