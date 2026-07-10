import uuid
from unittest.mock import patch

import pytest

from app.models import Tool, ToolRequest, User, UserEntitlement
from app.services.entitlements import set_entitlements


def _as_admin():
    # TESTING mode skips auth entirely, so g.user is never set -- _is_admin()
    # would blow up reading it. These tests are about the entitlements
    # endpoints' behavior, not JWT/session handling, so bypass the guard.
    return patch("app.routes.admin._is_admin", return_value=True)


@pytest.fixture
def target_user(client):
    from app import db

    with client.application.app_context():
        user = User(
            email=f"admin-target-{uuid.uuid4()}@example.com",
            name="Admin Target",
            is_active=True,
            email_verified=True,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    yield user_id
    with client.application.app_context():
        UserEntitlement.query.filter_by(user_id=user_id).delete()
        ToolRequest.query.filter_by(user_id=user_id).delete()
        User.query.filter_by(id=user_id).delete()
        db.session.commit()


def test_admin_grants_access_independently(client, target_user):
    with _as_admin():
        rv = client.post(f"/api/admin/users/{target_user}/access", json={"has_personal": True})
    assert rv.status_code == 200
    assert rv.get_json() == {"has_personal": True, "has_business": False}

    with _as_admin():
        rv = client.post(f"/api/admin/users/{target_user}/access", json={"has_business": True})
    assert rv.status_code == 200
    assert rv.get_json() == {"has_personal": True, "has_business": True}

    with _as_admin():
        rv = client.post(f"/api/admin/users/{target_user}/access", json={"has_personal": False})
    assert rv.status_code == 200
    assert rv.get_json() == {"has_personal": False, "has_business": True}


def test_admin_access_endpoint_forbidden_for_non_admin(client, target_user):
    with patch("app.routes.admin._is_admin", return_value=False):
        rv = client.post(f"/api/admin/users/{target_user}/access", json={"has_personal": True})
    assert rv.status_code == 403


def test_get_user_entitlements_empty(client, target_user):
    with _as_admin():
        rv = client.get(f"/api/admin/users/{target_user}/entitlements")
    assert rv.status_code == 200
    assert rv.get_json()["tool_keys"] == []


def test_admin_can_add_a_tool(client, target_user):
    with _as_admin():
        rv = client.post(f"/api/admin/users/{target_user}/entitlements",
                          json={"tool_key": "hiring", "enabled": True})
    assert rv.status_code == 200
    assert rv.get_json()["tool_keys"] == ["hiring"]

    with client.application.app_context():
        row = UserEntitlement.query.filter_by(user_id=target_user).first()
        assert row.source == "admin_manual"


def test_admin_can_remove_a_tool(client, target_user):
    with client.application.app_context():
        set_entitlements(target_user, {"hiring", "sop"}, source="self_service")

    with _as_admin():
        rv = client.post(f"/api/admin/users/{target_user}/entitlements",
                          json={"tool_key": "sop", "enabled": False})
    assert rv.status_code == 200
    assert rv.get_json()["tool_keys"] == ["hiring"]


def test_admin_rejects_unknown_tool_key(client, target_user):
    with _as_admin():
        rv = client.post(f"/api/admin/users/{target_user}/entitlements",
                          json={"tool_key": "not-a-tool", "enabled": True})
    assert rv.status_code == 400


def test_non_admin_forbidden(client, target_user):
    with patch("app.routes.admin._is_admin", return_value=False):
        rv = client.get(f"/api/admin/users/{target_user}/entitlements")
        assert rv.status_code == 403
        rv = client.post(f"/api/admin/users/{target_user}/entitlements",
                          json={"tool_key": "hiring", "enabled": True})
        assert rv.status_code == 403
        rv = client.get("/api/admin/entitlements/summary")
        assert rv.status_code == 403


def test_entitlements_summary_shape(client, target_user):
    with client.application.app_context():
        set_entitlements(target_user, {"hiring"}, source="self_service")

    with _as_admin():
        rv = client.get("/api/admin/entitlements/summary")
    assert rv.status_code == 200
    rows = rv.get_json()
    hiring_rows = [r for r in rows if r["tool_key"] == "hiring" and r["source"] == "self_service"]
    assert len(hiring_rows) >= 1
    row = hiring_rows[0]
    assert row["tool_name"] == "Hiring Manager"
    assert row["app"] == "business"
    assert row["enabled_at"] is not None


def test_list_tool_requests_shape(client, target_user):
    with client.application.app_context():
        from app import db
        tool = Tool.query.filter_by(key="sop").first()
        db.session.add(ToolRequest(user_id=target_user, tool_id=tool.id))
        db.session.commit()

    with _as_admin():
        rv = client.get("/api/admin/tool-requests")
    assert rv.status_code == 200
    rows = rv.get_json()
    matches = [r for r in rows if r["user_id"] == target_user]
    assert len(matches) == 1
    row = matches[0]
    assert row["tool_key"] == "sop"
    assert row["tool_name"] == "SOP Generator"
    assert row["app"] == "business"
    assert row["requested_at"] is not None
    assert "request_id" in row


def test_grant_tool_request_creates_entitlement_and_clears_request(client, target_user):
    with client.application.app_context():
        from app import db
        tool = Tool.query.filter_by(key="sop").first()
        req = ToolRequest(user_id=target_user, tool_id=tool.id)
        db.session.add(req)
        db.session.commit()
        request_id = req.id

    with _as_admin():
        rv = client.post(f"/api/admin/tool-requests/{request_id}/grant")
    assert rv.status_code == 200

    with client.application.app_context():
        assert db.session.get(ToolRequest, request_id) is None
        row = UserEntitlement.query.filter_by(user_id=target_user).first()
        assert row.source == "admin_manual"


def test_dismiss_tool_request_clears_without_granting(client, target_user):
    with client.application.app_context():
        from app import db
        tool = Tool.query.filter_by(key="sop").first()
        req = ToolRequest(user_id=target_user, tool_id=tool.id)
        db.session.add(req)
        db.session.commit()
        request_id = req.id

    with _as_admin():
        rv = client.post(f"/api/admin/tool-requests/{request_id}/dismiss")
    assert rv.status_code == 200

    with client.application.app_context():
        assert db.session.get(ToolRequest, request_id) is None
        assert UserEntitlement.query.filter_by(user_id=target_user).count() == 0


def test_tool_requests_forbidden_for_non_admin(client, target_user):
    with patch("app.routes.admin._is_admin", return_value=False):
        rv = client.get("/api/admin/tool-requests")
        assert rv.status_code == 403
        rv = client.post("/api/admin/tool-requests/1/grant")
        assert rv.status_code == 403
        rv = client.post("/api/admin/tool-requests/1/dismiss")
        assert rv.status_code == 403
