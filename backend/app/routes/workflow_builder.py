from flask import Blueprint, jsonify, request

from app.services import claude_client

bp = Blueprint("workflow_builder", __name__)

SYSTEM_PROMPT = """\
You are a Python automation expert. The user will describe a repetitive task they want to automate.
Generate a ready-to-run Python script that automates it.

Return a JSON object with exactly two keys:
- "filename": A short, descriptive snake_case filename ending in .py (e.g. "rename_photos.py"). No path, just the filename.
- "script": The complete, ready-to-run Python script as a string. Use only the Python standard library unless the task clearly requires a third-party package. Make it safe — no destructive operations without confirmation.

Return only valid JSON. No markdown fences, no extra text.
"""


@bp.post("/api/workflow")
def workflow_builder():
    body = request.get_json(silent=True) or {}
    task = (body.get("task") or "").strip()
    if not task:
        return jsonify({"error": "task is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Task: {task}",
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(result)
