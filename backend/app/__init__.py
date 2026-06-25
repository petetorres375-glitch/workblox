from flask import Flask
from flask_cors import CORS

from .config import Config


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    if testing:
        app.config["TESTING"] = True

    allowed_origins = [
        "https://petetorres375-glitch.github.io",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    CORS(app, origins=allowed_origins)

    from .routes import register_blueprints
    register_blueprints(app)

    return app
