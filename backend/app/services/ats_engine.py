import os
import re
from datetime import datetime

KEYWORDS = {
    "Technical Skills": [
        "microsoft office", "excel", "word", "powerpoint", "outlook",
        "google sheets", "google docs", "google forms", "data entry", "quickbooks",
        "zoom", "slack", "trello", "asana", "wordpress",
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "time management", "attention to detail", "organized", "reliable",
        "multitasking", "customer service", "adaptable", "self-motivated",
        "critical thinking", "collaboration", "conflict resolution",
    ],
    "Action Verbs": [
        "managed", "managing", "developed", "created", "led", "improved", "increased",
        "reduced", "designed", "implemented", "coordinated", "coordinating", "analyzed",
        "delivered", "delivering", "achieved", "trained", "maintained", "maintaining",
        "streamlined", "generated", "launched", "negotiated", "supervised",
        "supported", "supporting", "provided", "providing", "assisted", "assisting",
    ],
    "Resume Essentials": [
        "experience", "education", "skills", "summary", "objective",
        "certifications", "references", "volunteer", "achievements", "projects",
    ],
}

JOB_KEYWORDS = {
    # --- Office & Admin ---
    "administrative assistant": [
        "administrative", "scheduling", "calendar management", "correspondence",
        "filing", "microsoft office", "excel", "word", "outlook", "data entry",
        "organized", "multitasking", "communication", "attention to detail",
        "office management", "travel arrangements", "expense reports", "confidential",
    ],
    "executive assistant": [
        "executive support", "calendar management", "scheduling", "travel arrangements",
        "correspondence", "confidential", "microsoft office", "board meetings",
        "expense reports", "project coordination", "stakeholder", "discretion",
        "communication", "organized", "prioritization",
    ],
    "receptionist": [
        "front desk", "reception", "phone handling", "customer service", "scheduling",
        "calendar management", "microsoft office", "organized", "communication",
        "multitasking", "professional", "greeting", "email management", "data entry",
    ],
    "office manager": [
        "office management", "administrative", "scheduling", "vendor management",
        "budgeting", "microsoft office", "organized", "leadership", "communication",
        "facilities", "supply ordering", "onboarding", "policies", "procedures",
    ],
    "data entry": [
        "data entry", "accuracy", "spreadsheet", "excel", "google sheets",
        "typing", "attention to detail", "organized", "quickbooks", "10-key",
        "database", "records management", "data integrity", "microsoft office",
    ],
    "virtual assistant": [
        "scheduling", "calendar management", "email management", "data entry",
        "communication", "organized", "microsoft office", "zoom", "trello", "asana",
        "remote", "research", "social media", "customer support", "invoicing",
    ],
    # --- Customer Facing ---
    "customer service": [
        "customer service", "communication", "problem solving", "crm",
        "salesforce", "phone support", "email support", "conflict resolution",
        "empathy", "patience", "customer satisfaction", "retention", "ticketing",
        "zendesk", "help desk", "follow-up",
    ],
    "call center": [
        "inbound", "outbound", "call center", "phone support", "crm", "salesforce",
        "customer service", "communication", "de-escalation", "conflict resolution",
        "high-volume", "multitasking", "empathy", "scripts", "metrics", "kpi",
    ],
    "sales associate": [
        "sales", "customer service", "product knowledge", "upselling", "cross-selling",
        "pos", "point of sale", "cash handling", "inventory", "communication",
        "goal-oriented", "quota", "teamwork", "retail", "merchandising",
    ],
    "retail associate": [
        "retail", "customer service", "cash handling", "pos", "point of sale",
        "inventory", "stocking", "merchandising", "product knowledge", "upselling",
        "teamwork", "communication", "organized", "loss prevention",
    ],
    "cashier": [
        "cash handling", "pos", "point of sale", "customer service", "accuracy",
        "transactions", "counting", "retail", "communication", "teamwork",
        "fast-paced", "reliable", "punctual",
    ],
    # --- Food & Hospitality ---
    "event server": [
        "fine dining", "banquet", "catering", "hospitality", "customer service",
        "food running", "food handler", "alcohol", "beverage service", "hors d'oeuvres",
        "tableside service", "buffet", "event setup", "breakdown", "guest engagement",
        "high-volume", "plating", "presentation", "wine", "punctuality", "reliability",
        "bilingual", "communication", "teamwork", "attention to detail",
    ],
    "hospitality": [
        "fine dining", "banquet", "catering", "hospitality", "customer service",
        "food running", "food handler", "alcohol", "beverage service", "hors d'oeuvres",
        "tableside service", "buffet", "event setup", "breakdown", "guest engagement",
        "high-volume", "plating", "presentation", "wine", "punctuality", "reliability",
        "bilingual", "communication", "teamwork", "attention to detail",
    ],
    "server": [
        "food service", "customer service", "menu knowledge", "upselling",
        "pos", "cash handling", "teamwork", "communication", "multitasking",
        "food handler", "alcohol", "fast-paced", "guest satisfaction", "sidework",
    ],
    "barista": [
        "espresso", "coffee", "latte art", "pos", "cash handling", "customer service",
        "food handler", "fast-paced", "teamwork", "communication", "cleanliness",
        "drink preparation", "inventory", "opening", "closing",
    ],
    "cook": [
        "food preparation", "knife skills", "food safety", "servsafe", "food handler",
        "line cook", "prep cook", "recipe", "portion control", "sanitation",
        "fast-paced", "teamwork", "inventory", "cleanliness", "mise en place",
    ],
    "restaurant manager": [
        "restaurant management", "food service", "scheduling", "inventory",
        "food safety", "servsafe", "customer service", "leadership", "training",
        "budgeting", "cost control", "pos", "staff management", "communication",
    ],
    # --- Warehouse & Logistics ---
    "warehouse associate": [
        "warehouse", "forklift", "pallet jack", "inventory", "shipping", "receiving",
        "pick and pack", "order fulfillment", "rf scanner", "safety", "lifting",
        "organized", "teamwork", "fast-paced", "accuracy",
    ],
    "forklift operator": [
        "forklift", "forklift certified", "pallet jack", "warehouse", "inventory",
        "shipping", "receiving", "safety", "rf scanner", "order fulfillment",
        "lifting", "organized", "accuracy", "reach truck",
    ],
    "delivery driver": [
        "driving", "route optimization", "delivery", "customer service", "navigation",
        "gps", "dot", "clean driving record", "vehicle inspection", "time management",
        "communication", "punctual", "reliable", "lifting", "organized",
    ],
    "inventory specialist": [
        "inventory management", "cycle counts", "stock", "shipping", "receiving",
        "rf scanner", "accuracy", "organized", "data entry", "excel",
        "warehouse management system", "wms", "shrinkage", "reconciliation",
    ],
    # --- Healthcare & Caregiving ---
    "caregiver": [
        "caregiving", "personal care", "activities of daily living", "adl",
        "companionship", "medication reminders", "patient care", "empathy",
        "communication", "reliable", "cpr", "first aid", "compassionate",
        "homecare", "elderly care", "documentation",
    ],
    "home health aide": [
        "home health", "patient care", "activities of daily living", "adl",
        "vital signs", "medication", "documentation", "empathy", "cpr",
        "first aid", "reliable", "compassionate", "hha certified", "homecare",
    ],
    "medical assistant": [
        "medical assistant", "clinical", "administrative", "ehr", "epic",
        "vital signs", "phlebotomy", "injections", "patient care", "hipaa",
        "scheduling", "insurance", "medical terminology", "cpr", "certified",
    ],
    "certified nursing assistant": [
        "cna", "certified nursing assistant", "patient care", "vital signs",
        "adl", "activities of daily living", "documentation", "empathy",
        "teamwork", "long-term care", "hipaa", "cpr", "reliable", "compassionate",
    ],
    "pharmacy technician": [
        "pharmacy", "medication dispensing", "prescription", "accuracy",
        "insurance billing", "customer service", "data entry", "hipaa",
        "retail pharmacy", "inventory", "ptcb", "certified", "communication",
    ],
    # --- Cleaning & Maintenance ---
    "housekeeper": [
        "housekeeping", "cleaning", "sanitizing", "laundry", "attention to detail",
        "organized", "reliable", "punctual", "teamwork", "time management",
        "chemical safety", "room turnover", "linen", "hospitality",
    ],
    "janitor": [
        "janitorial", "cleaning", "sanitizing", "floor care", "buffing",
        "chemical safety", "organized", "reliable", "time management",
        "maintenance", "trash removal", "attention to detail", "teamwork",
    ],
    "maintenance technician": [
        "maintenance", "repair", "troubleshooting", "electrical", "plumbing",
        "hvac", "preventive maintenance", "work orders", "tools", "safety",
        "organized", "reliable", "communication", "facilities",
    ],
    # --- Education & Childcare ---
    "teacher assistant": [
        "classroom support", "lesson plans", "student engagement", "communication",
        "organized", "patience", "teamwork", "curriculum", "special needs",
        "documentation", "behavior management", "bilingual", "technology",
    ],
    "childcare worker": [
        "childcare", "child development", "cpr", "first aid", "patience",
        "communication", "organized", "creative", "teamwork", "lesson planning",
        "safety", "nurturing", "reliable", "documentation",
    ],
    "tutor": [
        "tutoring", "lesson planning", "communication", "patience", "organized",
        "curriculum", "student progress", "subject matter", "assessment",
        "adaptable", "technology", "math", "reading", "writing",
    ],
    # --- Security ---
    "security guard": [
        "security", "patrol", "surveillance", "access control", "incident report",
        "communication", "cpr", "first aid", "licensed", "reliable", "punctual",
        "conflict resolution", "de-escalation", "customer service", "observant",
    ],
    # --- Tech ---
    "web developer": [
        "html", "css", "javascript", "responsive", "mobile-friendly",
        "wordpress", "git", "debugging", "python", "sql", "react", "api",
        "version control", "deployment", "testing",
    ],
    "it support": [
        "troubleshooting", "help desk", "technical support", "windows", "active directory",
        "networking", "hardware", "software", "ticketing", "communication",
        "customer service", "comptia", "remote support", "documentation", "vpn",
    ],
    "social media manager": [
        "social media", "content creation", "instagram", "facebook", "tiktok",
        "scheduling", "analytics", "engagement", "canva", "copywriting",
        "brand voice", "strategy", "community management", "paid ads", "seo",
    ],
    # --- Finance & Bookkeeping ---
    "bookkeeper": [
        "bookkeeping", "quickbooks", "accounts payable", "accounts receivable",
        "bank reconciliation", "payroll", "invoicing", "excel", "accuracy",
        "organized", "financial reporting", "gaap", "attention to detail",
    ],
    "accounting clerk": [
        "accounting", "accounts payable", "accounts receivable", "data entry",
        "excel", "quickbooks", "invoicing", "reconciliation", "organized",
        "accuracy", "communication", "financial records", "attention to detail",
    ],
    # --- Construction & Labor ---
    "general laborer": [
        "labor", "lifting", "physical stamina", "safety", "osha", "teamwork",
        "reliable", "punctual", "tools", "construction", "outdoor", "fast-paced",
        "organized", "following instructions",
    ],
    "landscaper": [
        "landscaping", "lawn care", "mowing", "trimming", "planting", "irrigation",
        "outdoor", "physical stamina", "safety", "reliable", "tools",
        "customer service", "teamwork", "organized",
    ],
    "catering": [
        "catering", "banquet", "event setup", "breakdown", "food service",
        "food handler", "beverage service", "buffet", "plating", "presentation",
        "high-volume", "customer service", "teamwork", "communication",
        "alcohol", "servsafe", "punctuality", "reliability", "hospitality",
        "tableside service", "guest engagement", "event coordination",
    ],
    "freelance caterer": [
        "catering", "freelance", "event planning", "food preparation", "food handler",
        "servsafe", "banquet", "buffet", "beverage service", "plating", "presentation",
        "event setup", "breakdown", "client relations", "self-motivated", "reliable",
        "scheduling", "invoicing", "menu planning", "food safety", "hospitality",
        "alcohol", "high-volume", "communication", "attention to detail",
    ],

}

