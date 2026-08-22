import os

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

# Railway injects these for GitHub-connected services. Empty locally, which is
# why the response falls back to "unknown" rather than omitting the keys.
_COMMIT = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "")
_BRANCH = os.environ.get("RAILWAY_GIT_BRANCH", "")


@bp.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "commit": _COMMIT[:7] or "unknown",
            "branch": _BRANCH or "unknown",
        }
    )
