from datetime import datetime, timezone

# Keyed exactly the way each frontend's own NAV_IDS/TOOLS maps already key
# these tools, so the API hands back an id both apps already know how to
# route on -- no second id scheme to keep in sync.
TOOL_SEED = [
    # (key, name, app)
    ("ats", "ATS Analyzer", "personal"),
    ("doc", "Doc Analyzer", "personal"),
    ("linux", "Linux Helper", "personal"),
    ("mac", "Mac Helper", "personal"),
    ("resume", "Resume Builder", "personal"),
    ("windows", "Windows Helper", "personal"),
    ("workflow", "Workflow Builder", "personal"),
    ("ad-copy", "Ad Copy Writer", "business"),
    ("batch-ats", "Batch ATS Analyzer", "business"),
    ("email", "Business Email Drafter", "business"),
    ("contacts", "Contacts", "business"),
    ("contract", "Contract Analyzer", "business"),
    ("customer", "Customer Response Drafter", "business"),
    ("data-cleanup", "Data Cleanup", "business"),
    ("expenses", "Expense Organizer", "business"),
    ("hiring", "Hiring Manager", "business"),
    ("job-desc", "Job Description Writer", "business"),
    ("meeting", "Meeting Notes Cleaner", "business"),
    ("policy", "Policy Generator", "business"),
    ("proposal", "Proposal Generator", "business"),
    ("review", "Review Request Email", "business"),
    ("social", "Social Media Generator", "business"),
    ("sop", "SOP Generator", "business"),
]

def seed_tools():
    """Insert any tool from TOOL_SEED not already in the `tools` table.
    Safe to call on every startup -- existing rows are left untouched."""
    from .. import db
    from ..models import Tool

    existing_keys = {t.key for t in Tool.query.all()}
    added = False
    for key, name, app in TOOL_SEED:
        if key not in existing_keys:
            db.session.add(Tool(key=key, name=name, app=app))
            added = True
    if added:
        db.session.commit()


def get_enabled_tool_keys(user_id, app: str = None) -> set:
    """Every tool key this user currently has enabled. Pass app="personal" or
    "business" to scope to just that app's tools (plus "both") -- both
    frontends must always pass this, since a Business-plan user's entitlements
    otherwise leak across apps that share this one backend/DB (e.g. Personal's
    Settings page showing a count that silently includes Business tools it
    never displays)."""
    from ..models import Tool, UserEntitlement

    query = (
        UserEntitlement.query
        .join(Tool, Tool.id == UserEntitlement.tool_id)
        .filter(UserEntitlement.user_id == user_id)
    )
    if app:
        query = query.filter(Tool.app.in_([app, "both"]))
    rows = query.with_entities(Tool.key).all()
    return {key for (key,) in rows}


def user_has_tool(user_id, tool_key: str) -> bool:
    return tool_key in get_enabled_tool_keys(user_id)


def require_tool(tool_key: str):
    """Route guard, same shape as the existing _require_business() checks:
    returns a 403 JSON response if the current user doesn't have this tool
    enabled, or None if they're clear to proceed. Demo sessions have no User
    row and no entitlements at all, so they bypass this check entirely and
    keep seeing every tool, same as before this feature existed."""
    from flask import g, jsonify

    from ..models import User

    sub = g.user.get("sub", "")
    if sub == "demo":
        return None
    user = User.query.filter_by(email=sub).first() if sub else None
    if not user or not user_has_tool(user.id, tool_key):
        return jsonify({"error": "This tool isn't enabled on your account."}), 403
    return None


def _apply_entitlement(user_id, tool, enabled: bool, source: str):
    """Mutates the session but does not commit -- callers commit once.
    Disabling a tool only revokes access -- it never deletes the underlying
    data (e.g. a client's saved Contacts). Re-enabling the tool later
    restores whatever was there before."""
    from .. import db
    from ..models import UserEntitlement

    existing = UserEntitlement.query.filter_by(user_id=user_id, tool_id=tool.id).first()
    if enabled:
        if not existing:
            db.session.add(UserEntitlement(
                user_id=user_id,
                tool_id=tool.id,
                enabled_at=datetime.now(timezone.utc),
                source=source,
            ))
    else:
        if existing:
            db.session.delete(existing)


def set_entitlement(user_id, tool_key: str, enabled: bool, source: str):
    """Add or remove a single tool entitlement (the admin one-tool-at-a-time
    path). Shares _apply_entitlement with set_entitlements so this can
    never drift from the self-service route."""
    from .. import db
    from ..models import Tool

    tool = Tool.query.filter_by(key=tool_key).first()
    if not tool:
        raise ValueError(f"Unknown tool key: {tool_key}")
    _apply_entitlement(user_id, tool, enabled, source)
    db.session.commit()


