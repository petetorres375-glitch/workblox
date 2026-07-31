import io
from unittest.mock import patch

import pytest

from app.services.ats_corpora import check_parity, detect_language
from app.services.ats_engine import analyze

# Prose English, the easy case.
EN_PROSE = """John Smith | john@example.com
SUMMARY
Results-oriented professional with a strong background in customer service and
team leadership. Committed to delivering quality work in a fast-paced setting.
WORK EXPERIENCE
Senior Engineer, Acme Corp, 2022 to 2026
- Managed a team of five engineers and improved performance by 40 percent
- Developed and implemented cloud systems used by the whole organization
EDUCATION
BS Computer Science, State University, 2020
SKILLS
Microsoft Office, Excel, communication, leadership, problem solving
"""

# Terse and keyword-stuffed. Barely any function words, so a check that keys off
# "does this look English?" wrongly rejects it -- and this is exactly the kind of
# resume an ATS tool gets fed.
EN_TERSE = """JANE DOE
jane@example.com | 555-0100 | New York
SKILLS
Python, JavaScript, React, Node, AWS, Docker, Kubernetes, SQL, Git, Linux
EXPERIENCE
Acme Corp - Senior Developer 2022-2026
Built microservices. Led migration. Improved latency 40%.
Globex - Developer 2019-2022
Shipped features. Mentored juniors. Automated deploys.
EDUCATION
BS Computer Science, State University 2019
CERTIFICATIONS
AWS Solutions Architect, Scrum Master, Certified Kubernetes Administrator
"""

# English resume carrying Spanish proper nouns -- "de", "la", "Casa de Oro".
EN_WITH_SPANISH_NAMES = """Maria de la Cruz | maria@example.com | Los Angeles, CA
SUMMARY
Bilingual customer service professional with experience in retail and hospitality.
WORK EXPERIENCE
Server, Casa de Oro Restaurant, 2021 to 2026
- Managed high-volume dining service and trained new staff on the point of sale
- Improved guest satisfaction scores by 25 percent
EDUCATION
AA Business, Santa Monica College, 2021
SKILLS
Customer service, cash handling, teamwork, communication, Spanish, English
"""

SPANISH = """Juan Perez | juan@ejemplo.com
RESUMEN
Profesional orientado a resultados con amplia experiencia en el servicio al cliente
y en el liderazgo de equipos. Comprometido con la entrega de trabajo de calidad.
EXPERIENCIA LABORAL
Ingeniero Senior, Acme Corp, de 2022 a 2026
- Dirigio un equipo de cinco ingenieros y mejoro el rendimiento en un 40 por ciento
- Desarrollo e implemento los sistemas en la nube para toda la organizacion
EDUCACION
Licenciatura en Informatica, Universidad Estatal, 2020
"""

ARABIC = """جون سميث | john@example.com
الملخص
محترف موجه نحو النتائج يتمتع بمهارات تواصل وعمل جماعي قوية وخبرة واسعة في المجال.
الخبرة العملية
مهندس أول، شركة أكمي 2022-2026
- قاد فريقًا من خمسة مهندسين وحسّن الأداء بنسبة 40%
التعليم
بكالوريوس علوم الحاسوب، جامعة الولاية، 2020
"""

CHINESE = """张伟 | zhang@example.com
个人简介
以结果为导向的专业人士，拥有丰富的客户服务和团队领导经验，善于沟通协作。
工作经历
高级工程师，Acme Corp，2022年至2026年
- 领导五人工程团队，将性能提升了百分之四十
教育背景
计算机科学学士，国立大学，2020年
"""


@pytest.fixture(autouse=True)
def _bypass_tool_entitlement():
    # TESTING mode skips auth, so g.user is never set and require_tool() would
    # blow up reading it. These tests are about language handling, not access.
    with patch("app.routes.ats_analyzer.require_tool", return_value=None), \
         patch("app.routes.ats_analyzer.require_personal", return_value=None):
        yield


@pytest.mark.parametrize("label,text", [
    ("prose", EN_PROSE),
    ("terse", EN_TERSE),
    ("spanish proper nouns", EN_WITH_SPANISH_NAMES),
])
def test_english_resumes_are_detected_as_english(label, text):
    language, reason = detect_language(text)
    assert language == "en", f"{label} English resume detected as {language} ({reason})"
    assert reason is None


def test_spanish_resume_is_now_scored_not_refused():
    # Spanish has a corpus, so it is scored rather than declined.
    language, reason = detect_language(SPANISH)
    assert language == "es"
    assert reason is None


@pytest.mark.parametrize("label,text,expected", [
    ("arabic", ARABIC, "non_latin_script"),
    ("chinese", CHINESE, "non_latin_script"),
])
def test_resumes_without_a_corpus_are_refused(label, text, expected):
    language, reason = detect_language(text)
    assert language is None, f"{label} resume should not be scored"
    assert reason == expected


def test_short_text_is_not_rejected():
    # Too sparse to judge — score it rather than guess. A false refusal costs a
    # real user a real score.
    language, reason = detect_language("John Smith\njohn@example.com\nDeveloper")
    assert language == "en"
    assert reason is None


def test_corpora_stay_in_parity_with_english():
    # Category and section keys are looked up by name while scoring, so a
    # translated key silently breaks rules rather than translating them.
    assert check_parity() == []


def _upload(client, payload):
    return client.post(
        "/api/ats",
        data={"resume": (io.BytesIO(payload.encode()), "resume.txt")},
        content_type="multipart/form-data",
    )


def test_route_scores_english_resume(client):
    rv = _upload(client, EN_PROSE)
    assert rv.status_code == 200
    assert "score" in rv.get_json()["results"]


def test_route_refuses_arabic_resume_instead_of_scoring_zero(client):
    rv = _upload(client, ARABIC)
    assert rv.status_code == 422
    body = rv.get_json()
    assert body["code"] == "non_latin_script"
    # The whole point: no misleading 0/100 in the payload.
    assert "results" not in body


def test_route_scores_spanish_resume_in_spanish(client):
    rv = _upload(client, SPANISH)
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["language"] == "es"
    # The whole point of the corpus: a real score, not the 0 it used to give.
    assert body["results"]["score"] > 0
    assert body["results"]["categories"]["Soft Skills"]["label"] == "Habilidades blandas"


def test_spanish_recommendations_are_in_spanish(client):
    rv = _upload(client, SPANISH)
    recs = rv.get_json()["results"]["recommendations"]
    assert recs, "expected recommendations for this resume"
    joined = " ".join(r["title"] + r["detail"] for r in recs)
    assert "Agrega" in joined or "Considera" in joined or "Completa" in joined
    # No English leaking into a Spanish report.
    assert "Add " not in joined and "Consider adding" not in joined


def test_spanish_verb_stems_match_conjugations():
    # "Gestioné" / "mejoré" must count as the verbs gestionar / mejorar.
    text = SPANISH + "\nGestioné, mejoré y desarrollé procesos internos."
    results = analyze(text, language="es")
    found = results["categories"]["Action Verbs"]["found"]
    assert "gestionar" in found
    assert "mejorar" in found
    assert "desarrollar" in found
