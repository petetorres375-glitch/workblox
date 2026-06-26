from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import Config

limiter = Limiter(key_func=get_remote_address, default_limits=["60 per hour"])


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

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Too many requests — please wait a moment and try again."}), 429

    from .routes import register_blueprints
    register_blueprints(app)

    return app