SECTION_PATTERNS = {
    "Summary / Objective": r'\b(summary|objective|profile|about me|professional profile)\b',
    "Work Experience":      r'\b(experience|work history|employment|professional experience|work experience)\b',
    "Education":            r'\b(education|academic|degree|university|college|school|diploma|graduate)\b',
    "Skills":               r'\b(skills|competencies|technical skills|core competencies|areas of expertise)\b',
    "Certifications":       r'\b(certif|license|credential|accredit)\w*\b',
    "Achievements":         r'\b(achievement|award|honor|recognition|accomplishment)\w*\b',
    "Volunteer":            r'\b(volunteer|community service|nonprofit)\w*\b',
}

_ROLE_SUMMARIES = {
    "hospitality": (
        "Dedicated hospitality professional with extensive experience in banquet service, "
        "fine dining, and catering. Known for delivering exceptional guest experiences in "
        "high-volume environments with a commitment to attention to detail, punctuality, "
        "and teamwork. Bilingual with a polished, professional presentation."
    ),
    "event server": (
        "Experienced event server and banquet professional with a strong background in "
        "tableside service, buffet operations, and guest engagement. Reliable and punctual "
        "with a proven ability to thrive in fast-paced, high-volume catering environments."
    ),
    "customer service": (
        "Customer-focused professional with proven experience resolving inquiries, building "
        "client relationships, and delivering consistent service excellence. Strong communicator "
        "skilled in CRM systems, conflict resolution, and multi-channel support."
    ),
    "data entry": (
        "Detail-oriented data entry specialist with demonstrated accuracy in spreadsheet "
        "management, data processing, and administrative support. Proficient in Microsoft "
        "Office Suite with a strong commitment to organized, efficient workflow."
    ),
    "virtual assistant": (
        "Organized and self-motivated virtual assistant with expertise in calendar management, "
        "email coordination, and remote team support. Proficient in Microsoft Office, Google "
        "Workspace, and project management tools including Trello and Asana."
    ),
    "web developer": (
        "Results-driven web developer with hands-on experience in HTML, CSS, JavaScript, and "
        "responsive design. Skilled in debugging, version control with Git, and delivering "
        "clean, mobile-friendly interfaces on schedule."
    ),
}

