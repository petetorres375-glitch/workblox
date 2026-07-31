"""English ATS corpus.

Extracted verbatim from the original ats_engine, so English scoring is
unchanged. This is the reference corpus: every other language mirrors these
keys, and ats_corpora.check_parity() asserts that they do.
"""


KEYWORDS = {
    "Technical Skills": [
        "microsoft office", "excel", "word", "powerpoint", "outlook", "google sheets",
        "google docs", "google forms", "data entry", "quickbooks", "zoom", "slack",
        "trello", "asana", "wordpress",
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving", "time management",
        "attention to detail", "organized", "reliable", "multitasking", "customer service",
        "adaptable", "self-motivated", "critical thinking", "collaboration",
        "conflict resolution",
    ],
    "Action Verbs": [
        "managed", "managing", "developed", "created", "led", "improved", "increased",
        "reduced", "designed", "implemented", "coordinated", "coordinating", "analyzed",
        "delivered", "delivering", "achieved", "trained", "maintained", "maintaining",
        "streamlined", "generated", "launched", "negotiated", "supervised", "supported",
        "supporting", "provided", "providing", "assisted", "assisting",
    ],
    "Resume Essentials": [
        "experience", "education", "skills", "summary", "objective", "certifications",
        "references", "volunteer", "achievements", "projects",
    ],
}

