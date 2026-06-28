from flask import Blueprint, jsonify, g

from .. import db
from ..models import User

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

ADMIN_SUBS = {"demo", "pete.torres.375@gmail.com", "pedro_torres@torrestechremote.com"}


def _is_admin():
    return g.user.get("sub") in ADMIN_SUBS


@bp.get("/users")
def list_users():
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([
        {
            "email": u.email,
            "name": u.name,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ])


@bp.post("/users/<email>/activate")
def activate_user(email):
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.is_active = True
    db.session.commit()
    return jsonify({"message": f"{user.email} activated"})


@bp.post("/users/<email>/deactivate")
def deactivate_user(email):
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.is_active = False
    db.session.commit()
    return jsonify({"message": f"{user.email} deactivated"})