_GENERIC_SUMMARY = (
    "Results-oriented professional with a strong foundation in communication, teamwork, and "
    "attention to detail. Committed to delivering quality work efficiently while adapting "
    "to new challenges with a positive, solutions-focused mindset."
)


def normalize(text):
    return (text
        .replace('‘', "'").replace('’', "'")
        .replace('“', '"').replace('”', '"')
        .replace('—', '-').replace('–', '-')
    )


def match_keywords(text, keyword_list):
    text_lower = re.sub(r'\s+', ' ', normalize(text).lower())
    pairs = [(kw, normalize(kw).lower()) for kw in keyword_list]
    found   = [kw for kw, nkw in pairs if nkw in text_lower]
    missing = [kw for kw, nkw in pairs if nkw not in text_lower]
    return found, missing


def check_formatting(text):
    warnings, tips = [], []
    if len(text) < 200:
        warnings.append("Resume seems very short (under 200 characters)")
    if not re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text):
        warnings.append("No email address detected")
    if not re.search(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
        tips.append("Consider adding a phone number")
    if len(text) > 6000:
        tips.append("Resume may be too long — aim for 1 page (or 2 max)")
    word_count = len(text.split())
    if word_count < 100:
        warnings.append(f"Very few words detected ({word_count}) — resume may be incomplete")
    return warnings, tips


def check_contact_info(text):
    return {
        "email":    bool(re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)),
        "phone":    bool(re.search(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text)),
        "linkedin": bool(re.search(r'linkedin\.com/in/', text, re.I)),
        "location": bool(re.search(r'\b[A-Z][a-zA-Z\s]+,\s*[A-Z]{2}\b', text)),
    }


