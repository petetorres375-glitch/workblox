"""Personal and Business are separate paid products -- these guards check
whether the current user has been granted the app they're calling into,
independent of (and checked before) any per-tool entitlement via
require_tool(). Demo sessions have no User row and bypass both checks
entirely, same as they already bypass require_tool()."""
from flask import g, jsonify


def require_personal():
    if g.user.get("sub") == "demo":
        return None
    if not g.user.get("has_personal"):
        return jsonify({"error": "Personal access required."}), 403
    return None


def require_business():
    if g.user.get("sub") == "demo":
        return None
    if not g.user.get("has_business"):
        return jsonify({"error": "Business access required."}), 403
    return None
