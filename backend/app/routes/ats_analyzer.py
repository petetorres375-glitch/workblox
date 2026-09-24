import io
import re

from flask import Blueprint, jsonify, request, send_file

from app import limiter
from app.services.ats_corpora import detect_language, supported_languages
from app.services.ats_engine import analyze, build_report, grade, JOB_KEYWORDS
from app.services.ats_reports import generate_pdf, generate_docx
from app.services.access import require_personal
from app.services.entitlements import require_tool
from app.services.localtime import local_now

bp = Blueprint("ats_analyzer", __name__)

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".pages"}


def _extract_text(file):
    """Returns (text, hidden_runs). Scoring counts keywords, so text a reader
    can't see (white-on-white keyword stuffing, 0.5pt type) would inflate the
    score; it's dropped, and hidden_runs lets the UI say so."""
    from app.services.hidden_text import docx_visible_text, pdf_visible_text

    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    raw = file.read()

    if ext == "txt":
        return raw.decode("utf-8", errors="replace"), 0

    if ext == "pdf":
        visible = pdf_visible_text(raw)
        if visible.hidden_runs:
            # pdfplumber's layout text below has no notion of visibility, so
            # for a file with hidden text use the visibility-filtered reading.
            return visible.text, visible.hidden_runs
        text = ""
        try:
            import pdfplumber, re as _re
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
        except Exception:
            text = ""

        if not text.strip():
            text = visible.text
        return text, 0

    if ext == "docx":
        visible = docx_visible_text(raw)
        return visible.text, visible.hidden_runs

    if ext == "pages":
        from app.services.pages_reader import read_pages
        return read_pages(raw), 0

    raise ValueError(f"Unsupported file type '.{ext}'. Upload TXT, PDF, DOCX, or PAGES.")


@bp.get("/api/ats/roles")
def get_roles():
    guard = require_personal() or require_tool("ats")
    if guard:
        return guard
    return jsonify(list(JOB_KEYWORDS.keys()))


@bp.post("/api/ats")
@limiter.limit("20 per hour")
def ats_analyze():
    guard = require_personal() or require_tool("ats")
    if guard:
        return guard
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
        resume_text, hidden_runs = _extract_text(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 415
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 422

    if not resume_text.strip():
        return jsonify({"error": "Could not extract any text from the file. Try saving as .txt."}), 422

    # Scoring matches a language-specific keyword corpus, so detect the CV's
    # language and score it against the right one. A language with no corpus
    # would come back 0/100 -- which reads as "your resume is bad" rather than
    # "this tool cannot read it" -- so refuse clearly instead.
    language, reason = detect_language(resume_text)
    if language is None:
        return jsonify({
            "error": ("This resume is not in a language the ATS Analyzer can score yet. "
                      "It currently rates resumes written in English or Spanish."),
            "code": reason,
            "supported_languages": supported_languages(),
        }), 422

    results   = analyze(resume_text, job_role=job_role,
                        custom_keywords=custom_keywords, language=language)
    now_label = local_now().strftime("%B %d, %Y  %H:%M")

    return jsonify({
        "results":      results,
        "client_name":  client_name,
        "filename":     file.filename,
        "job_role":     job_role,
        "now":          now_label,
        "grade":        grade(results["score"], language),
        "score_color":  "green" if results["score"] >= 65 else "amber" if results["score"] >= 50 else "red",
        "resume_text":  resume_text,
        "language":     language,
        **({"hidden_text": {"count": hidden_runs}} if hidden_runs else {}),
    })


@bp.post("/api/ats/download/txt")
@limiter.limit("30 per hour")
def ats_download_txt():
    guard = require_personal() or require_tool("ats")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    results  = body.get("results")
    filename = body.get("filename", "resume")
    if not results:
        return jsonify({"error": "results required"}), 400

    report_txt = build_report(results, filename)  # language travels in results
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
    guard = require_personal() or require_tool("ats")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    results     = body.get("results")
    client_name = body.get("client_name", "Client")
    filename    = body.get("filename", "resume")
    job_role    = body.get("job_role")
    now         = body.get("now", local_now().strftime("%B %d, %Y  %H:%M"))
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
    guard = require_personal() or require_tool("ats")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    results     = body.get("results")
    client_name = body.get("client_name", "Client")
    filename    = body.get("filename", "resume")
    job_role    = body.get("job_role")
    now         = body.get("now", local_now().strftime("%B %d, %Y  %H:%M"))
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
