from flask import Blueprint, jsonify, request

from app import limiter
from app.services import claude_client

bp = Blueprint("linux_helper", __name__)

SYSTEM_PROMPT = """\
You are a Linux expert. The user will describe a problem or task in plain English.
Return a JSON object with exactly these four keys:
- "gui_steps": A list of step-by-step instructions to accomplish the task using a Linux desktop GUI (GNOME, KDE, Nautilus, or common graphical tools). Write each step as a clear action. If no GUI method exists or the task is terminal-only, return ["No GUI method available for this task."].
- "command": The recommended Linux command or sequence of commands (as a string).
- "explanation": A plain-English explanation of what the command does and why it works.
- "warnings": A list of cautions or side effects the user should know. If none, return ["None."].

Return only valid JSON. No markdown fences, no extra text.
"""


@bp.post("/api/linux")
@limiter.limit("20 per hour")
def linux_helper():
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
