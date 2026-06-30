from flask import Blueprint, jsonify, request, g

from .. import limiter
from ..services import claude_client
from ..services.email import send_pdf_email, send_report_email
from ..services.file_handler import extract_text

bp = Blueprint("biz", __name__, url_prefix="/api/biz")


def _require_business():
    if g.user.get("plan") != "business":
        return jsonify({"error": "Business subscription required"}), 403
    return None


# ── System prompts ─────────────────────────────────────────────────────────────

_HIRING_MANAGER_PROMPT = """You are an expert hiring manager and HR professional. Given a description of a position, generate a comprehensive hiring package.

Return ONLY valid JSON with this structure:
{
  "job_title": "string",
  "position_summary": "string",
  "interview_questions": ["string", ...],
  "evaluation_criteria": ["string", ...],
  "red_flags": ["string", ...],
  "onboarding_tips": ["string", ...]
}"""

_JOB_DESC_PROMPT = """You are an expert HR copywriter. Create a compelling job description that attracts top talent.

Return ONLY valid JSON with this structure:
{
  "job_title": "string",
  "overview": "string",
  "responsibilities": ["string", ...],
  "requirements": ["string", ...],
  "nice_to_have": ["string", ...],
  "benefits": ["string", ...],
  "about_company_placeholder": "string"
}"""

_PROPOSAL_PROMPT = """You are an expert business consultant and proposal writer. Create a professional proposal or quote based on the provided details.

Return ONLY valid JSON with this structure:
{
  "executive_summary": "string",
  "scope_of_work": ["string", ...],
  "deliverables": ["string", ...],
  "line_items": [{"description": "string", "quantity": number, "unit_price": number, "total": number}, ...],
  "subtotal": number,
  "notes": "string",
  "terms": "string",
  "validity_days": number
}"""

_CONTRACT_PROMPT = """You are an expert contract lawyer and business analyst. Analyze the provided contract and give a plain-language summary.

Return ONLY valid JSON with this structure:
{
  "document_type": "string",
  "summary": "string",
  "key_obligations": ["string", ...],
  "important_dates": ["string", ...],
  "payment_terms": "string",
  "termination_clauses": ["string", ...],
  "red_flags": ["string", ...],
  "missing_standard_clauses": ["string", ...],
  "overall_risk": "low|medium|high",
  "recommendation": "string"
}"""

_CUSTOMER_RESPONSE_PROMPT = """You are an expert customer success manager. Draft a professional, empathetic response to a customer message.

Return ONLY valid JSON with this structure:
{
  "subject": "string",
  "response_draft": "string",
  "tone": "string",
  "key_points_addressed": ["string", ...],
  "follow_up_suggested": "string"
}"""

_REVIEW_REQUEST_PROMPT = """You are an expert at customer experience and reputation management. Write a friendly, natural review request email.

Return ONLY valid JSON with this structure:
{
  "subject": "string",
  "body": "string",
  "platform_links_placeholder": "string",
  "timing_advice": "string"
}"""

_SOCIAL_MEDIA_PROMPT = """You are an expert social media marketer. Create engaging social media content for the given topic and platforms.

Return ONLY valid JSON with this structure:
{
  "posts": [
    {
      "platform": "string",
      "content": "string",
      "hashtags": ["string", ...],
      "best_time_to_post": "string",
      "character_count": number
    }
  ],
  "content_tips": ["string", ...]
}"""

_AD_COPY_PROMPT = """You are an expert direct-response copywriter. Write high-converting ad copy for the given product or service.

Return ONLY valid JSON with this structure:
{
  "headlines": ["string", ...],
  "primary_descriptions": ["string", ...],
  "short_descriptions": ["string", ...],
  "cta_options": ["string", ...],
  "value_propositions": ["string", ...],
  "notes": "string"
}"""

_POLICY_PROMPT = """You are an expert business policy writer and HR professional. Draft a clear, professional company policy document.

Return ONLY valid JSON with this structure:
{
  "title": "string",
  "purpose": "string",
  "scope": "string",
  "effective_date_placeholder": "[EFFECTIVE DATE]",
  "sections": [{"heading": "string", "content": "string"}, ...],
  "acknowledgment_statement": "string"
}"""

_SOP_PROMPT = """You are an expert operations manager and technical writer. Create a clear, actionable standard operating procedure.

Return ONLY valid JSON with this structure:
{
  "title": "string",
  "purpose": "string",
  "scope": "string",
  "frequency": "string",
  "required_tools": ["string", ...],
  "steps": [{"step_number": number, "action": "string", "details": "string", "warning": "string|null"}, ...],
  "quality_checks": ["string", ...],
  "notes": "string"
}"""

