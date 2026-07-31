import os
import re
from datetime import datetime

from app.services import ats_corpora
from app.services.ats_corpora import en as _en_corpus
from app.services.ats_corpora import detect_language, fold, get_corpus

# Role identifiers are English in every corpus (they are IDs, not display
# text), so the roles endpoint keeps serving this one list.
JOB_KEYWORDS = _en_corpus.JOB_KEYWORDS








def normalize(text):
    return (text
        .replace('‘', "'").replace('’', "'")
        .replace('“', '"').replace('”', '"')
        .replace('—', '-').replace('–', '-')
    )


# Language handling lives in ats_corpora: it owns the per-language keyword sets
# and therefore knows which languages can actually be scored.


def check_language_support(text):
    """Back-compat shim: True when the CV can be scored in some language."""
    language, reason = detect_language(text)
    return language is not None, reason


def match_keywords(text, keyword_list):
    """Match keywords against the CV, accent-insensitively.

    A keyword entry is either a plain string, or a (display, [forms]) pair for
    languages that inflect. Spanish conjugates heavily, so "gestionar" is
    matched by the stem "gestion" -- catching gestioné / gestionar / gestionado
    / gestión -- while the report still shows the user "gestionar".
    """
    haystack = re.sub(r'\s+', ' ', fold(normalize(text)))
    found, missing = [], []
    for entry in keyword_list:
        if isinstance(entry, (tuple, list)):
            display, forms = entry[0], entry[1]
        else:
            display, forms = entry, [entry]
        if any(fold(normalize(f)) in haystack for f in forms):
            found.append(display)
        else:
            missing.append(display)
    return found, missing


def check_formatting(text, corpus):
    msg = corpus.MESSAGES
    warnings, tips = [], []
    if len(text) < 200:
        warnings.append(msg["warn_short"])
    if not re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text):
        warnings.append(msg["warn_no_email"])
    if not re.search(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
        tips.append(msg["tip_phone"])
    if len(text) > 6000:
        tips.append(msg["tip_too_long"])
    word_count = len(text.split())
    if word_count < 100:
        warnings.append(msg["warn_few_words"].format(count=word_count))
    return warnings, tips


def check_contact_info(text, corpus):
    return {
        "email":    bool(re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)),
        "phone":    bool(re.search(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text)),
        "linkedin": bool(re.search(r'linkedin\.com/in/', text, re.I)),
        "location": bool(re.search(corpus.LOCATION_PATTERN, text)),
    }


def check_quantification(text, corpus):
    examples = []
    for pattern in corpus.METRIC_PATTERNS:
        examples.extend(m.group(0) for m in re.finditer(pattern, text, re.I))
    return {
        "has_metrics":  bool(examples),
        "number_count": len(re.findall(r'\b\d+\b', text)),
        "examples":     examples[:4],
    }


def check_sections(text, corpus):
    folded = re.sub(r'\s+', ' ', fold(text))
    return {name: bool(re.search(pat, folded))
            for name, pat in corpus.SECTION_PATTERNS.items()}


def build_recommendations(results, corpus, job_role=None):
    msg  = corpus.MESSAGES
    recs = []
    cats = results["categories"]

    def add(priority, title_key, detail_key, **fmt):
        recs.append({
            "priority": priority,
            "title":  msg[title_key].format(**fmt),
            "detail": msg[detail_key].format(**fmt),
        })

    if results.get("job_match") and results["job_match"]["missing"]:
        missing = results["job_match"]["missing"]
        tail = msg["rec_role_overflow"].format(count=len(missing) - 6) if len(missing) > 6 else ""
        add("high", "rec_role_title", "rec_role_detail",
            role=(results["job_match"].get("role") or msg["job_role_generic"]),
            keywords=", ".join(missing[:6]) + tail)

    if not results.get("quantification", {}).get("has_metrics"):
        add("high", "rec_metrics_title", "rec_metrics_detail")

    missing_verbs = cats["Action Verbs"]["missing"]
    if len(missing_verbs) > 10:
        add("high", "rec_verbs_strong_title", "rec_verbs_strong_detail",
            keywords=", ".join(missing_verbs[:6]))
    elif len(missing_verbs) > 4:
        add("medium", "rec_verbs_more_title", "rec_verbs_more_detail",
            keywords=", ".join(missing_verbs[:5]))

    missing_tech = cats["Technical Skills"]["missing"]
    if len(missing_tech) > len(cats["Technical Skills"]["found"]):
        add("high", "rec_tech_title", "rec_tech_detail",
            keywords=", ".join(missing_tech[:6]))

    sections = results.get("sections", {})
    if not sections.get("Summary / Objective"):
        add("medium", "rec_summary_title", "rec_summary_detail")
    if not sections.get("Skills"):
        add("medium", "rec_skills_title", "rec_skills_detail")

    contact = results.get("contact", {})
    missing_contact = []
    if not contact.get("linkedin"): missing_contact.append(msg["contact_linkedin"])
    if not contact.get("location"): missing_contact.append(msg["contact_location"])
    if missing_contact:
        add("medium", "rec_contact_title", "rec_contact_detail",
            items=", ".join(missing_contact))

    missing_soft = cats["Soft Skills"]["missing"]
    if len(missing_soft) > 7:
        add("low", "rec_soft_title", "rec_soft_detail",
            keywords=", ".join(missing_soft[:5]))

    order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: order.get(r["priority"], 3))
    return recs


