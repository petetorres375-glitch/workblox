import json
from app.services.claude_client import call as claude_call

SYSTEM_PROMPT = """You are a professional resume writer specializing in ATS-optimized resumes.
The user will provide their background information. Your job is to write polished, professional
resume content that passes ATS systems and impresses hiring managers.

Rules:
- Use strong action verbs to start every bullet point
- Include measurable results where the user hints at numbers
- Keep the summary to 3-4 sentences max
- Each experience entry gets 3-5 bullet points
- Skills should be a flat list of individual skills
- Be concise — this is a resume, not a novel
- Match the language and keywords to the target job role
- Never invent facts — only enhance and polish what the user provides

Return ONLY valid JSON in exactly this format, no markdown, no explanation:
{
  "summary": "Professional summary paragraph here.",
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "dates": "Start – End",
      "bullets": [
        "Action verb + achievement + impact",
        "Action verb + responsibility + result"
      ]
    }
  ],
  "education": [
    {
      "degree": "Degree or Diploma",
      "school": "School Name",
      "year": "Year"
    }
  ],
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "certifications": ["Certification 1", "Certification 2"]
}"""


def build_user_message(data):
    lines = [f"Target Job Role: {data.get('job_role', 'Not specified')}"]

    exp = data.get("experience", [])
    if exp:
        lines.append("\nWork Experience:")
        for i, job in enumerate(exp, 1):
            lines.append(f"  {i}. Title: {job.get('title', '')}")
            lines.append(f"     Company: {job.get('company', '')}")
            lines.append(f"     Dates: {job.get('dates', '')}")
            if job.get("duties"):
                lines.append(f"     Duties/Achievements: {job['duties']}")

    edu = data.get("education", [])
    if edu:
        lines.append("\nEducation:")
        for e in edu:
            lines.append(f"  - {e.get('degree', '')} | {e.get('school', '')} | {e.get('year', '')}")

    if data.get("skills"):
        lines.append(f"\nSkills (raw): {data['skills']}")

    if data.get("certifications"):
        lines.append(f"\nCertifications: {data['certifications']}")

    if data.get("extra"):
        lines.append(f"\nAdditional info: {data['extra']}")

    return "\n".join(lines)


def generate_resume(data):
    user_message = build_user_message(data)
    raw = claude_call(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
    )

    if isinstance(raw, dict) and "summary" in raw:
        return raw

    if isinstance(raw, str):
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    raise ValueError("Unexpected response format from Claude")