def check_quantification(text):
    metric_patterns = [
        r'\d+\s*%',
        r'\$\s*[\d,]+',
        r'\b\d+\s*(?:people|employees|staff|clients|customers|guests|accounts|members|team)\b',
        r'\b(?:increased|decreased|reduced|improved|grew|saved|generated|managed)\w*\s+\w+\s+by\s+\d+',
        r'\b\d{1,3}(?:,\d{3})+\b',
    ]
    examples = []
    for pattern in metric_patterns:
        examples.extend(m.group(0) for m in re.finditer(pattern, text, re.I))
    return {
        "has_metrics":  bool(examples),
        "number_count": len(re.findall(r'\b\d+\b', text)),
        "examples":     examples[:4],
    }


def check_sections(text):
    text_lower = re.sub(r'\s+', ' ', text.lower())
    return {name: bool(re.search(pat, text_lower)) for name, pat in SECTION_PATTERNS.items()}


def build_recommendations(results, job_role=None):
    recs = []
    cats = results["categories"]

    if results.get("job_match") and results["job_match"]["missing"]:
        missing = results["job_match"]["missing"]
        tail = f" (+{len(missing)-6} more)" if len(missing) > 6 else ""
        recs.append({
            "priority": "high",
            "title": f"Add {job_role or 'job'}-specific keywords",
            "detail": f"Critical for this role — add to Skills or Experience: {', '.join(missing[:6])}{tail}",
        })

    if not results.get("quantification", {}).get("has_metrics"):
        recs.append({
            "priority": "high",
            "title": "Add measurable achievements",
            "detail": 'Numbers make bullets stand out — e.g. "Managed 15-person team", "Reduced costs by 20%"',
        })

    missing_verbs = cats["Action Verbs"]["missing"]
    if len(missing_verbs) > 10:
        recs.append({
            "priority": "high",
            "title": "Strengthen bullet points with action verbs",
            "detail": f"Start each bullet with: {', '.join(missing_verbs[:6])}",
        })
    elif len(missing_verbs) > 4:
        recs.append({
            "priority": "medium",
            "title": "Add more action verbs",
            "detail": f"Consider using: {', '.join(missing_verbs[:5])}",
        })

    missing_tech = cats["Technical Skills"]["missing"]
    if len(missing_tech) > len(cats["Technical Skills"]["found"]):
        recs.append({
            "priority": "high",
            "title": "Expand your Technical Skills section",
            "detail": f"Add any you're familiar with: {', '.join(missing_tech[:6])}",
        })

    sections = results.get("sections", {})
    if not sections.get("Summary / Objective"):
        recs.append({
            "priority": "medium",
            "title": "Add a professional summary",
            "detail": "3–4 lines at the top tailored to the target role",
        })

    if not sections.get("Skills"):
        recs.append({
            "priority": "medium",
            "title": 'Add a dedicated "Skills" section',
            "detail": "A clearly labeled Skills section helps ATS extract your qualifications instantly",
        })

    contact = results.get("contact", {})
    missing_contact = []
    if not contact.get("linkedin"): missing_contact.append("LinkedIn URL")
    if not contact.get("location"): missing_contact.append("City, State")
    if missing_contact:
        recs.append({
            "priority": "medium",
            "title": "Complete your contact information",
            "detail": f"Consider adding: {', '.join(missing_contact)}",
        })

    missing_soft = cats["Soft Skills"]["missing"]
    if len(missing_soft) > 7:
        recs.append({
            "priority": "low",
            "title": "Weave in more soft skills",
            "detail": f"Use naturally in your summary or bullets: {', '.join(missing_soft[:5])}",
        })

    order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: order.get(r["priority"], 3))
    return recs


