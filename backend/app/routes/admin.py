from flask import Blueprint, jsonify, request, g

from .. import db
from ..models import User, AppConfig, Tool, UserEntitlement
from ..services.entitlements import (
    dismiss_tool_request,
    get_enabled_tool_keys,
    grant_tool_request,
    list_pending_requests,
    set_entitlement,
)

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

ADMIN_SUBS = {"demo", "pete.torres.375@gmail.com", "pedro_torres@torrestechremote.com"}

# Internal/test accounts -- excluded from the tool-selection dashboard so it
# reflects real client demand, not Pedro's own accounts or people testing the
# app on his behalf. Not the same set as ADMIN_SUBS (e.g. a tester here isn't
# an admin, and this list has nothing to do with API access).
DASHBOARD_EXCLUDED_EMAILS = {
    "pete.torres.375@gmail.com",
    "pedro_torres@torrestechremote.com",
    "berto@themissionfwd.com",
}


def _is_admin():
    return g.user.get("sub") in ADMIN_SUBS


@bp.get("/users")
def list_users():
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "is_active": u.is_active,
            "has_personal": u.has_personal,
            "has_business": u.has_business,
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


@bp.post("/users/<int:user_id>/access")
def set_user_access(user_id):
    # Personal and Business are separate paid products -- independent
    # toggles (partial update, same pattern as the kill-switch endpoint
    # below) rather than one mutually-exclusive plan, since a client can
    # have either, both, or neither.
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    body = request.get_json(silent=True) or {}
    if "has_personal" in body:
        user.has_personal = bool(body["has_personal"])
    if "has_business" in body:
        user.has_business = bool(body["has_business"])
    db.session.commit()
    return jsonify({"has_personal": user.has_personal, "has_business": user.has_business})


@bp.get("/kill-switch")
def get_kill_switch():
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    personal = db.session.get(AppConfig, "personal_enabled")
    business = db.session.get(AppConfig, "business_enabled")
    return jsonify({
        "personal_enabled": personal.value == "true" if personal else True,
        "business_enabled": business.value == "true" if business else True,
    })


@bp.post("/kill-switch")
def set_kill_switch():
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    body = request.get_json(silent=True) or {}
    results = {}
    for key in ("personal_enabled", "business_enabled"):
        if key in body:
            row = db.session.get(AppConfig, key)
            if not row:
                row = AppConfig(key=key, value="true")
                db.session.add(row)
            row.value = "true" if body[key] else "false"
            results[key] = body[key]
    db.session.commit()
    return jsonify(results)


@bp.get("/users/<int:user_id>/entitlements")
def get_user_entitlements(user_id):
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"tool_keys": sorted(get_enabled_tool_keys(user_id))})


@bp.post("/users/<int:user_id>/entitlements")
def set_user_entitlement(user_id):
    # Manual comp/support path -- writes to the exact same user_entitlements
    # table as the self-service picker (via the shared set_entitlement()
    # function), just tagged source="admin_manual" so the dashboard can tell
    # real client demand apart from comps. Nothing client-facing ever
    # surfaces that distinction.
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(silent=True) or {}
    tool_key = body.get("tool_key")
    enabled = bool(body.get("enabled"))
    if not tool_key or not Tool.query.filter_by(key=tool_key).first():
        return jsonify({"error": "Unknown tool_key"}), 400

    set_entitlement(user_id, tool_key, enabled, source="admin_manual")
    return jsonify({"tool_keys": sorted(get_enabled_tool_keys(user_id))})


@bp.get("/entitlements/summary")
def entitlements_summary():
    # Read-only, raw per-row feed -- Pedro's dashboard aggregates client-side
    # (by tool, by app, by source, by week) rather than this endpoint
    # committing to a fixed set of GROUP BY shapes. No user-identifying data
    # included; this is for tool-popularity reporting, not a user lookup.
    # Internal/test accounts are filtered out here (not just for one source
    # filter) so every view of the dashboard reflects real client activity.
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    rows = (
        UserEntitlement.query
        .join(Tool, Tool.id == UserEntitlement.tool_id)
        .join(User, User.id == UserEntitlement.user_id)
        .filter(~User.email.in_(DASHBOARD_EXCLUDED_EMAILS))
        .with_entities(Tool.key, Tool.name, Tool.app, UserEntitlement.source, UserEntitlement.enabled_at)
        .all()
    )
    return jsonify([
        {
            "tool_key": key,
            "tool_name": name,
            "app": app,
            "source": source,
            "enabled_at": enabled_at.isoformat() if enabled_at else None,
        }
        for key, name, app, source, enabled_at in rows
    ])


@bp.get("/tool-requests")
def list_tool_requests():
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(list_pending_requests())


@bp.post("/tool-requests/<int:request_id>/grant")
def grant_tool_request_route(request_id):
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    try:
        grant_tool_request(request_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify({"granted": True})


@bp.post("/tool-requests/<int:request_id>/dismiss")
def dismiss_tool_request_route(request_id):
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    try:
        dismiss_tool_request(request_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify({"dismissed": True})
