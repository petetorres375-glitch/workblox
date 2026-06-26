from flask import Blueprint, jsonify, request

from app import limiter
from app.services import claude_client

bp = Blueprint("workflow_builder", __name__)

SYSTEM_PROMPT = """\
You are a Python automation expert. The user will describe a repetitive task they want to automate.
Generate a small, focused, ready-to-run Python script that automates it.

IMPORTANT SCOPE LIMITS — this tool is for simple, single-purpose scripts only:
- Maximum ~50 lines of code
- Standard library only (no pip installs)
- Single file, no classes, no complex architecture
- One clear task: rename files, send an email, parse a CSV, clean a folder, etc.

If the request is too complex (multi-step pipelines, database integrations, APIs, GUIs, web scraping, full applications, or anything requiring more than ~50 lines), do NOT attempt it. Instead return:
- "filename": "contact_torres_tech.txt"
- "script": "This task is too complex for the Workflow Builder tool.\n\nFor custom automation projects, contact Torres Tech Remote:\npedro_torres@torrestechremote.com\nhttps://torrestechremote.com\n\nDescribe your project and you'll receive a flat-rate quote within 24 hours."

For simple tasks, return a JSON object with exactly two keys:
- "filename": A short, descriptive snake_case filename ending in .py (e.g. "rename_photos.py"). No path, just the filename.
- "script": The complete, ready-to-run Python script as a string. Make it safe — no destructive operations without confirmation.

Return only valid JSON. No markdown fences, no extra text.
"""


@bp.post("/api/workflow")
@limiter.limit("10 per hour")
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