def set_entitlements(user_id, tool_keys, source: str, app: str = None):
    """Replace a user's selection in one call. Used only for a brand-new
    user's FIRST pick at signup (source="self_service", immediate) and for
    admin/backfill bulk grants -- Settings' ongoing self-service edits go
    through sync_tool_selection() instead, since new additions there need
    approval rather than immediate access. Diffs against what's already
    enabled so untouched tools keep their original enabled_at/source instead
    of being rewritten. Pass app= to scope the diff to just that app's tools
    -- otherwise saving Personal's picker would wipe out a Business-plan
    user's Business entitlements entirely, since this function has no other
    way to know they're out of scope."""
    from .. import db
    from ..models import Tool

    current = get_enabled_tool_keys(user_id, app=app)
    target = set(tool_keys)
    relevant_keys = current | target
    tools_by_key = {t.key: t for t in Tool.query.filter(Tool.key.in_(relevant_keys)).all()}

    for key in target - current:
        _apply_entitlement(user_id, tools_by_key[key], True, source)
    for key in current - target:
        _apply_entitlement(user_id, tools_by_key[key], False, source)

    db.session.commit()


def get_pending_request_keys(user_id, app: str = None) -> set:
    """Tool keys this user has an open (unapproved) request for."""
    from ..models import Tool, ToolRequest

    query = (
        ToolRequest.query
        .join(Tool, Tool.id == ToolRequest.tool_id)
        .filter(ToolRequest.user_id == user_id)
    )
    if app:
        query = query.filter(Tool.app.in_([app, "both"]))
    rows = query.with_entities(Tool.key).all()
    return {key for (key,) in rows}


def sync_tool_selection(user_id, tool_keys, app: str):
    """Settings' ongoing self-service save. Unlike set_entitlements(), a
    NEWLY checked tool doesn't take effect immediately -- it becomes a
    pending ToolRequest for Pedro to grant or dismiss. Removing a tool the
    user already has active still happens immediately (giving up access
    needs no approval). Unchecking a tool that was only pending just
    cancels that request. Returns the resulting
    (active_keys, pending_keys), both scoped to `app`."""
    from .. import db
    from ..models import Tool, ToolRequest

    current_active = get_enabled_tool_keys(user_id, app=app)
    current_pending = get_pending_request_keys(user_id, app=app)
    target = set(tool_keys)

    to_remove_active = current_active - target
    to_cancel_pending = current_pending - target
    to_request = target - current_active - current_pending

    relevant_keys = to_remove_active | to_request | to_cancel_pending
    tools_by_key = {t.key: t for t in Tool.query.filter(Tool.key.in_(relevant_keys)).all()}

    for key in to_remove_active:
        _apply_entitlement(user_id, tools_by_key[key], False, "self_service")

    if to_cancel_pending:
        cancel_tool_ids = [tools_by_key[key].id for key in to_cancel_pending]
        (ToolRequest.query
            .filter(ToolRequest.user_id == user_id, ToolRequest.tool_id.in_(cancel_tool_ids))
            .delete(synchronize_session=False))

    for key in to_request:
        db.session.add(ToolRequest(user_id=user_id, tool_id=tools_by_key[key].id))

    db.session.commit()
    return (
        get_enabled_tool_keys(user_id, app=app),
        get_pending_request_keys(user_id, app=app),
    )


def list_pending_requests():
    """Every open tool request across all clients, for the admin queue."""
    from ..models import Tool, ToolRequest, User

    rows = (
        ToolRequest.query
        .join(Tool, Tool.id == ToolRequest.tool_id)
        .join(User, User.id == ToolRequest.user_id)
        .with_entities(
            ToolRequest.id, User.id, User.name, User.email,
            Tool.key, Tool.name, Tool.app, ToolRequest.requested_at,
        )
        .order_by(ToolRequest.requested_at.asc())
        .all()
    )
    return [
        {
            "request_id": request_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_email": user_email,
            "tool_key": tool_key,
            "tool_name": tool_name,
            "app": app,
            "requested_at": requested_at.isoformat() if requested_at else None,
        }
        for request_id, user_id, user_name, user_email, tool_key, tool_name, app, requested_at in rows
    ]


def grant_tool_request(request_id):
    """Admin approves a pending request: create the real entitlement via
    set_entitlement() (source="admin_manual") so this can never drift from
    the existing manual-grant path, then remove the request."""
    from .. import db
    from ..models import Tool, ToolRequest

    req = db.session.get(ToolRequest, request_id)
    if not req:
        raise ValueError("Request not found")
    tool = db.session.get(Tool, req.tool_id)
    set_entitlement(req.user_id, tool.key, True, source="admin_manual")
    db.session.delete(req)
    db.session.commit()


def dismiss_tool_request(request_id):
    """Admin declines a pending request without granting anything."""
    from .. import db
    from ..models import ToolRequest

    req = db.session.get(ToolRequest, request_id)
    if not req:
        raise ValueError("Request not found")
    db.session.delete(req)
    db.session.commit()
