from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

from .config import Config

limiter = Limiter(key_func=get_remote_address, default_limits=["60 per hour"])
db = SQLAlchemy()

_PUBLIC_PREFIXES = ("/api/auth/", "/api/health")


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    if testing:
        app.config["TESTING"] = True
        limiter.enabled = False

    allowed_origins = Config.ALLOWED_ORIGINS
    CORS(app, origins=allowed_origins)

    @app.after_request
    def _force_cors(response):
        origin = request.headers.get("Origin", "")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE, PATCH"
            response.headers["Vary"] = "Origin"
        return response

    @app.errorhandler(500)
    def _server_error(e):
        return jsonify({"error": "Internal server error — check logs"}), 500

    limiter.init_app(app)
    db.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401 — ensure models are registered
        db.create_all()
        from sqlalchemy import text
        try:
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN plan VARCHAR(50) NOT NULL DEFAULT 'free'"
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN language VARCHAR(10)"
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN has_personal BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            db.session.commit()
            # One-time backfill, tied to this column being created for the
            # first time: every existing user has been using Personal for
            # free until now (it had no gate at all), so grandfather them in
            # rather than lock them out the moment this deploys. A future
            # boot where the column already exists hits the except branch
            # and skips this -- it can only ever run once, at the instant
            # the column is introduced, before any new signup could exist.
            db.session.execute(text("UPDATE users SET has_personal = TRUE"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN has_business BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            db.session.commit()
            # Same one-time backfill for Business: copy whatever the old
            # `plan` column already said. `plan` itself is left in place
            # (unused, harmless) rather than dropped -- this app never runs
            # column-removing migrations.
            db.session.execute(text("UPDATE users SET has_business = TRUE WHERE plan = 'business'"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # seed kill-switch rows if missing
        from .models import AppConfig
        for key, val in [("personal_enabled", "true"), ("business_enabled", "true")]:
            if not db.session.get(AppConfig, key):
                db.session.add(AppConfig(key=key, value=val))
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        from .services.entitlements import seed_tools
        seed_tools()

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

        # Kill switch — admin routes are exempt so Pedro can re-enable; profile and
        # entitlement routes are exempt because they're shared account settings, not
        # an app-specific AI feature. Without this, a Business user's own /api/tools
        # or /api/entitlements call would incorrectly get checked against
        # personal_enabled, since neither path starts with /api/biz.
        _KILL_SWITCH_EXEMPT_PREFIXES = ("/api/admin", "/api/profile", "/api/tools", "/api/entitlements")
        if not any(request.path.startswith(p) for p in _KILL_SWITCH_EXEMPT_PREFIXES):
            from .models import AppConfig
            if request.path.startswith("/api/biz"):
                cfg = db.session.get(AppConfig, "business_enabled")
                if cfg and cfg.value != "true":
                    return jsonify({"error": "Workblox Business is temporarily unavailable."}), 503
            else:
                cfg = db.session.get(AppConfig, "personal_enabled")
                if cfg and cfg.value != "true":
                    return jsonify({"error": "Workblox is temporarily unavailable."}), 503

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401
        token = auth_header[7:]
        try:
            from .services.auth import decode_token
            g.user = decode_token(token)
        except Exception:
            return jsonify({"error": "Invalid or expired session"}), 401

        # is_active check — skip for demo (no DB row) and admin routes
        sub = g.user.get("sub", "")
        if sub and sub != "demo" and not request.path.startswith("/api/admin"):
            from .models import User
            user_row = User.query.filter_by(email=sub).first()
            if user_row and not user_row.is_active:
                return jsonify({"error": "Account is not active. Contact pedro_torres@torrestechremote.com."}), 401

    from .routes import register_blueprints
    register_blueprints(app)

    return app
