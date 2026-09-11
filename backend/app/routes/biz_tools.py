import io
import json
import re
from datetime import date, timedelta
from pathlib import Path

from flask import Blueprint, jsonify, request, g, Response, send_file

from .. import limiter
from ..services import claude_client, data_cleaner, spreadsheet
from ..services.access import require_business as _require_business
from ..services.email import send_pdf_email, send_report_email, _generate_pdf
from ..services.entitlements import require_tool
from ..services.file_handler import extract_text, prepare_image
from ..services.spreadsheet import TableTooLarge, format_for_filename, read_table, write_table

bp = Blueprint("biz", __name__, url_prefix="/api/biz")


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


_DATA_COLUMN_PLAN_PROMPT = """You are a data analyst. You will be shown a spreadsheet's column headers, a sample of its rows, and possibly a note from the user describing what the data is.

Classify each column, and identify which columns together identify a unique real-world record.

Return ONLY valid JSON with this structure:
{
  "types": {"<exact column header>": "date|currency|email|phone|name|number|text", ...},
  "identity": ["<exact column header>", ...]
}

Rules:
- Use the EXACT column header strings you were given as the keys in "types". Do not rename, reword, or translate them.
- Every column must appear in "types".
- "identity" must be the SMALLEST set of columns that together identify one record (e.g. an email column on its own, or first name + last name). Never include columns that merely describe a record, such as notes, amounts, or status.
- If nothing in the data reliably identifies a record, return an empty "identity" list."""

_EXPENSE_RECEIPT_PROMPT = """You are an expert bookkeeper reading a receipt.

Return ONLY valid JSON with this structure:
{
  "date": "YYYY-MM-DD",
  "vendor": "string",
  "amount": number,
  "currency": "string",
  "category": "string",
  "confidence": "high|low",
  "reason": "string",
  "notes": "string"
}

Rules:
- Report ONLY what is actually visible on the receipt. Never infer, complete, or invent a vendor, date, or amount.
- "amount" must be the final total paid, as a plain number with no currency symbol.
- If any of date, vendor or amount is missing or illegible, leave that field as an empty string (or 0 for amount), set "confidence" to "low", and say which field was unreadable in "reason".
- Set "confidence" to "low" whenever you are unsure of the category as well, and explain why in "reason".
- Leave "reason" as an empty string when confidence is "high"."""

_EXPENSE_CATEGORIZE_PROMPT = """You are an expert bookkeeper categorizing bank and credit-card transactions.

Return ONLY valid JSON with this structure:
{
  "entries": [
    {"index": number, "vendor": "string", "category": "string", "confidence": "high|low", "reason": "string", "notes": "string"}
  ]
}

Rules:
- Return exactly one entry for every transaction you were given, echoing back the same "index".
- "vendor" is the human-readable merchant name recovered from the raw bank description (e.g. "SQ *BLUE BOTTLE COFFEE 0123" becomes "Blue Bottle Coffee").
- Choose "category" from the allowed list you are given. Use the closest match.
- Set "confidence" to "low" when the description is too cryptic to categorize reliably, and explain why in "reason". Never guess a specific merchant from an unreadable description.
- Leave "reason" as an empty string when confidence is "high"."""


# ── Pattern A routes (JSON in → Claude → JSON out) ─────────────────────────────

