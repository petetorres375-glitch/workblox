"""
Route-level entitlement and app-access enforcement. Unlike the other route
tests, these deliberately use a REAL (non-TESTING) app so the actual auth
path runs and g.user is genuinely populated from a real JWT -- that's the
only way to prove require_tool()/require_personal()/require_business()
actually block a route, not just that they're wired in.
"""
from unittest.mock import patch

import pytest

from app import create_app, db
from app.models import User
from app.services.auth import create_token
from app.services.entitlements import set_entitlements


@pytest.fixture
def real_client(tmp_path, monkeypatch):
    from app.config import Config
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{tmp_path}/gating_test.db")
    app = create_app()
    with app.test_client() as c:
        yield app, c


def _make_user(app, email, has_personal=False, has_business=False):
    with app.app_context():
        user = User(email=email, name="Gating Test", is_active=True, email_verified=True,
                    has_personal=has_personal, has_business=has_business)
        db.session.add(user)
        db.session.commit()
        return user.id


def _token(app, email, has_personal=False, has_business=False):
    with app.app_context():
        return create_token(sub=email, name="Gating Test",
                             has_personal=has_personal, has_business=has_business)


def test_personal_tool_blocked_without_app_access(real_client):
    # No has_personal at all -- blocked before require_tool() even matters.
    app, c = real_client
    user_id = _make_user(app, "gating-no-personal@example.com", has_personal=False)
    with app.app_context():
        set_entitlements(user_id, {"linux"}, source="self_service", app="personal")
    token = _token(app, "gating-no-personal@example.com", has_personal=False)

    rv = c.post("/api/linux", json={"problem": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_personal_tool_blocked_without_entitlement(real_client):
    app, c = real_client
    _make_user(app, "gating-personal@example.com", has_personal=True)
    token = _token(app, "gating-personal@example.com", has_personal=True)

    rv = c.post("/api/linux", json={"problem": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_personal_tool_allowed_with_access_and_entitlement(real_client):
    app, c = real_client
    user_id = _make_user(app, "gating-personal2@example.com", has_personal=True)
    with app.app_context():
        set_entitlements(user_id, {"linux"}, source="self_service")
    token = _token(app, "gating-personal2@example.com", has_personal=True)

    mock_resp = {"gui_steps": [], "command": "ls", "explanation": "", "warnings": ["None."]}
    with patch("app.routes.linux_helper.claude_client.call", return_value=mock_resp):
        rv = c.post("/api/linux", json={"problem": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200


def test_business_tool_blocked_without_app_access(real_client):
    app, c = real_client
    _make_user(app, "gating-business@example.com", has_business=False)
    token = _token(app, "gating-business@example.com", has_business=False)

    rv = c.post("/api/biz/hiring-manager", json={"description": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_business_tool_allowed_with_access_and_entitlement(real_client):
    app, c = real_client
    user_id = _make_user(app, "gating-business2@example.com", has_business=True)
    with app.app_context():
        set_entitlements(user_id, {"hiring"}, source="self_service")
    token = _token(app, "gating-business2@example.com", has_business=True)

    mock_resp = {
        "job_title": "x", "position_summary": "x", "interview_questions": [],
        "evaluation_criteria": [], "red_flags": [], "onboarding_tips": [],
    }
    with patch("app.routes.biz_tools.claude_client.call", return_value=mock_resp):
        rv = c.post("/api/biz/hiring-manager", json={"description": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200


def test_business_access_gate_still_enforced_even_with_entitlement(real_client):
    # A user with a "hiring" entitlement row but no has_business still can't
    # reach a Business route -- require_tool() is an ADDITIONAL restriction
    # layered on top of require_business(), not a replacement for it.
    app, c = real_client
    user_id = _make_user(app, "gating-no-biz-access-with-tool@example.com", has_business=False)
    with app.app_context():
        set_entitlements(user_id, {"hiring"}, source="admin_manual")
    token = _token(app, "gating-no-biz-access-with-tool@example.com", has_business=False)

    rv = c.post("/api/biz/hiring-manager", json={"description": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_personal_access_independent_of_business_access(real_client):
    # Personal and Business are separate products -- having one doesn't
    # imply the other.
    app, c = real_client
    _make_user(app, "gating-personal-only@example.com", has_personal=True, has_business=False)
    token = _token(app, "gating-personal-only@example.com", has_personal=True, has_business=False)

    rv = c.post("/api/biz/hiring-manager", json={"description": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_demo_bypasses_access_and_entitlement_checks(real_client):
    app, c = real_client
    token = _token(app, "demo")  # demo has no User row and no access flags at all

    mock_resp = {"gui_steps": [], "command": "ls", "explanation": "", "warnings": ["None."]}
    with patch("app.routes.linux_helper.claude_client.call", return_value=mock_resp):
        rv = c.post("/api/linux", json={"problem": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200