_MEETING_NOTES_PROMPT = """You are an expert executive assistant and meeting facilitator. Clean up and structure the provided meeting notes.

Return ONLY valid JSON with this structure:
{
  "meeting_summary": "string",
  "date_placeholder": "[DATE]",
  "attendees_placeholder": "[ATTENDEES]",
  "decisions_made": ["string", ...],
  "action_items": [{"task": "string", "owner": "string", "due_date": "string"}, ...],
  "next_steps": ["string", ...],
  "follow_up_meeting": "string"
}"""

_BUSINESS_EMAIL_PROMPT = """You are an expert business communication specialist. Write a clear, professional business email.

Return ONLY valid JSON with this structure:
{
  "subject": "string",
  "body": "string",
  "tone": "string",
  "key_points": ["string", ...],
  "call_to_action": "string"
}"""

_BATCH_ATS_PROMPT = """You are an expert recruiter and ATS specialist. Evaluate this resume against the job description.

Return ONLY valid JSON with this structure:
{
  "candidate_name": "string",
  "match_score": number,
  "match_level": "Strong|Good|Fair|Weak",
  "matched_keywords": ["string", ...],
  "missing_keywords": ["string", ...],
  "top_strengths": ["string", ...],
  "concerns": ["string", ...],
  "recommendation": "Advance|Maybe|Pass"
}"""


# ── Pattern A routes (JSON in → Claude → JSON out) ─────────────────────────────