@bp.post("/hiring-manager")
@limiter.limit("20 per hour")
def hiring_manager():
    guard = _require_business()
    if guard:
        return guard
    guard = require_tool("hiring")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    description = (body.get("description") or "").strip()
    language = (body.get("language") or "en").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_HIRING_MANAGER_PROMPT,
            user_message=description,
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            language=language,
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
    guard = require_tool("job-desc")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    job_title = (body.get("job_title") or "").strip()
    department = (body.get("department") or "").strip()
    requirements = (body.get("requirements") or "").strip()
    salary_range = (body.get("salary_range") or "").strip()
    company_info = (body.get("company_info") or "").strip()
    language = (body.get("language") or "en").strip()
    if not job_title:
        return jsonify({"error": "job_title is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_JOB_DESC_PROMPT,
            user_message=f"Job Title: {job_title}\nDepartment: {department}\nRequirements: {requirements}\nSalary Range: {salary_range}\nCompany Info: {company_info}",
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            language=language,
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
    guard = require_tool("proposal")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    client_name = (body.get("client_name") or "").strip()
    project_description = (body.get("project_description") or "").strip()
    services = (body.get("services") or "").strip()
    budget_range = (body.get("budget_range") or "").strip()
    timeline = (body.get("timeline") or "").strip()
    language = (body.get("language") or "en").strip()
    if not project_description:
        return jsonify({"error": "project_description is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_PROPOSAL_PROMPT,
            user_message=f"Client: {client_name}\nProject: {project_description}\nServices: {services}\nBudget: {budget_range}\nTimeline: {timeline}",
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            language=language,
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
    guard = require_tool("customer")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    customer_message = (body.get("customer_message") or "").strip()
    context = (body.get("context") or "").strip()
    tone = (body.get("tone") or "professional").strip()
    language = (body.get("language") or "en").strip()
    if not customer_message:
        return jsonify({"error": "customer_message is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_CUSTOMER_RESPONSE_PROMPT,
            user_message=f"Customer Message: {customer_message}\nContext: {context}\nDesired Tone: {tone}",
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            language=language,
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
    guard = require_tool("review")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    business_name = (body.get("business_name") or "").strip()
    customer_name = (body.get("customer_name") or "").strip()
    service_provided = (body.get("service_provided") or "").strip()
    platforms = (body.get("platforms") or "Google, Yelp").strip()
    language = (body.get("language") or "en").strip()
    if not business_name:
        return jsonify({"error": "business_name is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_REVIEW_REQUEST_PROMPT,
            user_message=f"Business: {business_name}\nCustomer Name: {customer_name}\nService: {service_provided}\nReview Platforms: {platforms}",
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            language=language,
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
    guard = require_tool("social")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    topic = (body.get("topic") or "").strip()
    business_name = (body.get("business_name") or "").strip()
    platforms = (body.get("platforms") or "LinkedIn, Instagram, Facebook").strip()
    tone = (body.get("tone") or "professional").strip()
    goal = (body.get("goal") or "engagement").strip()
    language = (body.get("language") or "en").strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_SOCIAL_MEDIA_PROMPT,
            user_message=f"Topic: {topic}\nBusiness: {business_name}\nPlatforms: {platforms}\nTone: {tone}\nGoal: {goal}",
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            language=language,
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
    guard = require_tool("ad-copy")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    product_service = (body.get("product_service") or "").strip()
    target_audience = (body.get("target_audience") or "").strip()
    platform = (body.get("platform") or "Google Ads").strip()
    unique_value = (body.get("unique_value") or "").strip()
    goal = (body.get("goal") or "conversions").strip()
    language = (body.get("language") or "en").strip()
    if not product_service:
        return jsonify({"error": "product_service is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_AD_COPY_PROMPT,
            user_message=f"Product/Service: {product_service}\nTarget Audience: {target_audience}\nPlatform: {platform}\nUnique Value Proposition: {unique_value}\nGoal: {goal}",
            model="claude-haiku-4-5-20251001",
            max_tokens=1536,
            language=language,
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
    guard = require_tool("policy")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    policy_type = (body.get("policy_type") or "").strip()
    company_name = (body.get("company_name") or "").strip()
    industry = (body.get("industry") or "").strip()
    specifics = (body.get("specifics") or "").strip()
    language = (body.get("language") or "en").strip()
    if not policy_type:
        return jsonify({"error": "policy_type is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_POLICY_PROMPT,
            user_message=f"Policy Type: {policy_type}\nCompany: {company_name}\nIndustry: {industry}\nSpecific Requirements: {specifics}",
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            language=language,
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
    guard = require_tool("sop")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    process_name = (body.get("process_name") or "").strip()
    department = (body.get("department") or "").strip()
    description = (body.get("description") or "").strip()
    frequency = (body.get("frequency") or "").strip()
    language = (body.get("language") or "en").strip()
    if not process_name:
        return jsonify({"error": "process_name is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_SOP_PROMPT,
            user_message=f"Process: {process_name}\nDepartment: {department}\nDescription: {description}\nFrequency: {frequency}",
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            language=language,
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
    guard = require_tool("meeting")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    raw_notes = (body.get("raw_notes") or "").strip()
    context = (body.get("context") or "").strip()
    language = (body.get("language") or "en").strip()
    if not raw_notes:
        return jsonify({"error": "raw_notes is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_MEETING_NOTES_PROMPT,
            user_message=f"Meeting Context: {context}\n\nRaw Notes:\n{raw_notes}",
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            language=language,
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
    guard = require_tool("email")
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    purpose = (body.get("purpose") or "").strip()
    recipient = (body.get("recipient") or "").strip()
    key_points = (body.get("key_points") or "").strip()
    tone = (body.get("tone") or "professional").strip()
    language = (body.get("language") or "en").strip()
    if not purpose:
        return jsonify({"error": "purpose is required"}), 400
    try:
        result = claude_client.call(
            system_prompt=_BUSINESS_EMAIL_PROMPT,
            user_message=f"Purpose: {purpose}\nRecipient/Role: {recipient}\nKey Points: {key_points}\nTone: {tone}",
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            language=language,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Pattern B routes (file upload) ────────────────────────────────────────────

_CONTRACT_PHOTO_INSTRUCTION = (
    "Analyze the contract shown in the attached photo(s). If there are multiple "
    "photos, treat them as consecutive pages of the same contract, in the order given."
)


@bp.post("/contract")
@limiter.limit("10 per hour")
def contract_analyzer():
    guard = _require_business()
    if guard:
        return guard
    guard = require_tool("contract")
    if guard:
        return guard

    file = request.files.get("file")
    images = [f for f in request.files.getlist("images") if f and f.filename]
    language = (request.form.get("language") or "en").strip()

    if file and file.filename and images:
        return jsonify({"error": "Provide either a file or photos, not both"}), 400

    if images:
        if len(images) > claude_client.MAX_IMAGES:
            return jsonify({"error": f"Too many photos — {claude_client.MAX_IMAGES} max per submission"}), 400
        try:
            image_blocks = [claude_client.to_image_content(prepare_image(img)) for img in images]
        except ValueError as e:
            return jsonify({"error": str(e)}), 415
        try:
            result = claude_client.call(
                system_prompt=_CONTRACT_PROMPT,
                user_message=_CONTRACT_PHOTO_INSTRUCTION,
                model="claude-haiku-4-5-20251001",
                max_tokens=3000,
                language=language,
                images=image_blocks,
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if not file or not file.filename:
        return jsonify({"error": "file is required"}), 400
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
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            language=language,
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
    guard = require_tool("batch-ats")
    if guard:
        return guard
    files = request.files.getlist("resumes")
    job_description = (request.form.get("job_description") or "").strip()
    language = (request.form.get("language") or "en").strip()
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
                language=language,
            )
            analysis["filename"] = file.filename
            results.append(analysis)
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})
    return jsonify({"results": results, "total": len(results)})


# ── Data Cleanup ──────────────────────────────────────────────────────────────

_ALLOWED_COLUMN_TYPES = {"date", "currency", "email", "phone", "name", "number", "text"}
_DATE_FORMAT_MODES = {"auto", "mdy", "dmy"}
_DUPLICATE_MODES = {"flag", "merge"}


def _column_plan(headers, rows, description):
    """Ask Claude what each column means. Returns a validated plan, or None to
    let data_cleaner fall back to its own heuristics -- the tool has to keep
    working when the AI call fails, since the cleanup itself doesn't need it."""
    sample = [
        ["" if cell is None else str(cell) for cell in row[:len(headers)]]
        for row in rows[:20]
    ]
    payload = {"columns": headers, "sample_rows": sample}
    if description:
        payload["user_description"] = description

    try:
        plan = claude_client.call(
            system_prompt=_DATA_COLUMN_PLAN_PROMPT,
            user_message=json.dumps(payload, ensure_ascii=False)[:12000],
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            # Deliberately not the user's language: this response is read by
            # code and keyed on the file's own column headers, so translating
            # it would break the lookup. Only user-facing copy gets localized.
            language="en",
        )
    except Exception:
        return None

    if not isinstance(plan, dict):
        return None
    raw_types = plan.get("types")
    if not isinstance(raw_types, dict):
        return None

    # Trust nothing about the shape: keep only real headers with known types,
    # and drop any identity column the model invented.
    types = {h: raw_types[h] for h in headers if raw_types.get(h) in _ALLOWED_COLUMN_TYPES}
    if not types:
        return None
    raw_identity = plan.get("identity")
    identity = [h for h in raw_identity if h in headers] if isinstance(raw_identity, list) else []
    return {"types": types, "identity": identity}


@bp.post("/data-cleanup")
@limiter.limit("15 per hour")
def data_cleanup():
    guard = _require_business()
    if guard:
        return guard
    guard = require_tool("data-cleanup")
    if guard:
        return guard

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "file is required"}), 400

    description = (request.form.get("description") or "").strip()
    date_format = (request.form.get("date_format") or "auto").strip()
    duplicate_handling = (request.form.get("duplicate_handling") or "flag").strip()
    if date_format not in _DATE_FORMAT_MODES:
        date_format = "auto"
    if duplicate_handling not in _DUPLICATE_MODES:
        duplicate_handling = "flag"

    try:
        headers, rows = read_table(file)
    except TableTooLarge as e:
        return jsonify({"error": str(e)}), 413
    except ValueError as e:
        return jsonify({"error": str(e)}), 415
    except Exception as e:
        return jsonify({"error": f"Could not read that file: {e}"}), 422

    if not rows:
        return jsonify({"error": "That file has a header row but no data rows."}), 422

    plan = _column_plan(headers, rows, description)
    result = data_cleaner.clean_table(
        headers, rows,
        date_format=date_format,
        duplicate_handling=duplicate_handling,
        column_plan=plan,
    )
    result["source_format"] = format_for_filename(file.filename)
    result["ai_plan_used"] = plan is not None
    return jsonify(result)


@bp.post("/data-cleanup/download")
@limiter.limit("20 per hour")
def data_cleanup_download():
    """The cleaned table round-trips through the browser rather than being held
    server-side between the two requests -- that's what keeps this tool
    genuinely no-retention."""
    guard = _require_business()
    if guard:
        return guard
    guard = require_tool("data-cleanup")
    if guard:
        return guard

    body = request.get_json(silent=True) or {}
    headers = body.get("headers")
    rows = body.get("rows")
    if not isinstance(headers, list) or not headers or not isinstance(rows, list):
        return jsonify({"error": "headers and rows are required"}), 400
    if len(rows) > spreadsheet.MAX_ROWS:
        return jsonify({"error": f"Too many rows — {spreadsheet.MAX_ROWS:,} is the maximum."}), 413

    fmt = "xlsx" if body.get("format") == "xlsx" else "csv"
    filename = (body.get("filename") or "cleaned_data").strip() or "cleaned_data"
    try:
        data = write_table(headers, rows, fmt)
    except Exception as e:
        return jsonify({"error": f"Could not build the file: {e}"}), 500

    mimetype = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if fmt == "xlsx" else "text/csv"
    )
    return send_file(io.BytesIO(data), mimetype=mimetype,
                     as_attachment=True, download_name=f"{filename}.{fmt}")


# ── Expense Organizer ─────────────────────────────────────────────────────────

_DEFAULT_EXPENSE_CATEGORIES = [
    "Meals", "Travel", "Lodging", "Office Supplies", "Software", "Utilities",
    "Professional Services", "Marketing", "Equipment", "Other",
]
_RECEIPT_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
_TRANSACTION_EXTS = {".csv", ".xlsx"}
_MAX_EXPENSE_FILES = 10
_DATE_RANGES = {"this_month", "last_month", "custom", "all"}


def _month_bounds(today, months_back=0):
    year, month = today.year, today.month - months_back
    while month < 1:
        month += 12
        year -= 1
    start = date(year, month, 1)
    end = (date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)) - timedelta(days=1)
    return start, end


def _resolve_range(mode, start_raw, end_raw):
    """Returns (start, end) as dates, or (None, None) for no filtering."""
    today = date.today()
    if mode == "this_month":
        return _month_bounds(today, 0)
    if mode == "last_month":
        return _month_bounds(today, 1)
    if mode == "custom":
        start = _iso_or_none(start_raw)
        end = _iso_or_none(end_raw)
        if start and end and start > end:
            start, end = end, start
        return start, end
    return None, None


def _iso_or_none(raw):
    try:
        return date.fromisoformat((raw or "").strip())
    except ValueError:
        return None


def _to_amount(raw):
    """Parse a spreadsheet money cell. Returns (value, ok)."""
    if raw is None:
        return 0.0, False
    if isinstance(raw, (int, float)):
        return float(raw), True
    text = str(raw).strip()
    if not text:
        return 0.0, False
    negative = text.startswith("(") and text.endswith(")")
    cleaned = re.sub(r"[^\d.\-]", "", text.replace(",", ""))
    if cleaned in ("", "-", ".", "-."):
        return 0.0, False
    try:
        value = float(cleaned)
    except ValueError:
        return 0.0, False
    return (-value if negative else value), True


def _find_column(headers, *keywords):
    lowered = [h.lower() for h in headers]
    for index, header in enumerate(lowered):
        if any(keyword in header for keyword in keywords):
            return index
    return None


def _transactions_from_table(headers, rows, filename):
    """Pull (date, description, amount) out of a bank or card export. Column
    names vary wildly between banks, so this matches on keywords and falls back
    to type detection when nothing recognizable is there."""
    date_i = _find_column(headers, "date", "posted")
    desc_i = _find_column(headers, "description", "details", "memo", "payee",
                          "merchant", "narrative", "reference", "particulars")
    amount_i = _find_column(headers, "amount", "value")
    debit_i = _find_column(headers, "debit", "withdrawal", "money out", "paid out")
    credit_i = _find_column(headers, "credit", "deposit", "money in", "paid in")

    types = data_cleaner.detect_column_types(headers, rows)
    if date_i is None:
        date_i = next((i for i, h in enumerate(headers) if types.get(h) == "date"), None)
    if amount_i is None and debit_i is None:
        amount_i = next((i for i, h in enumerate(headers) if types.get(h) == "number"), None)
    if desc_i is None:
        desc_i = next((i for i, h in enumerate(headers)
                       if types.get(h) == "text" and i not in (date_i, amount_i)), None)

    if amount_i is None and debit_i is None:
        raise ValueError("Could not find an amount column in this file.")

    # Resolve M/D vs D/M once for the whole column, the same way Data Cleanup
    # does -- a single transaction can't disambiguate itself.
    order = "auto"
    if date_i is not None:
        order = data_cleaner.resolve_date_order(
            [data_cleaner.normalize_cell(r[date_i]) for r in rows if date_i < len(r)], "auto"
        )

    signed_values = []
    if amount_i is not None:
        for row in rows:
            if amount_i < len(row):
                value, ok = _to_amount(row[amount_i])
                if ok:
                    signed_values.append(value)
    mixed_signs = any(v < 0 for v in signed_values) and any(v > 0 for v in signed_values)

    transactions = []
    for row in rows:
        def cell(index):
            return data_cleaner.normalize_cell(row[index]) if index is not None and index < len(row) else ""

        raw_amount, ok = (0.0, False)
        possible_refund = False
        if debit_i is not None and cell(debit_i):
            raw_amount, ok = _to_amount(row[debit_i])
        elif credit_i is not None and cell(credit_i):
            raw_amount, ok = _to_amount(row[credit_i])
            possible_refund = ok
        elif amount_i is not None and amount_i < len(row):
            raw_amount, ok = _to_amount(row[amount_i])
            # Most exports write spending as negative. When a file mixes signs,
            # a positive row is probably money coming in -- surface it rather
            # than dropping it, and let the user delete it if it doesn't belong.
            possible_refund = ok and mixed_signs and raw_amount > 0
        if not ok:
            continue

        iso_date = ""
        date_ok = True
        raw_date = cell(date_i)
        if raw_date:
            parsed = data_cleaner.parse_date(raw_date)
            if parsed:
                resolved, ambiguous = data_cleaner.apply_date_order(parsed, order)
                if resolved and not ambiguous:
                    iso_date = resolved.isoformat()
                else:
                    date_ok = False
            else:
                date_ok = False

        transactions.append({
            "date": iso_date,
            "date_ok": date_ok,
            "raw_date": raw_date,
            "description": cell(desc_i) or "(no description)",
            "amount": round(abs(raw_amount), 2),
            "possible_refund": possible_refund,
            "source": filename,
        })
    return transactions


def _categorize_transactions(transactions, categories, language):
    """One batched call for the whole file rather than one per row -- a 300-line
    bank export stays a single request."""
    if not transactions:
        return {}
    payload = {
        "allowed_categories": categories,
        "transactions": [
            {"index": i, "description": t["description"], "amount": t["amount"], "date": t["date"]}
            for i, t in enumerate(transactions)
        ],
    }
    try:
        result = claude_client.call(
            system_prompt=_EXPENSE_CATEGORIZE_PROMPT,
            user_message=json.dumps(payload, ensure_ascii=False)[:24000],
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            language=language,
        )
    except Exception:
        return {}

    entries = result.get("entries") if isinstance(result, dict) else None
    if not isinstance(entries, list):
        return {}
    by_index = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        index = entry.get("index")
        if isinstance(index, int) and 0 <= index < len(transactions):
            by_index[index] = entry
    return by_index


def _receipt_entry(file, ext, categories, language):
    """Extract one receipt. Images go to Claude's vision; PDFs are read as text
    first (file_handler already OCRs image-only pages) and only fall back to
    vision if that turns up nothing."""
    instruction = (
        "Extract the expense from this receipt. "
        f"Choose a category from this list: {', '.join(categories)}."
    )

    if ext == ".pdf":
        text = extract_text(file)
        if text.strip():
            return claude_client.call(
                system_prompt=_EXPENSE_RECEIPT_PROMPT,
                user_message=f"{instruction}\n\nReceipt text:\n{text[:6000]}",
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                language=language,
            )
        file.stream.seek(0)

    image = claude_client.to_image_content(prepare_image(file))
    return claude_client.call(
        system_prompt=_EXPENSE_RECEIPT_PROMPT,
        user_message=instruction,
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        language=language,
        images=[image],
    )


def _normalize_entry(raw, source, fallback_category):
    amount, _ = _to_amount(raw.get("amount"))
    confidence = "low" if str(raw.get("confidence", "")).lower() == "low" else "high"
    iso = str(raw.get("date") or "").strip()
    if iso and _iso_or_none(iso) is None:
        iso = ""
    category = str(raw.get("category") or "").strip() or fallback_category
    return {
        "date": iso,
        "vendor": str(raw.get("vendor") or "").strip(),
        "amount": round(abs(amount), 2),
        "currency": str(raw.get("currency") or "").strip(),
        "category": category,
        "source": source,
        "notes": str(raw.get("notes") or "").strip(),
        "confidence": confidence,
        "reason": str(raw.get("reason") or "").strip(),
    }


@bp.post("/expenses")
@limiter.limit("10 per hour")
def expense_organizer():
    guard = _require_business()
    if guard:
        return guard
    guard = require_tool("expenses")
    if guard:
        return guard

    files = [f for f in request.files.getlist("files") if f and f.filename]
    if not files:
        return jsonify({"error": "at least one receipt or statement file is required"}), 400
    if len(files) > _MAX_EXPENSE_FILES:
        return jsonify({"error": f"Too many files — {_MAX_EXPENSE_FILES} max per submission"}), 400

    language = (request.form.get("language") or "en").strip()
    date_range = (request.form.get("date_range") or "all").strip()
    if date_range not in _DATE_RANGES:
        date_range = "all"
    start, end = _resolve_range(date_range,
                               request.form.get("start_date"),
                               request.form.get("end_date"))

    custom = [c.strip() for c in (request.form.get("categories") or "").split(",") if c.strip()]
    categories = custom or _DEFAULT_EXPENSE_CATEGORIES
    fallback_category = categories[-1]

    entries = []
    errors = []

    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        try:
            if ext in _TRANSACTION_EXTS:
                headers, rows = read_table(file)
                transactions = _transactions_from_table(headers, rows, file.filename)
                categorized = _categorize_transactions(transactions, categories, language)
                for index, transaction in enumerate(transactions):
                    detail = categorized.get(index, {})
                    entry = _normalize_entry({
                        "date": transaction["date"],
                        "vendor": detail.get("vendor") or transaction["description"],
                        "amount": transaction["amount"],
                        "category": detail.get("category"),
                        "notes": detail.get("notes") or "",
                        "confidence": detail.get("confidence", "low" if not detail else "high"),
                        "reason": detail.get("reason") or ("Could not categorize automatically." if not detail else ""),
                    }, file.filename, fallback_category)
                    _apply_transaction_flags(entry, transaction)
                    entries.append(entry)
            elif ext in _RECEIPT_IMAGE_EXTS or ext == ".pdf":
                raw = _receipt_entry(file, ext, categories, language)
                entries.append(_normalize_entry(raw, file.filename, fallback_category))
            else:
                errors.append({"filename": file.filename,
                               "error": f"Unsupported file type '{ext}'. Upload receipts (JPG, PNG, HEIC, PDF) or a .csv/.xlsx statement."})
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    kept, filtered_out = _filter_by_range(entries, start, end)
    totals = {}
    for entry in kept:
        totals[entry["category"]] = round(totals.get(entry["category"], 0.0) + entry["amount"], 2)

    return jsonify({
        "entries": kept,
        "totals": totals,
        "grand_total": round(sum(e["amount"] for e in kept), 2),
        "categories": categories,
        "errors": errors,
        "filtered_out": filtered_out,
        "range": {
            "mode": date_range,
            "start": start.isoformat() if start else "",
            "end": end.isoformat() if end else "",
        },
    })


def _apply_transaction_flags(entry, transaction):
    reasons = [entry["reason"]] if entry["reason"] else []
    if not transaction["date_ok"]:
        entry["confidence"] = "low"
        reasons.append(f"Could not read the date \"{transaction['raw_date']}\".")
    if transaction["possible_refund"]:
        entry["confidence"] = "low"
        reasons.append("This looks like money coming in, not an expense.")
    entry["reason"] = " ".join(reasons)


def _filter_by_range(entries, start, end):
    """Entries whose date couldn't be read are always kept -- dropping a receipt
    because its date was smudged is the worst thing this tool could do."""
    if not start and not end:
        return entries, 0
    kept = []
    removed = 0
    for entry in entries:
        parsed = _iso_or_none(entry["date"])
        if parsed is None:
            kept.append(entry)
            continue
        if (start and parsed < start) or (end and parsed > end):
            removed += 1
            continue
        kept.append(entry)
    return kept, removed


@bp.post("/expenses/export")
@limiter.limit("20 per hour")
def expenses_export():
    guard = _require_business()
    if guard:
        return guard
    guard = require_tool("expenses")
    if guard:
        return guard

    body = request.get_json(silent=True) or {}
    entries = body.get("entries")
    if not isinstance(entries, list) or not entries:
        return jsonify({"error": "entries are required"}), 400
    if len(entries) > spreadsheet.MAX_ROWS:
        return jsonify({"error": f"Too many rows — {spreadsheet.MAX_ROWS:,} is the maximum."}), 413

    labels = body.get("labels") if isinstance(body.get("labels"), list) else None
    headers = labels if labels and len(labels) == 6 else ["Date", "Vendor", "Amount", "Category", "Source", "Notes"]
    rows = [
        [
            str(e.get("date") or ""),
            str(e.get("vendor") or ""),
            _to_amount(e.get("amount"))[0],
            str(e.get("category") or ""),
            str(e.get("source") or ""),
            str(e.get("notes") or ""),
        ]
        for e in entries if isinstance(e, dict)
    ]
    filename = (body.get("filename") or "expenses").strip() or "expenses"
    try:
        data = write_table(headers, rows, "xlsx")
    except Exception as e:
        return jsonify({"error": f"Could not build the file: {e}"}), 500
    return send_file(
        io.BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{filename}.xlsx",
    )


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
    language = (body.get("language") or "").strip()
    if not email_to or not content_txt:
        return jsonify({"error": "email and content are required"}), 400
    try:
        success = send_pdf_email(email_to, subject, content_txt, filename, language)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not success:
        return jsonify({"error": "Failed to send PDF email — check SendGrid configuration."}), 500
    return jsonify({"sent": True})


@bp.post("/download-pdf")
@limiter.limit("10 per hour")
def download_pdf():
    guard = _require_business()
    if guard:
        return guard
    body = request.get_json(silent=True) or {}
    subject = (body.get("subject") or "Workblox Report").strip()
    content_txt = (body.get("content_txt") or "").strip()
    filename = (body.get("filename") or "report").strip()
    language = (body.get("language") or "").strip()
    if not content_txt:
        return jsonify({"error": "content_txt is required"}), 400
    try:
        pdf_bytes = _generate_pdf(subject, content_txt, language)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
