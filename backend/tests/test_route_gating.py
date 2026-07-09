"""
Route-level entitlement enforcement. Unlike the other route tests, these
deliberately use a REAL (non-TESTING) app so the actual auth path runs and
g.user is genuinely populated from a real JWT -- that's the only way to
prove require_tool() actually blocks a route, not just that it's wired in.
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


def _make_user(app, email, plan):
    with app.app_context():
        user = User(email=email, name="Gating Test", is_active=True, email_verified=True, plan=plan)
        db.session.add(user)
        db.session.commit()
        return user.id


def _token(app, email, plan):
    with app.app_context():
        return create_token(sub=email, name="Gating Test", plan=plan)


def test_personal_tool_blocked_without_entitlement(real_client):
    app, c = real_client
    _make_user(app, "gating-personal@example.com", plan="free")
    token = _token(app, "gating-personal@example.com", plan="free")

    rv = c.post("/api/linux", json={"problem": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_personal_tool_allowed_with_entitlement(real_client):
    app, c = real_client
    user_id = _make_user(app, "gating-personal2@example.com", plan="free")
    with app.app_context():
        set_entitlements(user_id, {"linux"}, source="self_service")
    token = _token(app, "gating-personal2@example.com", plan="free")

    mock_resp = {"gui_steps": [], "command": "ls", "explanation": "", "warnings": ["None."]}
    with patch("app.routes.linux_helper.claude_client.call", return_value=mock_resp):
        rv = c.post("/api/linux", json={"problem": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200


def test_business_tool_blocked_without_entitlement(real_client):
    app, c = real_client
    _make_user(app, "gating-business@example.com", plan="business")
    token = _token(app, "gating-business@example.com", plan="business")

    rv = c.post("/api/biz/hiring-manager", json={"description": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_business_tool_allowed_with_entitlement(real_client):
    app, c = real_client
    user_id = _make_user(app, "gating-business2@example.com", plan="business")
    with app.app_context():
        set_entitlements(user_id, {"hiring"}, source="self_service")
    token = _token(app, "gating-business2@example.com", plan="business")

    mock_resp = {
        "job_title": "x", "position_summary": "x", "interview_questions": [],
        "evaluation_criteria": [], "red_flags": [], "onboarding_tips": [],
    }
    with patch("app.routes.biz_tools.claude_client.call", return_value=mock_resp):
        rv = c.post("/api/biz/hiring-manager", json={"description": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200


def test_business_plan_gate_still_enforced_even_with_entitlement(real_client):
    # A free-plan user who somehow has a "hiring" entitlement row still can't
    # reach a Business route -- require_tool() is an ADDITIONAL restriction
    # layered on top of _require_business(), not a replacement for it.
    app, c = real_client
    user_id = _make_user(app, "gating-free-with-biz-tool@example.com", plan="free")
    with app.app_context():
        set_entitlements(user_id, {"hiring"}, source="admin_manual")
    token = _token(app, "gating-free-with-biz-tool@example.com", plan="free")

    rv = c.post("/api/biz/hiring-manager", json={"description": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403


def test_demo_bypasses_entitlement_check(real_client):
    app, c = real_client
    token = _token(app, "demo", plan="free")  # demo has no User row at all

    mock_resp = {"gui_steps": [], "command": "ls", "explanation": "", "warnings": ["None."]}
    with patch("app.routes.linux_helper.claude_client.call", return_value=mock_resp):
        rv = c.post("/api/linux", json={"problem": "x"}, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200
