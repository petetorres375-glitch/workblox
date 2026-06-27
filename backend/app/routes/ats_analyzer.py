import io
import re
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from app import limiter
from app.services.ats_engine import analyze, build_report, grade, JOB_KEYWORDS
from app.services.ats_reports import generate_pdf, generate_docx

bp = Blueprint("ats_analyzer", __name__)

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def _extract_text(file):
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    raw = file.read()

    if ext == "txt":
        return raw.decode("utf-8", errors="replace")

    if ext == "pdf":
        try:
            import pdfplumber, re as _re
            text = ""
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text(layout=True) or ""
                    page_text = _re.sub(
                        r'\b([A-Z] ){2,}[A-Z]\b',
                        lambda m: m.group(0).replace(' ', ''),
                        page_text
                    )
                    lines = []
                    for line in page_text.splitlines():
                        s = line.strip()
                        if s:
                            lines.append(_re.sub(r' {3,}', '\n', s))
                    text += '\n'.join(lines) + '\n'
            return text
        except Exception:
            import fitz
            doc = fitz.open(stream=raw, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)

    if ext == "docx":
        import docx as python_docx
        doc = python_docx.Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(f"Unsupported file type '.{ext}'. Upload TXT, PDF, or DOCX.")


@bp.get("/api/ats/roles")
def get_roles():
    return jsonify(list(JOB_KEYWORDS.keys()))


@bp.post("/api/ats")
@limiter.limit("20 per hour")
def ats_analyze():
    if "resume" not in request.files:
        return jsonify({"error": "resume file is required"}), 400

    file = request.files["resume"]
    if not file.filename:
        return jsonify({"error": "no file selected"}), 400

    client_name     = (request.form.get("client_name") or "").strip() or "Client"
    job_role        = (request.form.get("job_role") or "").strip() or None
    custom_kw_raw   = (request.form.get("custom_keywords") or "").strip()
    custom_keywords = [kw.strip() for kw in custom_kw_raw.splitlines() if kw.strip()] or None

    try:
        resume_text = _extract_text(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 415
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 422

    if not resume_text.strip():
        return jsonify({"error": "Could not extract any text from the file. Try saving as .txt."}), 422

    results   = analyze(resume_text, job_role=job_role, custom_keywords=custom_keywords)
    now_label = datetime.now().strftime("%B %d, %Y  %H:%M")

    return jsonify({
        "results":      results,
        "client_name":  client_name,
        "filename":     file.filename,
        "job_role":     job_role,
        "now":          now_label,
        "grade":        grade(results["score"]),
        "score_color":  "green" if results["score"] >= 65 else "amber" if results["score"] >= 50 else "red",
        "resume_text":  resume_text,
    })


@bp.post("/api/ats/download/txt")
@limiter.limit("30 per hour")
def ats_download_txt():
    body = request.get_json(silent=True) or {}
    results  = body.get("results")
    filename = body.get("filename", "resume")
    if not results:
        return jsonify({"error": "results required"}), 400

    report_txt = build_report(results, filename)
    safe_name  = (body.get("client_name") or "Client").replace(" ", "_")
    return send_file(
        io.BytesIO(report_txt.encode("utf-8")),
        as_attachment=True,
        download_name=f"ATS_Report_{safe_name}.txt",
        mimetype="text/plain",
    )


@bp.post("/api/ats/download/pdf")
@limiter.limit("10 per hour")
def ats_download_pdf():
    body = request.get_json(silent=True) or {}
    results     = body.get("results")
    client_name = body.get("client_name", "Client")
    filename    = body.get("filename", "resume")
    job_role    = body.get("job_role")
    now         = body.get("now", datetime.now().strftime("%B %d, %Y  %H:%M"))
    if not results:
        return jsonify({"error": "results required"}), 400

    try:
        buf = generate_pdf(results, client_name, filename, job_role, now)
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {e}"}), 500

    safe_name = client_name.replace(" ", "_")
    return send_file(buf, as_attachment=True,
        download_name=f"ATS_Report_{safe_name}.pdf",
        mimetype="application/pdf")


@bp.post("/api/ats/download/docx")
@limiter.limit("10 per hour")
def ats_download_docx():
    body = request.get_json(silent=True) or {}
    results     = body.get("results")
    client_name = body.get("client_name", "Client")
    filename    = body.get("filename", "resume")
    job_role    = body.get("job_role")
    now         = body.get("now", datetime.now().strftime("%B %d, %Y  %H:%M"))
    if not results:
        return jsonify({"error": "results required"}), 400

    try:
        buf = generate_docx(results, client_name, filename, job_role, now)
    except Exception as e:
        return jsonify({"error": f"Word document generation failed: {e}"}), 500

    safe_name = client_name.replace(" ", "_")
    return send_file(buf, as_attachment=True,
        download_name=f"ATS_Report_{safe_name}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
