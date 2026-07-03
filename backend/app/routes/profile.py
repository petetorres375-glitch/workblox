from flask import Blueprint, jsonify, request, g

from .. import db
from ..models import User

bp = Blueprint("profile", __name__, url_prefix="/api/profile")

# Keep this in sync with the frontend's supported language list (SUPPORTED_LANGUAGES
# in src/i18n.js, which is auto-derived from src/locales/*/) and claude_client.LANGUAGE_NAMES.
_SUPPORTED_LANGUAGES = {
    "en", "es", "fr", "de", "pt", "zh", "ja", "ko", "ar", "hi", "ru", "it",
    "nl", "pl", "tr", "vi", "th", "id", "sv", "uk", "el", "he", "cs", "ro",
}


@bp.patch("/language")
def set_language():
    language = (request.get_json(silent=True) or {}).get("language")
    if language not in _SUPPORTED_LANGUAGES:
        return jsonify({"error": "Unsupported language"}), 400

    # g.user comes from the JWT (set in before_request); "sub" is the user's email.
    # Demo logins have no email/DB row, so there's nothing to save — just no-op.
    email = g.user.get("sub", "")
    if not email or email == "demo":
        return jsonify({"language": language})

    user = User.query.filter_by(email=email).first()
    if user:
        user.language = language
        db.session.commit()

    return jsonify({"language": language})
