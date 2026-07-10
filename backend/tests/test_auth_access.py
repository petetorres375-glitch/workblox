import uuid
from unittest.mock import patch

import pytest

from app.models import User


@pytest.fixture
def cleanup_emails():
    created = []
    yield created
    from app import db
    for email in created:
        User.query.filter_by(email=email).delete()
    db.session.commit()


def _unique_email(cleanup_emails, label):
    email = f"{label}-{uuid.uuid4()}@example.com"
    cleanup_emails.append(email)
    return email


def test_register_from_personal_origin_grants_only_personal(client, cleanup_emails):
    email = _unique_email(cleanup_emails, "reg-personal")
    rv = client.post("/api/auth/register",
                      json={"email": email, "name": "Reg Test", "password": "password123"},
                      headers={"Origin": "http://localhost:5173"})
    assert rv.status_code == 201
    user = User.query.filter_by(email=email).first()
    assert user.has_personal is True
    assert user.has_business is False


def test_register_from_business_origin_grants_only_business(client, cleanup_emails):
    email = _unique_email(cleanup_emails, "reg-business")
    rv = client.post("/api/auth/register",
                      json={"email": email, "name": "Reg Test", "password": "password123"},
                      headers={"Origin": "http://localhost:5174"})
    assert rv.status_code == 201
    user = User.query.filter_by(email=email).first()
    assert user.has_personal is False
    assert user.has_business is True


def _mock_google_info(email, name="Google Test"):
    return {"email": email, "name": name}


def test_google_login_new_user_from_personal_origin(client, cleanup_emails):
    email = _unique_email(cleanup_emails, "google-personal")
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=_mock_google_info(email)):
        rv = client.post("/api/auth/google", json={"credential": "fake"},
                          headers={"Origin": "http://localhost:5173"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["has_personal"] is True
    assert data["has_business"] is False


def test_google_login_new_user_from_business_origin(client, cleanup_emails):
    email = _unique_email(cleanup_emails, "google-business")
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=_mock_google_info(email)):
        rv = client.post("/api/auth/google", json={"credential": "fake"},
                          headers={"Origin": "http://localhost:5174"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["has_personal"] is False
    assert data["has_business"] is True


def test_owner_google_login_gets_both_regardless_of_origin(client, cleanup_emails):
    owner_email = "pete.torres.375@gmail.com"
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=_mock_google_info(owner_email, "Pedro")):
        rv = client.post("/api/auth/google", json={"credential": "fake"},
                          headers={"Origin": "http://localhost:5173"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["has_personal"] is True
    assert data["has_business"] is True


def test_demo_login_always_grants_both(client):
    from app import create_app
    demo_app = create_app(testing=True)
    demo_app.config["DEMO_PASSWORD"] = "test-demo-pw"
    with demo_app.test_client() as demo_client:
        rv = demo_client.post("/api/auth/demo", json={"password": "test-demo-pw"})
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["has_personal"] is True
        assert data["has_business"] is True
