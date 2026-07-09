from flask import Blueprint, g, jsonify, request

from ..models import Tool, User
from ..services.entitlements import (
    get_enabled_tool_keys,
    get_pending_request_keys,
    set_entitlements,
    sync_tool_selection,
)

bp = Blueprint("entitlements", __name__, url_prefix="/api")


def _user_id():
    sub = g.user.get("sub")
    if not sub:
        return None
    user = User.query.filter_by(email=sub).first()
    return user.id if user else None


@bp.get("/tools")
def list_tools():
    app_filter = request.args.get("app")
    query = Tool.query
    if app_filter in ("personal", "business"):
        query = query.filter(Tool.app.in_([app_filter, "both"]))
    tools = query.order_by(Tool.key).all()
    return jsonify([{"key": t.key, "name": t.name, "app": t.app} for t in tools])


@bp.get("/entitlements")
def get_entitlements():
    user_id = _user_id()
    app_filter = request.args.get("app")
    if user_id is None:
        return jsonify({"tool_keys": [], "pending_keys": []})
    return jsonify({
        "tool_keys": sorted(get_enabled_tool_keys(user_id, app=app_filter)),
        "pending_keys": sorted(get_pending_request_keys(user_id, app=app_filter)),
    })


def _validate_tool_keys(tool_keys, app_filter):
    """Shared by PUT and /sync: returns (valid_keys, error_response_or_None)."""
    if not isinstance(tool_keys, list) or len(tool_keys) == 0:
        return None, (jsonify({"error": "At least one tool must be selected"}), 400)

    query = Tool.query.filter(Tool.key.in_(tool_keys))
    if app_filter in ("personal", "business"):
        query = query.filter(Tool.app.in_([app_filter, "both"]))
    valid_keys = {t.key for t in query.all()}
    unknown = set(tool_keys) - valid_keys
    if unknown:
        return None, (jsonify({"error": f"Unknown tool key(s): {', '.join(sorted(unknown))}"}), 400)
    return valid_keys, None


@bp.put("/entitlements")
def put_entitlements():
    """Immediate full-replace -- used only for a brand-new user's FIRST pick
    at signup, so they're not left staring at an empty app waiting on Pedro.
    Every later self-service change goes through /entitlements/sync instead."""
    user_id = _user_id()
    if user_id is None:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(silent=True) or {}
    app_filter = body.get("app")
    valid_keys, error = _validate_tool_keys(body.get("tool_keys"), app_filter)
    if error:
        return error

    set_entitlements(user_id, valid_keys, source="self_service", app=app_filter)
    return jsonify({"tool_keys": sorted(get_enabled_tool_keys(user_id, app=app_filter))})


@bp.post("/entitlements/sync")
def sync_entitlements():
    """Settings' ongoing self-service save. Removing an already-active tool
    still happens immediately; a newly checked tool becomes a pending
    request instead of taking effect right away."""
    user_id = _user_id()
    if user_id is None:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(silent=True) or {}
    app_filter = body.get("app")
    if app_filter not in ("personal", "business"):
        return jsonify({"error": "app must be 'personal' or 'business'"}), 400
    valid_keys, error = _validate_tool_keys(body.get("tool_keys"), app_filter)
    if error:
        return error

    active_keys, pending_keys = sync_tool_selection(user_id, valid_keys, app=app_filter)
    return jsonify({"tool_keys": sorted(active_keys), "pending_keys": sorted(pending_keys)})