def analyze(resume_text, job_role=None, custom_keywords=None, language=None):
    """Score a CV against the corpus for `language` (default: English)."""
    corpus = get_corpus(language)
    results = {"language": language or ats_corpora.REFERENCE}
    total_found = total_possible = 0

    category_results = {}
    for category, keywords in corpus.KEYWORDS.items():
        found, missing = match_keywords(resume_text, keywords)
        category_results[category] = {
            "found": found, "missing": missing,
            "score": len(found), "total": len(keywords),
            # Key stays the English identifier so scoring rules keep working;
            # the label is what the report shows.
            "label": corpus.CATEGORY_LABELS.get(category, category),
        }
        total_found    += len(found)
        total_possible += len(keywords)
    results["categories"] = category_results

    if job_role:
        role_key = job_role.lower().strip()
        matched  = next((k for k in corpus.JOB_KEYWORDS
                         if k in role_key or role_key in k), None)
        job_kws  = corpus.JOB_KEYWORDS.get(matched) if matched else None
        if job_kws:
            found, missing = match_keywords(resume_text, job_kws)
            results["job_match"] = {
                # Role keys are English identifiers; show the localized name.
                "role": corpus.ROLE_LABELS.get(matched, job_role),
                "found": found, "missing": missing,
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

    warnings, tips = check_formatting(resume_text, corpus)
    results["warnings"]        = warnings
    results["tips"]            = tips
    results["contact"]         = check_contact_info(resume_text, corpus)
    results["quantification"]  = check_quantification(resume_text, corpus)
    results["sections"]        = check_sections(resume_text, corpus)
    results["section_labels"]  = dict(corpus.SECTION_LABELS)

    base_score = int((total_found / total_possible) * 85) if total_possible else 0
    results["score"]          = max(0, min(100, base_score - len(warnings) * 5))
    results["total_found"]    = total_found
    results["total_possible"] = total_possible
    results["recommendations"] = build_recommendations(results, corpus, job_role)

    return results


def grade(score, language=None):
    msg = get_corpus(language).MESSAGES
    if score >= 80: return msg["grade_a"]
    if score >= 65: return msg["grade_b"]
    if score >= 50: return msg["grade_c"]
    if score >= 35: return msg["grade_d"]
    return            msg["grade_f"]


def build_report(results, filename, language=None):
    msg = get_corpus(language or results.get("language")).MESSAGES
    lines = []
    w = 58
    lines += [
        "=" * w,
        f"  {msg['report_title']}",
        f"  {msg['report_file']} : {os.path.basename(filename)}",
        f"  {msg['report_date']} : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * w,
        f"\n  {msg['hdr_overall']} : {results['score']} / 100",
        f"  {msg['hdr_grade']} : {grade(results['score'], results.get('language'))}",
        f"  {msg['hdr_found']}: {results['total_found']} / {results['total_possible']}",
        "",
    ]
    filled = int(results['score'] / 5)
    lines.append(f"  [{'█' * filled}{'░' * (20 - filled)}] {results['score']}%\n")

    c = results.get("contact", {})
    lines += ["=" * w, f"  {msg['hdr_contact']}", "-" * w]
    for label, key in [(msg["label_email"], "email"), (msg["label_phone"], "phone"),
                       (msg["label_linkedin"], "linkedin"), (msg["label_location"], "location")]:
        lines.append(f"  {label:<20}: {msg['report_yes'] if c.get(key) else msg['report_no']}")

    recs = results.get("recommendations", [])
    if recs:
        lines += ["", "=" * w, f"  {msg['hdr_recs']}", "-" * w]
        for i, rec in enumerate(recs, 1):
            prio = msg.get(f"priority_{rec['priority']}", rec['priority'].upper())
            lines += [f"  {i}. [{prio}] {rec['title']}", f"     {rec['detail']}", ""]

    if results["warnings"]:
        lines += ["=" * w, f"  {msg['hdr_warnings']}", "-" * w]
        lines += [f"  !  {m}" for m in results["warnings"]]

    if results["tips"]:
        lines += ["", f"  {msg['hdr_tips']}"]
        lines += [f"  ->  {t}" for t in results["tips"]]

    if results.get("job_match"):
        jm = results["job_match"]
        lines += ["", "=" * w, f"  JOB MATCH: {jm['role'].upper()}", f"  {jm['score']} / {jm['total']} keywords found", "-" * w]
        if jm["found"]:   lines.append(f"  {msg['report_found']}   : " + ", ".join(jm["found"]))
        if jm["missing"]: lines.append(f"  {msg['report_missing']} : " + ", ".join(jm["missing"]))

    lines += ["", "=" * w, f"  {msg['hdr_breakdown']}", "=" * w]
    for cat, data in results["categories"].items():
        cat = data.get("label", cat)
        pct = int((data["score"] / data["total"]) * 100) if data["total"] else 0
        lines += [f"\n  {cat}  ({data['score']}/{data['total']}  {pct}%)", "  " + "-" * (w - 2)]
        if data["found"]:   lines.append(f"  {msg['report_found']}   : " + ", ".join(data["found"]))
        if data["missing"]: lines.append(f"  {msg['report_missing']} : " + ", ".join(data["missing"]))

    lines += ["", "=" * w, f"  {msg['hdr_end']}", "=" * w]
    return "\n".join(lines)


def generate_revised(original_text, results, job_role=None, language=None):
    corpus  = get_corpus(language or results.get('language'))
    lines   = original_text.rstrip().split('\n')
    revised = list(lines)
    changes = []

    if not results.get('sections', {}).get('Summary / Objective'):
        role_key = (job_role or '').lower().strip()
        body = next((v for k, v in corpus.ROLE_SUMMARIES.items()
                     if k in role_key or role_key in k), corpus.GENERIC_SUMMARY)
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
