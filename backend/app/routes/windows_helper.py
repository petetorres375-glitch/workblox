from flask import Blueprint, jsonify, request

from app import limiter
from app.services import claude_client

bp = Blueprint("windows_helper", __name__)

SYSTEM_PROMPT = """\
You are a Windows PowerShell and Command Prompt expert. The user will describe a problem or task in plain English.
Return a JSON object with exactly these three keys:
- "command": The recommended PowerShell or CMD command (as a string). Prefer PowerShell for modern tasks.
- "explanation": A plain-English explanation of what the command does and why it works.
- "warnings": A list of cautions or side effects the user should know. If none, return ["None."].

Return only valid JSON. No markdown fences, no extra text.
"""


@bp.post("/api/windows")
@limiter.limit("20 per hour")
def windows_helper():
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
