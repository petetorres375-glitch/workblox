from flask import Blueprint, jsonify, request

from app.services import claude_client
from app.services.file_handler import extract_text

bp = Blueprint("doc_analyzer", __name__)

SYSTEM_PROMPT = """\
You are a helpful document analyst. Analyze the provided document and return a JSON object with exactly these four keys:
- "summary": A 2-3 sentence overview of the document.
- "key_data_points": A list of important names, dates, amounts, or figures as bullet points.
- "action_items": A list of tasks, deadlines, or next steps. If none, return ["None identified."].
- "red_flags": A list of concerns, risks, or missing information. If none, return ["None identified."].

Return only valid JSON. No markdown fences, no extra text.
"""


@bp.post("/api/doc")
def doc_analyzer():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "no file selected"}), 400

    try:
        text = extract_text(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 415
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 422

    if not text.strip():
        return jsonify({"error": "Could not extract any text from the file"}), 422

    try:
        result = claude_client.call(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Document: {file.filename}\n\nContent:\n{text}",
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result)
