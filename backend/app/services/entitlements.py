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
    ("hiring", "Hiring Manager", "business"),
    ("job-desc", "Job Description Writer", "business"),
    ("meeting", "Meeting Notes Cleaner", "business"),
    ("policy", "Policy Generator", "business"),
    ("proposal", "Proposal Generator", "business"),
    ("review", "Review Request Email", "business"),
    ("social", "Social Media Generator", "business"),
    ("sop", "SOP Generator", "business"),
]

CONTACTS_TOOL_KEY = "contacts"


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
    """Mutates the session but does not commit -- callers commit once."""
    from .. import db
    from ..models import Contact, UserEntitlement

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
        if tool.key == CONTACTS_TOOL_KEY:
            Contact.query.filter_by(user_id=user_id).delete()


def set_entitlement(user_id, tool_key: str, enabled: bool, source: str):
    """Add or remove a single tool entitlement (the admin one-tool-at-a-time
    path). Shares _apply_entitlement with set_entitlements so the Contacts
    delete-on-remove behavior can never drift between the self-service and
    admin routes."""
    from .. import db
    from ..models import Tool

    tool = Tool.query.filter_by(key=tool_key).first()
    if not tool:
        raise ValueError(f"Unknown tool key: {tool_key}")
    _apply_entitlement(user_id, tool, enabled, source)
    db.session.commit()


def set_entitlements(user_id, tool_keys, source: str, app: str = None):
    """Replace a user's selection in one call (the self-service picker).
    Diffs against what's already enabled so untouched tools keep their
    original enabled_at/source instead of being rewritten. Pass app= to scope
    the diff to just that app's tools -- otherwise saving Personal's picker
    would wipe out a Business-plan user's Business entitlements entirely,
    since this function has no other way to know they're out of scope."""
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
