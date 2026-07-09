from flask import Blueprint, g, jsonify, request

from ..models import Tool, User
from ..services.entitlements import get_enabled_tool_keys, set_entitlements

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
        return jsonify({"tool_keys": []})
    return jsonify({"tool_keys": sorted(get_enabled_tool_keys(user_id, app=app_filter))})


@bp.put("/entitlements")
def put_entitlements():
    user_id = _user_id()
    if user_id is None:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(silent=True) or {}
    tool_keys = body.get("tool_keys")
    app_filter = body.get("app")
    if not isinstance(tool_keys, list) or len(tool_keys) == 0:
        return jsonify({"error": "At least one tool must be selected"}), 400

    query = Tool.query.filter(Tool.key.in_(tool_keys))
    if app_filter in ("personal", "business"):
        query = query.filter(Tool.app.in_([app_filter, "both"]))
    valid_keys = {t.key for t in query.all()}
    unknown = set(tool_keys) - valid_keys
    if unknown:
        return jsonify({"error": f"Unknown tool key(s): {', '.join(sorted(unknown))}"}), 400

    set_entitlements(user_id, valid_keys, source="self_service", app=app_filter)
    return jsonify({"tool_keys": sorted(get_enabled_tool_keys(user_id, app=app_filter))})
