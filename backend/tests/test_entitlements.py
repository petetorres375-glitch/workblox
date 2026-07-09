import uuid
from unittest.mock import patch

import pytest

from app.models import Tool, User, UserEntitlement


def _as_user(user_id):
    # TESTING mode skips auth entirely (see app/__init__.py::require_auth), so
    # g.user is never set. Patching _user_id() the same way test_biz_tools.py
    # patches _require_business() isolates these tests to entitlement logic,
    # not JWT/session handling.
    return patch("app.routes.entitlements._user_id", return_value=user_id)


@pytest.fixture
def test_user(client):
    from app import db

    with client.application.app_context():
        user = User(
            email=f"entitlements-test-{uuid.uuid4()}@example.com",
            name="Entitlements Test",
            is_active=True,
            email_verified=True,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    yield user_id
    with client.application.app_context():
        UserEntitlement.query.filter_by(user_id=user_id).delete()
        User.query.filter_by(id=user_id).delete()
        db.session.commit()


def test_seed_tools_creates_all_21(client):
    with client.application.app_context():
        assert Tool.query.count() == 21
        assert Tool.query.filter_by(key="contacts").first().app == "business"
        assert Tool.query.filter_by(key="resume").first().app == "personal"


def test_list_tools_filtered_to_personal(client):
    rv = client.get("/api/tools?app=personal")
    assert rv.status_code == 200
    keys = {t["key"] for t in rv.get_json()}
    assert keys == {"ats", "doc", "linux", "mac", "resume", "windows", "workflow"}


def test_list_tools_filtered_to_business(client):
    rv = client.get("/api/tools?app=business")
    assert rv.status_code == 200
    keys = {t["key"] for t in rv.get_json()}
    assert len(keys) == 14
    assert "contacts" in keys


def test_get_entitlements_empty_for_new_user(client, test_user):
    with _as_user(test_user):
        rv = client.get("/api/entitlements")
    assert rv.status_code == 200
    assert rv.get_json()["tool_keys"] == []


def test_put_entitlements_sets_selection(client, test_user):
    with _as_user(test_user):
        rv = client.put("/api/entitlements", json={"tool_keys": ["resume", "doc"]})
    assert rv.status_code == 200
    assert sorted(rv.get_json()["tool_keys"]) == ["doc", "resume"]

    with _as_user(test_user):
        rv = client.get("/api/entitlements")
    assert sorted(rv.get_json()["tool_keys"]) == ["doc", "resume"]


def test_put_entitlements_can_change_selection(client, test_user):
    with _as_user(test_user):
        client.put("/api/entitlements", json={"tool_keys": ["resume", "doc"]})
        rv = client.put("/api/entitlements", json={"tool_keys": ["ats"]})
    assert rv.status_code == 200
    assert rv.get_json()["tool_keys"] == ["ats"]


def test_put_entitlements_rejects_empty_selection(client, test_user):
    with _as_user(test_user):
        rv = client.put("/api/entitlements", json={"tool_keys": []})
    assert rv.status_code == 400


def test_put_entitlements_rejects_unknown_key(client, test_user):
    with _as_user(test_user):
        rv = client.put("/api/entitlements", json={"tool_keys": ["not-a-real-tool"]})
    assert rv.status_code == 400


def test_removing_contacts_deletes_contact_rows(client, test_user):
    from app import db
    from app.models import Contact

    with client.application.app_context():
        db.session.add(Contact(user_id=test_user, first_name="Jane", last_name="Doe"))
        db.session.commit()

    with _as_user(test_user):
        client.put("/api/entitlements", json={"tool_keys": ["contacts", "resume"]})

    with client.application.app_context():
        assert Contact.query.filter_by(user_id=test_user).count() == 1

    with _as_user(test_user):
        rv = client.put("/api/entitlements", json={"tool_keys": ["resume"]})
    assert rv.status_code == 200

    with client.application.app_context():
        assert Contact.query.filter_by(user_id=test_user).count() == 0


def test_set_entitlement_single_tool_for_admin_path(client, test_user):
    from app.services.entitlements import get_enabled_tool_keys, set_entitlement

    with client.application.app_context():
        set_entitlement(test_user, "hiring", True, source="admin_manual")
        assert get_enabled_tool_keys(test_user) == {"hiring"}
        row = UserEntitlement.query.filter_by(user_id=test_user).first()
        assert row.source == "admin_manual"

        set_entitlement(test_user, "hiring", False, source="admin_manual")
        assert get_enabled_tool_keys(test_user) == set()