JOB_KEYWORDS = {
    "administrative assistant": [
        "administrative", "scheduling", "calendar management", "correspondence", "filing",
        "microsoft office", "excel", "word", "outlook", "data entry", "organized",
        "multitasking", "communication", "attention to detail", "office management",
        "travel arrangements", "expense reports", "confidential",
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
        "data entry", "accuracy", "spreadsheet", "excel", "google sheets", "typing",
        "attention to detail", "organized", "quickbooks", "10-key", "database",
        "records management", "data integrity", "microsoft office",
    ],
    "virtual assistant": [
        "scheduling", "calendar management", "email management", "data entry",
        "communication", "organized", "microsoft office", "zoom", "trello", "asana",
        "remote", "research", "social media", "customer support", "invoicing",
    ],
    "customer service": [
        "customer service", "communication", "problem solving", "crm", "salesforce",
        "phone support", "email support", "conflict resolution", "empathy", "patience",
        "customer satisfaction", "retention", "ticketing", "zendesk", "help desk",
        "follow-up",
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
        "retail", "customer service", "cash handling", "pos", "point of sale", "inventory",
        "stocking", "merchandising", "product knowledge", "upselling", "teamwork",
        "communication", "organized", "loss prevention",
    ],
    "cashier": [
        "cash handling", "pos", "point of sale", "customer service", "accuracy",
        "transactions", "counting", "retail", "communication", "teamwork", "fast-paced",
        "reliable", "punctual",
    ],
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
        "food service", "customer service", "menu knowledge", "upselling", "pos",
        "cash handling", "teamwork", "communication", "multitasking", "food handler",
        "alcohol", "fast-paced", "guest satisfaction", "sidework",
    ],
    "barista": [
        "espresso", "coffee", "latte art", "pos", "cash handling", "customer service",
        "food handler", "fast-paced", "teamwork", "communication", "cleanliness",
        "drink preparation", "inventory", "opening", "closing",
    ],
    "cook": [
        "food preparation", "knife skills", "food safety", "servsafe", "food handler",
        "line cook", "prep cook", "recipe", "portion control", "sanitation", "fast-paced",
        "teamwork", "inventory", "cleanliness", "mise en place",
    ],
    "restaurant manager": [
        "restaurant management", "food service", "scheduling", "inventory", "food safety",
        "servsafe", "customer service", "leadership", "training", "budgeting",
        "cost control", "pos", "staff management", "communication",
    ],
    "warehouse associate": [
        "warehouse", "forklift", "pallet jack", "inventory", "shipping", "receiving",
        "pick and pack", "order fulfillment", "rf scanner", "safety", "lifting",
        "organized", "teamwork", "fast-paced", "accuracy",
    ],
    "forklift operator": [
        "forklift", "forklift certified", "pallet jack", "warehouse", "inventory",
        "shipping", "receiving", "safety", "rf scanner", "order fulfillment", "lifting",
        "organized", "accuracy", "reach truck",
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
    "caregiver": [
        "caregiving", "personal care", "activities of daily living", "adl",
        "companionship", "medication reminders", "patient care", "empathy",
        "communication", "reliable", "cpr", "first aid", "compassionate", "homecare",
        "elderly care", "documentation",
    ],
    "home health aide": [
        "home health", "patient care", "activities of daily living", "adl", "vital signs",
        "medication", "documentation", "empathy", "cpr", "first aid", "reliable",
        "compassionate", "hha certified", "homecare",
    ],
    "medical assistant": [
        "medical assistant", "clinical", "administrative", "ehr", "epic", "vital signs",
        "phlebotomy", "injections", "patient care", "hipaa", "scheduling", "insurance",
        "medical terminology", "cpr", "certified",
    ],
    "certified nursing assistant": [
        "cna", "certified nursing assistant", "patient care", "vital signs", "adl",
        "activities of daily living", "documentation", "empathy", "teamwork",
        "long-term care", "hipaa", "cpr", "reliable", "compassionate",
    ],
    "pharmacy technician": [
        "pharmacy", "medication dispensing", "prescription", "accuracy",
        "insurance billing", "customer service", "data entry", "hipaa", "retail pharmacy",
        "inventory", "ptcb", "certified", "communication",
    ],
    "housekeeper": [
        "housekeeping", "cleaning", "sanitizing", "laundry", "attention to detail",
        "organized", "reliable", "punctual", "teamwork", "time management",
        "chemical safety", "room turnover", "linen", "hospitality",
    ],
    "janitor": [
        "janitorial", "cleaning", "sanitizing", "floor care", "buffing", "chemical safety",
        "organized", "reliable", "time management", "maintenance", "trash removal",
        "attention to detail", "teamwork",
    ],
    "maintenance technician": [
        "maintenance", "repair", "troubleshooting", "electrical", "plumbing", "hvac",
        "preventive maintenance", "work orders", "tools", "safety", "organized",
        "reliable", "communication", "facilities",
    ],
    "teacher assistant": [
        "classroom support", "lesson plans", "student engagement", "communication",
        "organized", "patience", "teamwork", "curriculum", "special needs",
        "documentation", "behavior management", "bilingual", "technology",
    ],
    "childcare worker": [
        "childcare", "child development", "cpr", "first aid", "patience", "communication",
        "organized", "creative", "teamwork", "lesson planning", "safety", "nurturing",
        "reliable", "documentation",
    ],
    "tutor": [
        "tutoring", "lesson planning", "communication", "patience", "organized",
        "curriculum", "student progress", "subject matter", "assessment", "adaptable",
        "technology", "math", "reading", "writing",
    ],
    "security guard": [
        "security", "patrol", "surveillance", "access control", "incident report",
        "communication", "cpr", "first aid", "licensed", "reliable", "punctual",
        "conflict resolution", "de-escalation", "customer service", "observant",
    ],
    "web developer": [
        "html", "css", "javascript", "responsive", "mobile-friendly", "wordpress", "git",
        "debugging", "python", "sql", "react", "api", "version control", "deployment",
        "testing",
    ],
    "it support": [
        "troubleshooting", "help desk", "technical support", "windows", "active directory",
        "networking", "hardware", "software", "ticketing", "communication",
        "customer service", "comptia", "remote support", "documentation", "vpn",
    ],
    "social media manager": [
        "social media", "content creation", "instagram", "facebook", "tiktok",
        "scheduling", "analytics", "engagement", "canva", "copywriting", "brand voice",
        "strategy", "community management", "paid ads", "seo",
    ],
    "bookkeeper": [
        "bookkeeping", "quickbooks", "accounts payable", "accounts receivable",
        "bank reconciliation", "payroll", "invoicing", "excel", "accuracy", "organized",
        "financial reporting", "gaap", "attention to detail",
    ],
    "accounting clerk": [
        "accounting", "accounts payable", "accounts receivable", "data entry", "excel",
        "quickbooks", "invoicing", "reconciliation", "organized", "accuracy",
        "communication", "financial records", "attention to detail",
    ],
    "general laborer": [
        "labor", "lifting", "physical stamina", "safety", "osha", "teamwork", "reliable",
        "punctual", "tools", "construction", "outdoor", "fast-paced", "organized",
        "following instructions",
    ],
    "landscaper": [
        "landscaping", "lawn care", "mowing", "trimming", "planting", "irrigation",
        "outdoor", "physical stamina", "safety", "reliable", "tools", "customer service",
        "teamwork", "organized",
    ],
    "catering": [
        "catering", "banquet", "event setup", "breakdown", "food service", "food handler",
        "beverage service", "buffet", "plating", "presentation", "high-volume",
        "customer service", "teamwork", "communication", "alcohol", "servsafe",
        "punctuality", "reliability", "hospitality", "tableside service",
        "guest engagement", "event coordination",
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
    "Summary / Objective": r"\b(summary|objective|profile|about me|professional profile)\b",
    "Work Experience"    : r"\b(experience|work history|employment|professional experience|work experience)\b",
    "Education"          : r"\b(education|academic|degree|university|college|school|diploma|graduate)\b",
    "Skills"             : r"\b(skills|competencies|technical skills|core competencies|areas of expertise)\b",
    "Certifications"     : r"\b(certif|license|credential|accredit)\w*\b",
    "Achievements"       : r"\b(achievement|award|honor|recognition|accomplishment)\w*\b",
    "Volunteer"          : r"\b(volunteer|community service|nonprofit)\w*\b",
}

ROLE_SUMMARIES = {
    "hospitality": (
        "Dedicated hospitality professional with extensive experience in banquet "
        "service, fine dining, and catering. Known for delivering exceptional guest "
        "experiences in high-volume environments with a commitment to attention to "
        "detail, punctuality, and teamwork. Bilingual with a polished, professional "
        "presentation."
    ),
    "event server": (
        "Experienced event server and banquet professional with a strong background in "
        "tableside service, buffet operations, and guest engagement. Reliable and "
        "punctual with a proven ability to thrive in fast-paced, high-volume catering "
        "environments."
    ),
    "customer service": (
        "Customer-focused professional with proven experience resolving inquiries, "
        "building client relationships, and delivering consistent service excellence. "
        "Strong communicator skilled in CRM systems, conflict resolution, and "
        "multi-channel support."
    ),
    "data entry": (
        "Detail-oriented data entry specialist with demonstrated accuracy in "
        "spreadsheet management, data processing, and administrative support. "
        "Proficient in Microsoft Office Suite with a strong commitment to organized, "
        "efficient workflow."
    ),
    "virtual assistant": (
        "Organized and self-motivated virtual assistant with expertise in calendar "
        "management, email coordination, and remote team support. Proficient in "
        "Microsoft Office, Google Workspace, and project management tools including "
        "Trello and Asana."
    ),
    "web developer": (
        "Results-driven web developer with hands-on experience in HTML, CSS, "
        "JavaScript, and responsive design. Skilled in debugging, version control with "
        "Git, and delivering clean, mobile-friendly interfaces on schedule."
    ),
}

GENERIC_SUMMARY = (
    "Results-oriented professional with a strong foundation in communication, "
    "teamwork, and attention to detail. Committed to delivering quality work "
    "efficiently while adapting to new challenges with a positive, "
    "solutions-focused mindset."
)


# Category and section keys are stable identifiers shared by every corpus --
# build_recommendations() looks up cats["Soft Skills"] and sections["Skills"]
# by name, so translating the keys would break scoring. Only these labels are
# localized; the keys never change.
CATEGORY_LABELS = {
    "Technical Skills": "Technical Skills",
    "Soft Skills":      "Soft Skills",
    "Action Verbs":     "Action Verbs",
    "Resume Essentials": "Resume Essentials",
}

SECTION_LABELS = {
    "Summary / Objective": "Summary / Objective",
    "Work Experience":     "Work Experience",
    "Education":           "Education",
    "Skills":              "Skills",
    "Certifications":      "Certifications",
    "Achievements":        "Achievements",
    "Volunteer":           "Volunteer",
}

# Patterns that show a bullet is quantified ("increased sales by 30%").
METRIC_PATTERNS = [
    r"\d+\s*%",
    r"\$\s*[\d,]+",
    r"\b\d+\s*(?:people|employees|staff|clients|customers|guests|accounts|members|team)\b",
    r"\b(?:increased|decreased|reduced|improved|grew|saved|generated|managed)\w*\s+\w+\s+by\s+\d+",
    r"\b\d{1,3}(?:,\d{3})+\b",
]

# "City, ST" -- US-style. Other locales override this.
LOCATION_PATTERN = r"\b[A-Z][a-zA-Z\s]+,\s*[A-Z]{2}\b"

MESSAGES = {
    "warn_short":        "Resume seems very short (under 200 characters)",
    "warn_no_email":     "No email address detected",
    "warn_few_words":    "Very few words detected ({count}) — resume may be incomplete",
    "tip_phone":         "Consider adding a phone number",
    "tip_too_long":      "Resume may be too long — aim for 1 page (or 2 max)",

    "rec_role_title":    "Add {role}-specific keywords",
    "rec_role_detail":   "Critical for this role — add to Skills or Experience: {keywords}",
    "rec_role_overflow": " (+{count} more)",
    "rec_metrics_title": "Add measurable achievements",
    "rec_metrics_detail": 'Numbers make bullets stand out — e.g. "Managed 15-person team", "Reduced costs by 20%"',
    "rec_verbs_strong_title":  "Strengthen bullet points with action verbs",
    "rec_verbs_strong_detail": "Start each bullet with: {keywords}",
    "rec_verbs_more_title":    "Add more action verbs",
    "rec_verbs_more_detail":   "Consider using: {keywords}",
    "rec_tech_title":    "Expand your Technical Skills section",
    "rec_tech_detail":   "Add any you're familiar with: {keywords}",
    "rec_summary_title": "Add a professional summary",
    "rec_summary_detail": "3–4 lines at the top tailored to the target role",
    "rec_skills_title":  'Add a dedicated "Skills" section',
    "rec_skills_detail": "A clearly labeled Skills section helps ATS extract your qualifications instantly",
    "rec_contact_title": "Complete your contact information",
    "rec_contact_detail": "Consider adding: {items}",
    "rec_soft_title":    "Weave in more soft skills",
    "rec_soft_detail":   "Use naturally in your summary or bullets: {keywords}",

    "contact_linkedin":  "LinkedIn URL",
    "contact_location":  "City, State",

    "grade_a": "A — Excellent",
    "grade_b": "B — Good",
    "grade_c": "C — Needs Work",
    "grade_d": "D — Weak",
    "grade_f": "F — Major Revision Needed",

    "report_title":   "ATS RESUME ANALYZER — REPORT",
    "report_file":    "File",
    "report_date":    "Date",
    "report_found":   "Found",
    "report_missing": "Missing",
    "report_yes":     "YES",
    "report_no":      "MISSING",
    "label_email":    "Email",
    "label_phone":    "Phone",
    "label_linkedin": "LinkedIn",
    "label_location": "Location",

    "hdr_overall":   "OVERALL SCORE",
    "hdr_grade":     "GRADE",
    "hdr_found":     "KEYWORDS FOUND",
    "hdr_contact":   "CONTACT INFO",
    "hdr_recs":      "RECOMMENDATIONS",
    "hdr_warnings":  "WARNINGS",
    "hdr_tips":      "TIPS",
    "hdr_breakdown": "KEYWORD BREAKDOWN",
    "hdr_end":       "END OF REPORT — Generated by Workblox",

    "priority_high":   "HIGH",
    "priority_medium": "MEDIUM",
    "priority_low":    "LOW",

    "job_role_generic":  "job",
}


# Role identifiers double as English display text.
ROLE_LABELS = {key: key for key in JOB_KEYWORDS}