def analyze(resume_text, job_role=None, custom_keywords=None):
    results = {}
    total_found = total_possible = 0

    category_results = {}
    for category, keywords in KEYWORDS.items():
        found, missing = match_keywords(resume_text, keywords)
        category_results[category] = {
            "found": found, "missing": missing,
            "score": len(found), "total": len(keywords),
        }
        total_found    += len(found)
        total_possible += len(keywords)
    results["categories"] = category_results

    if job_role:
        role_key = job_role.lower().strip()
        job_kws  = next((v for k, v in JOB_KEYWORDS.items() if k in role_key or role_key in k), None)
        if job_kws:
            found, missing = match_keywords(resume_text, job_kws)
            results["job_match"] = {
                "role": job_role, "found": found, "missing": missing,
                "score": len(found), "total": len(job_kws),
            }
            total_found    += len(found)
            total_possible += len(job_kws)
        else:
            results["job_match"] = None

    if custom_keywords:
        found, missing = match_keywords(resume_text, custom_keywords)
        results["custom"] = {
            "found": found, "missing": missing,
            "score": len(found), "total": len(custom_keywords),
        }
        total_found    += len(found)
        total_possible += len(custom_keywords)

    warnings, tips = check_formatting(resume_text)
    results["warnings"]        = warnings
    results["tips"]            = tips
    results["contact"]         = check_contact_info(resume_text)
    results["quantification"]  = check_quantification(resume_text)
    results["sections"]        = check_sections(resume_text)

    base_score = int((total_found / total_possible) * 85) if total_possible else 0
    results["score"]          = max(0, min(100, base_score - len(warnings) * 5))
    results["total_found"]    = total_found
    results["total_possible"] = total_possible
    results["recommendations"] = build_recommendations(results, job_role)

    return results


def grade(score):
    if score >= 80: return "A — Excellent"
    if score >= 65: return "B — Good"
    if score >= 50: return "C — Needs Work"
    if score >= 35: return "D — Weak"
    return            "F — Major Revision Needed"