@bp.post("/hiring-manager")
@limiter.limit("20 per hour")
def hiring_manager():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    description = (body.get("description") or "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_HIRING_MANAGER_PROMPT,
            user_message=description,
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/job-desc")
@limiter.limit("20 per hour")
def job_desc_writer():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    job_title = (body.get("job_title") or "").strip()
    department = (body.get("department") or "").strip()
    requirements = (body.get("requirements") or "").strip()
    salary_range = (body.get("salary_range") or "").strip()
    company_info = (body.get("company_info") or "").strip()
    if not job_title:
        return jsonify({"error": "job_title is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_JOB_DESC_PROMPT,
            user_message=f"Job Title: {job_title}\nDepartment: {department}\nRequirements: {requirements}\nSalary Range: {salary_range}\nCompany Info: {company_info}",
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/proposal")
@limiter.limit("15 per hour")
def proposal_generator():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    client_name = (body.get("client_name") or "").strip()
    project_description = (body.get("project_description") or "").strip()
    services = (body.get("services") or "").strip()
    budget_range = (body.get("budget_range") or "").strip()
    timeline = (body.get("timeline") or "").strip()
    if not project_description:
        return jsonify({"error": "project_description is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_PROPOSAL_PROMPT,
            user_message=f"Client: {client_name}\nProject: {project_description}\nServices: {services}\nBudget: {budget_range}\nTimeline: {timeline}",
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/customer-response")
@limiter.limit("30 per hour")
def customer_response_drafter():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    customer_message = (body.get("customer_message") or "").strip()
    context = (body.get("context") or "").strip()
    tone = (body.get("tone") or "professional").strip()
    if not customer_message:
        return jsonify({"error": "customer_message is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_CUSTOMER_RESPONSE_PROMPT,
            user_message=f"Customer Message: {customer_message}\nContext: {context}\nDesired Tone: {tone}",
            model="claude-sonnet-4-6",
            max_tokens=1024,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/review-request")
@limiter.limit("20 per hour")
def review_request_email():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    business_name = (body.get("business_name") or "").strip()
    customer_name = (body.get("customer_name") or "").strip()
    service_provided = (body.get("service_provided") or "").strip()
    platforms = (body.get("platforms") or "Google, Yelp").strip()
    if not business_name:
        return jsonify({"error": "business_name is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_REVIEW_REQUEST_PROMPT,
            user_message=f"Business: {business_name}\nCustomer Name: {customer_name}\nService: {service_provided}\nReview Platforms: {platforms}",
            model="claude-sonnet-4-6",
            max_tokens=1024,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/social-media")
@limiter.limit("20 per hour")
def social_media_generator():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    topic = (body.get("topic") or "").strip()
    business_name = (body.get("business_name") or "").strip()
    platforms = (body.get("platforms") or "LinkedIn, Instagram, Facebook").strip()
    tone = (body.get("tone") or "professional").strip()
    goal = (body.get("goal") or "engagement").strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_SOCIAL_MEDIA_PROMPT,
            user_message=f"Topic: {topic}\nBusiness: {business_name}\nPlatforms: {platforms}\nTone: {tone}\nGoal: {goal}",
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/ad-copy")
@limiter.limit("20 per hour")
def ad_copy_writer():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    product_service = (body.get("product_service") or "").strip()
    target_audience = (body.get("target_audience") or "").strip()
    platform = (body.get("platform") or "Google Ads").strip()
    unique_value = (body.get("unique_value") or "").strip()
    goal = (body.get("goal") or "conversions").strip()
    if not product_service:
        return jsonify({"error": "product_service is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_AD_COPY_PROMPT,
            user_message=f"Product/Service: {product_service}\nTarget Audience: {target_audience}\nPlatform: {platform}\nUnique Value Proposition: {unique_value}\nGoal: {goal}",
            model="claude-sonnet-4-6",
            max_tokens=1536,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/policy")
@limiter.limit("15 per hour")
def policy_generator():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    policy_type = (body.get("policy_type") or "").strip()
    company_name = (body.get("company_name") or "").strip()
    industry = (body.get("industry") or "").strip()
    specifics = (body.get("specifics") or "").strip()
    if not policy_type:
        return jsonify({"error": "policy_type is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_POLICY_PROMPT,
            user_message=f"Policy Type: {policy_type}\nCompany: {company_name}\nIndustry: {industry}\nSpecific Requirements: {specifics}",
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/sop")
@limiter.limit("15 per hour")
def sop_generator():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    process_name = (body.get("process_name") or "").strip()
    department = (body.get("department") or "").strip()
    description = (body.get("description") or "").strip()
    frequency = (body.get("frequency") or "").strip()
    if not process_name:
        return jsonify({"error": "process_name is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_SOP_PROMPT,
            user_message=f"Process: {process_name}\nDepartment: {department}\nDescription: {description}\nFrequency: {frequency}",
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/meeting-notes")
@limiter.limit("30 per hour")
def meeting_notes_cleaner():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    raw_notes = (body.get("raw_notes") or "").strip()
    context = (body.get("context") or "").strip()
    if not raw_notes:
        return jsonify({"error": "raw_notes is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_MEETING_NOTES_PROMPT,
            user_message=f"Meeting Context: {context}\n\nRaw Notes:\n{raw_notes}",
            model="claude-sonnet-4-6",
            max_tokens=2048,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/business-email")
@limiter.limit("30 per hour")
def business_email_drafter():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    purpose = (body.get("purpose") or "").strip()
    recipient = (body.get("recipient") or "").strip()
    key_points = (body.get("key_points") or "").strip()
    tone = (body.get("tone") or "professional").strip()
    if not purpose:
        return jsonify({"error": "purpose is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_BUSINESS_EMAIL_PROMPT,
            user_message=f"Purpose: {purpose}\nRecipient/Role: {recipient}\nKey Points: {key_points}\nTone: {tone}",
            model="claude-sonnet-4-6",
            max_tokens=1024,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Pattern B routes (file upload) ────────────────────────────────────────────

@bp.post("/contract")
@limiter.limit("10 per hour")
def contract_analyzer():
    guard = _require_business()
    if guard:
        return guard
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
            system_prompt=_CONTRACT_PROMPT,
            user_message=f"Contract filename: {file.filename}\n\nContent:\n{text[:12000]}",
            model="claude-sonnet-4-6",
            max_tokens=3000,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/batch-ats")
@limiter.limit("5 per hour")
def batch_ats():
    guard = _require_business()
    if guard:
        return guard
    files = request.files.getlist("resumes")
    job_description = (request.form.get("job_description") or "").strip()
    if not files or not files[0].filename:
        return jsonify({"error": "at least one resume file is required"}), 400
    results = []
    for file in files[:10]:
        try:
            text = extract_text(file)
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})
            continue
        try:
            analysis = claude_client.call(
                system_prompt=_BATCH_ATS_PROMPT,
                user_message=f"Job Description: {job_description}\n\nResume ({file.filename}):\n{text[:6000]}",
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
            )
            analysis["filename"] = file.filename
            results.append(analysis)
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})
    return jsonify({"results": results, "total": len(results)})


@bp.post("/send-report")
@limiter.limit("10 per hour")
def send_report():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    email_to = (body.get("email") or "").strip()
    subject = (body.get("subject") or "Workblox Report").strip()
    content_txt = (body.get("content_txt") or "").strip()
    content_html = (body.get("content_html") or "").strip()
    if not email_to or not content_txt:
        return jsonify({"error": "email and content are required"}), 400
    success = send_report_email(email_to, subject, content_txt, content_html or content_txt)
    if not success:
        return jsonify({"error": "Failed to send email — check SendGrid configuration."}), 500
    return jsonify({"sent": True})


@bp.post("/email-pdf")
@limiter.limit("5 per hour")
def email_pdf():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    email_to = (body.get("email") or "").strip()
    subject = (body.get("subject") or "Workblox Report").strip()
    content_txt = (body.get("content_txt") or "").strip()
    filename = (body.get("filename") or "report").strip()
    if not email_to or not content_txt:
        return jsonify({"error": "email and content are required"}), 400
    try:
        success = send_pdf_email(email_to, subject, content_txt, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not success:
        return jsonify({"error": "Failed to send PDF email — check SendGrid configuration."}), 500
    return jsonify({"sent": True})
