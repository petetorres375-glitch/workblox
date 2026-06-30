import json
import os
import re
from datetime import datetime, timezone

_blocklist = None


def _load_blocklist():
    global _blocklist
    if _blocklist is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "blocklist.json")
        with open(os.path.normpath(config_path)) as f:
            _blocklist = json.load(f)
    return _blocklist


def check(user_message: str, user_sub: str = None, app: str = None) -> None:
    """Raise ModerationError if user_message matches any blocked category."""
    # auto-detect context from Flask request if not provided
    if user_sub is None or app is None:
        try:
            from flask import g, request
            if user_sub is None:
                user_sub = (g.user or {}).get("sub") if hasattr(g, "user") else None
            if app is None:
                app = "business" if request.path.startswith("/api/biz") else "personal"
        except RuntimeError:
            pass  # outside request context (tests, CLI)

    blocklist = _load_blocklist()
    for category, patterns in blocklist.items():
        for pattern in patterns:
            if re.search(pattern, user_message):
                _log(category, user_sub, app)
                raise ModerationError(category)


def _log(category: str, user_sub: str, app: str):
    try:
        from .. import db
        from ..models import ModerationLog
        entry = ModerationLog(
            category=category,
            user_sub=user_sub,
            app=app,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        pass  # never let logging crash the moderation check


class ModerationError(Exception):
    def __init__(self, category: str):
        self.category = category
        super().__init__(f"Request blocked: {category}")
