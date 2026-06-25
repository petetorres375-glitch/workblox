from flask import Flask
from flask_cors import CORS

from .config import Config


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    if testing:
        app.config["TESTING"] = True

    CORS(app)

    from .routes import register_blueprints
    register_blueprints(app)

    return app