def build_report(results, filename):
    lines = []
    w = 58
    lines += [
        "=" * w,
        "  ATS RESUME ANALYZER — REPORT",
        f"  File : {os.path.basename(filename)}",
        f"  Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * w,
        f"\n  OVERALL SCORE : {results['score']} / 100",
        f"  GRADE         : {grade(results['score'])}",
        f"  KEYWORDS FOUND: {results['total_found']} / {results['total_possible']}",
        "",
    ]
    filled = int(results['score'] / 5)
    lines.append(f"  [{'█' * filled}{'░' * (20 - filled)}] {results['score']}%\n")

    c = results.get("contact", {})
    lines += ["=" * w, "  CONTACT INFO", "-" * w]
    for label, key in [("Email", "email"), ("Phone", "phone"), ("LinkedIn", "linkedin"), ("Location", "location")]:
        lines.append(f"  {label:<12}: {'YES' if c.get(key) else 'MISSING'}")

    recs = results.get("recommendations", [])
    if recs:
        lines += ["", "=" * w, "  RECOMMENDATIONS", "-" * w]
        for i, rec in enumerate(recs, 1):
            lines += [f"  {i}. [{rec['priority'].upper()}] {rec['title']}", f"     {rec['detail']}", ""]

    if results["warnings"]:
        lines += ["=" * w, "  WARNINGS", "-" * w]
        lines += [f"  !  {m}" for m in results["warnings"]]

    if results["tips"]:
        lines += ["", "  TIPS"]
        lines += [f"  ->  {t}" for t in results["tips"]]

    if results.get("job_match"):
        jm = results["job_match"]
        lines += ["", "=" * w, f"  JOB MATCH: {jm['role'].upper()}", f"  {jm['score']} / {jm['total']} keywords found", "-" * w]
        if jm["found"]:   lines.append("  Found   : " + ", ".join(jm["found"]))
        if jm["missing"]: lines.append("  Missing : " + ", ".join(jm["missing"]))

    lines += ["", "=" * w, "  KEYWORD BREAKDOWN", "=" * w]
    for cat, data in results["categories"].items():
        pct = int((data["score"] / data["total"]) * 100) if data["total"] else 0
        lines += [f"\n  {cat}  ({data['score']}/{data['total']}  {pct}%)", "  " + "-" * (w - 2)]
        if data["found"]:   lines.append("  Found   : " + ", ".join(data["found"]))
        if data["missing"]: lines.append("  Missing : " + ", ".join(data["missing"]))

    lines += ["", "=" * w, "  END OF REPORT — Generated by Workblox", "=" * w]
    return "\n".join(lines)


def generate_revised(original_text, results, job_role=None):
    lines   = original_text.rstrip().split('\n')
    revised = list(lines)
    changes = []

    if not results.get('sections', {}).get('Summary / Objective'):
        role_key = (job_role or '').lower().strip()
        body = next((v for k, v in _ROLE_SUMMARIES.items() if k in role_key or role_key in k), _GENERIC_SUMMARY)
        revised = ['PROFESSIONAL SUMMARY', '-' * 28, body, ''] + revised
        changes.append('Added Professional Summary section at top')

    missing_tech = results['categories']['Technical Skills']['missing']
    missing_soft = results['categories']['Soft Skills']['missing'][:5]
    missing_job  = (results.get('job_match') or {}).get('missing', [])

    seen, keywords_to_add = set(), []
    for kw in missing_job + missing_tech + missing_soft:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            keywords_to_add.append(kw)

    if keywords_to_add:
        kw_preview = ', '.join(keywords_to_add[:12])
        if results.get('sections', {}).get('Skills'):
            revised.append('')
            revised.append(f'[ REVISION NOTE: Weave these missing keywords naturally into your Summary, Skills, or bullets: {kw_preview} ]')
            changes.append(f'Flagged {min(len(keywords_to_add), 12)} missing keywords for natural integration')
        else:
            chunk = keywords_to_add
            kw_lines = []
            while chunk:
                kw_lines.append(', '.join(chunk[:8]))
                chunk = chunk[8:]
            revised += ['', 'SKILLS', '-' * 28] + kw_lines
            changes.append(f'Added Skills section with {len(keywords_to_add)} keywords')

    if not results.get('quantification', {}).get('has_metrics'):
        revised += ['', '[ REVISION NOTE: Add specific numbers to your bullets — e.g. "Served 150+ guests nightly", "Managed team of 8" ]']
        changes.append('Added note to incorporate measurable results')

    return lines, revised, changes
