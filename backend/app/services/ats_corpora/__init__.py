"""Per-language ATS corpora.

The scoring engine matches a CV against a corpus of keywords. Those keywords
are language-specific, so a corpus exists per supported language and English
is the reference: every other corpus must define the same category keys,
section keys and role keys, or scoring silently diverges between languages.

Adding a language:
  1. Copy en.py, translate the values -- never the dict keys.
  2. Register it in CORPORA below.
  3. Add its function words to _LANGUAGE_MARKERS so detection can find it.
  4. test_ats_corpora.py enforces parity with English automatically.
"""

import re
import unicodedata

from . import en, es

CORPORA = {
    "en": en,
    "es": es,
}

REFERENCE = "en"


def fold(text):
    """Lowercase and strip accents, so 'Gestión' == 'gestion'.

    Applied to both the CV text and the keywords, which lets a corpus be
    written with correct accents while still matching CVs that drop them --
    common in practice, and near-universal in plain-text exports.
    """
    lowered = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in lowered if not unicodedata.combining(c))


def get_corpus(language):
    return CORPORA.get(language) or CORPORA[REFERENCE]


def supported_languages():
    return sorted(CORPORA)


# Function words used to identify which language a CV is written in. Tokens
# that are also ordinary English resume words (a, in, is, on, at, as, or, do,
# no, os, van) are left out -- a collision costs a real user a real score.
_LANGUAGE_MARKERS = {
    "en": """
        and the of with for to an by from are was were been
        my our their his her its this that these those not all any each
    """,
    "es": """
        el los las del con para por una que su y en se mas como
        tambien desde hasta sobre entre durante fue son
    """,
    # Not supported for scoring, but recognised so we can decline clearly
    # instead of scoring a Portuguese CV against the Spanish corpus.
    "pt": "nao sao dos das pelo pela uma nos nas ele ela mais quando",
    "fr": "les des le du dans sur au aux et une leur ses nos vos",
    "de": "und der die das den von mit fur im ein eine bei auch ist",
    "it": "il della degli nel gli di per una che sono anche",
    "nl": "het een van voor met op dat te zijn naar",
}

_MARKERS = {lang: frozenset(words.split()) for lang, words in _LANGUAGE_MARKERS.items()}

_MIN_WORDS_FOR_LANGUAGE_CHECK = 40
_MAX_NON_LATIN_LETTER_RATIO = 0.20
_MIN_MARKER_RATIO = 0.06
_DOMINANCE_RATIO = 2.0


def detect_language(text):
    """Identify the CV's language.

    Returns (language, reason). `language` is a key of CORPORA when the CV can
    be scored, otherwise None and `reason` explains why:
      "non_latin_script" -- a script we have no corpus for at all
      "unsupported_language" -- recognisably another Latin-script language

    Biased towards scoring. English is the default whenever the evidence is
    weak, because refusing to score a real CV is worse than scoring a slightly
    unusual one -- a terse, keyword-stuffed CV has almost no function words in
    any language.
    """
    letters = [c for c in text if c.isalpha()]
    if letters:
        non_latin = sum(1 for c in letters if ord(c) > 0x24F)
        if non_latin / len(letters) > _MAX_NON_LATIN_LETTER_RATIO:
            return None, "non_latin_script"

    words = re.findall(r"[a-z']+", fold(text))
    if len(words) < _MIN_WORDS_FOR_LANGUAGE_CHECK:
        return REFERENCE, None

    counts = {lang: sum(1 for w in words if w in marks) for lang, marks in _MARKERS.items()}
    best = max(counts, key=counts.get)
    best_count = counts[best]
    runner_up = max((c for lang, c in counts.items() if lang != best), default=0)

    weak = best_count / len(words) < _MIN_MARKER_RATIO
    unclear = best_count < runner_up * _DOMINANCE_RATIO
    if weak or unclear:
        return REFERENCE, None

    if best in CORPORA:
        return best, None
    return None, "unsupported_language"


_REQUIRED = ("KEYWORDS", "JOB_KEYWORDS", "SECTION_PATTERNS", "SECTION_LABELS",
             "CATEGORY_LABELS", "ROLE_SUMMARIES", "GENERIC_SUMMARY",
             "METRIC_PATTERNS", "LOCATION_PATTERN", "MESSAGES", "ROLE_LABELS")


def check_parity():
    """Return a list of ways each corpus deviates from the English reference.

    Keys are load-bearing: build_recommendations() looks up cats["Soft Skills"]
    and sections["Skills"] by name, so a translated key means a KeyError or a
    silently skipped rule rather than a translated report.
    """
    ref = CORPORA[REFERENCE]
    problems = []
    for lang, mod in CORPORA.items():
        if lang == REFERENCE:
            continue
        for attr in _REQUIRED:
            if not hasattr(mod, attr):
                problems.append(f"{lang}: missing {attr}")
        for attr in ("KEYWORDS", "JOB_KEYWORDS", "SECTION_PATTERNS",
                     "SECTION_LABELS", "CATEGORY_LABELS", "MESSAGES",
                     "ROLE_LABELS"):
            if not hasattr(mod, attr):
                continue
            missing = set(getattr(ref, attr)) - set(getattr(mod, attr))
            extra = set(getattr(mod, attr)) - set(getattr(ref, attr))
            if missing:
                problems.append(f"{lang}.{attr} missing keys: {sorted(missing)}")
            if extra:
                problems.append(f"{lang}.{attr} unknown keys: {sorted(extra)}")
    return problems
