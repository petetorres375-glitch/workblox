from flask import Blueprint, jsonify, request

from app import limiter
from app.services import claude_client

bp = Blueprint("mac_helper", __name__)

SYSTEM_PROMPT = """\
You are a macOS expert. The user will describe a problem or task in plain English.
Return a JSON object with exactly these four keys:
- "gui_steps": A list of step-by-step instructions to accomplish the task using the macOS GUI (System Settings, Finder, right-click menus, menu bar, etc.). Write each step as a clear action, e.g. "Open System Settings > General > Software Update". If no GUI method exists, return ["No GUI method available for this task."].
- "command": The recommended macOS Terminal command or sequence of commands (as a string).
- "explanation": A plain-English explanation of what the command does and why it works.
- "warnings": A list of cautions or side effects the user should know. If none, return ["None."].

Return only valid JSON. No markdown fences, no extra text.
"""


@bp.post("/api/mac")
@limiter.limit("20 per hour")
def mac_helper():
    body = request.get_json(silent=True) or {}
    problem = (body.get("problem") or "").strip()
    if not problem:
        return jsonify({"error": "problem is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Problem: {problem}",
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(result)
