from flask import Blueprint, request, jsonify, current_app, redirect
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import User
from ..services.auth import create_token, decode_verification_token
from ..services.email import send_verification_email

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

_PENDING_MSG = "Your account is pending activation. You'll get access once your subscription is confirmed."


@bp.post("/register")
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""

    if not email or not name or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(email=email, name=name, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    email_sent = send_verification_email(email, name)
    if email_sent:
        msg = "Account created. Please check your email to verify your address."
    else:
        msg = "Account created. You'll receive access once your subscription is confirmed."

    return jsonify({"message": msg, "email_sent": email_sent}), 201


@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Incorrect email or password"}), 401
    if not user.email_verified:
        return jsonify({"error": "Please verify your email before signing in. Check your inbox."}), 403
    if not user.is_active:
        return jsonify({"error": _PENDING_MSG}), 403

    token = create_token(sub=user.email, name=user.name)
    return jsonify({"token": token, "name": user.name})


@bp.get("/verify/<token>")
def verify_email(token):
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    try:
        email = decode_verification_token(token)
    except Exception:
        return redirect(f"{frontend_url}?verified=false")

    user = User.query.filter_by(email=email).first()
    if user:
        user.email_verified = True
        db.session.commit()

    return redirect(f"{frontend_url}?verified=true")


@bp.post("/google")
def google_login():
    data = request.get_json() or {}
    credential = data.get("credential")
    if not credential:
        return jsonify({"error": "Missing credential"}), 400
    try:
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            current_app.config["GOOGLE_CLIENT_ID"],
        )
    except ValueError:
        return jsonify({"error": "Invalid Google token"}), 401

    email = info["email"].lower()
    name = info.get("name", email)

    _OWNER = {"pete.torres.375@gmail.com", "pedro_torres@torrestechremote.com"}

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, name=name, email_verified=True, is_active=(email in _OWNER))
        db.session.add(user)
        db.session.commit()

    if not user.is_active:
        return jsonify({"error": _PENDING_MSG}), 403

    token = create_token(sub=user.email, name=user.name)
    return jsonify({"token": token, "name": user.name})


@bp.post("/demo")
def demo_login():
    data = request.get_json() or {}
    password = data.get("password")
    demo_pw = current_app.config.get("DEMO_PASSWORD", "")
    if not demo_pw or password != demo_pw:
        return jsonify({"error": "Invalid"}), 401
    token = create_token(sub="demo", name="Pedro", hours=8)
    return jsonify({"token": token, "name": "Pedro"})
