import io
from flask import Blueprint, jsonify, request, send_file
from app import limiter
from app.services.access import require_personal
from app.services.entitlements import require_tool
from app.services.resume_engine import generate_resume
from app.services.resume_pdf import generate_resume_pdf, generate_resume_docx, generate_resume_txt

bp = Blueprint("resume_builder", __name__)


@bp.post("/api/resume/create")
@limiter.limit("10 per hour")
def create_resume():
    guard = require_personal() or require_tool("resume")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}

    contact = {
        "name":     (body.get("name") or "").strip(),
        "email":    (body.get("email") or "").strip(),
        "phone":    (body.get("phone") or "").strip(),
        "location": (body.get("location") or "").strip(),
        "linkedin": (body.get("linkedin") or "").strip(),
    }
    job_role   = (body.get("job_role") or "").strip() or None
    experience = body.get("experience") or []
    education  = body.get("education") or []
    language   = (body.get("language") or "en").strip()

    data = {
        "job_role":       job_role,
        "experience":     experience,
        "education":      education,
        "skills":         (body.get("skills") or "").strip(),
        "certifications": (body.get("certifications") or "").strip(),
        "extra":          (body.get("extra") or "").strip(),
    }

    if not contact["name"]:
        return jsonify({"error": "Name is required"}), 400
    if not experience and not data["skills"]:
        return jsonify({"error": "Please add at least one job or some skills"}), 400

    try:
        resume = generate_resume(data, language=language)
    except Exception as e:
        return jsonify({"error": f"Resume generation failed: {e}"}), 500

    return jsonify({"contact": contact, "resume": resume, "job_role": job_role})


@bp.post("/api/resume/download/pdf")
@limiter.limit("10 per hour")
def download_resume_pdf():
    guard = require_personal() or require_tool("resume")
    if guard:
        return guard
    body    = request.get_json(silent=True) or {}
    contact = body.get("contact", {})
    resume  = body.get("resume", {})
    job_role = body.get("job_role")
    if not resume:
        return jsonify({"error": "resume data required"}), 400
    try:
        buf = generate_resume_pdf(contact, resume, job_role, body.get("labels"))
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {e}"}), 500
    safe = (contact.get("name") or "Resume").replace(" ", "_")
    return send_file(buf, as_attachment=True,
        download_name=f"{safe}_Resume.pdf",
        mimetype="application/pdf")


@bp.post("/api/resume/download/docx")
@limiter.limit("10 per hour")
def download_resume_docx():
    guard = require_personal() or require_tool("resume")
    if guard:
        return guard
    body    = request.get_json(silent=True) or {}
    contact = body.get("contact", {})
    resume  = body.get("resume", {})
    job_role = body.get("job_role")
    if not resume:
        return jsonify({"error": "resume data required"}), 400
    try:
        buf = generate_resume_docx(contact, resume, job_role, body.get("labels"))
    except Exception as e:
        return jsonify({"error": f"Word document generation failed: {e}"}), 500
    safe = (contact.get("name") or "Resume").replace(" ", "_")
    return send_file(buf, as_attachment=True,
        download_name=f"{safe}_Resume.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@bp.post("/api/resume/download/txt")
@limiter.limit("20 per hour")
def download_resume_txt():
    guard = require_personal() or require_tool("resume")
    if guard:
        return guard
    body    = request.get_json(silent=True) or {}
    contact = body.get("contact", {})
    resume  = body.get("resume", {})
    job_role = body.get("job_role")
    if not resume:
        return jsonify({"error": "resume data required"}), 400
    txt  = generate_resume_txt(contact, resume, job_role, body.get("labels"))
    safe = (contact.get("name") or "Resume").replace(" ", "_")
    return send_file(
        io.BytesIO(txt.encode("utf-8")),
        as_attachment=True,
        download_name=f"{safe}_Resume.txt",
        mimetype="text/plain")
