from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

from .config import Config

limiter = Limiter(key_func=get_remote_address, default_limits=["60 per hour"])
db = SQLAlchemy()

_PUBLIC_PREFIXES = ("/api/auth/", "/health")


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    if testing:
        app.config["TESTING"] = True
        limiter.enabled = False

    allowed_origins = [
        "https://petetorres375-glitch.github.io",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    CORS(app, origins=allowed_origins)
    limiter.init_app(app)
    db.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401 — ensure models are registered
        db.create_all()

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Too many requests — please wait a moment and try again."}), 429

    @app.before_request
    def require_auth():
        if app.config.get("TESTING"):
            return
        if request.method == "OPTIONS":
            return
        if any(request.path.startswith(p) for p in _PUBLIC_PREFIXES):
            return
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401
        token = auth_header[7:]
        try:
            from .services.auth import decode_token
            g.user = decode_token(token)
        except Exception:
            return jsonify({"error": "Invalid or expired session"}), 401

    from .routes import register_blueprints
    register_blueprints(app)

    return app
