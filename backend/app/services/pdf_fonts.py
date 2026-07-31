"""Shared font setup for every Workblox PDF generator.

Workblox ships 24 UI languages, so a PDF may contain any script. Getting that
right needs three things together — miss any one and the output is silently
wrong rather than an error:

1. Embedded TrueType fonts. The PDF core fonts (Helvetica et al.) are Latin-1
   only, so anything outside that range has to be replaced with "?" to avoid a
   crash. Embedding real fonts removes that whole class of damage.

2. HarfBuzz text shaping. Arabic and Hebrew need contextual letter joining and
   right-to-left reordering. Without shaping the glyphs are present but appear
   disconnected and in reverse order — unreadable to a native speaker.

3. Fallback fonts. No single font of a practical size covers Latin + CJK +
   Devanagari + Thai, so DejaVu is the base and the rest fill gaps per glyph.

IMPORTANT: every font registered here must be TrueType (glyf outlines). fpdf2
renders CFF / CID-keyed OpenType — which is what the official Noto Sans CJK
.otf and .ttc files are — as *blank glyphs with no error or warning*. That is
why Korean uses a static TrueType instance of Noto Sans KR and Chinese and
Japanese use Droid Sans Fallback rather than Noto Sans CJK.
"""

import os

FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fonts")

# Base family: Latin, Cyrillic, Greek, Hebrew, Arabic, Vietnamese and the
# Central/Eastern European accents. Covers 19 of the 24 UI languages.
BASE_FONT = "DejaVu"

_BASE_FACES = {
    "":  "DejaVuSans.ttf",
    "B": "DejaVuSans-Bold.ttf",
}

# Gap-fillers, tried in order. Regular weight only — `exact_match=False` on
# set_fallback_fonts lets fpdf2 substitute regular where bold was requested,
# which is what we want: a real glyph beats a correct weight.
_FALLBACK_FACES = {
    "NotoZhJa": "DroidSansFallbackFull.ttf",       # Chinese + Japanese (incl. kana)
    "NotoKo":   "NotoSansKR-Regular.ttf",           # Korean / Hangul
    "NotoDeva": "NotoSansDevanagari-Regular.ttf",   # Hindi
    "NotoThai": "NotoSansThai-Regular.ttf",         # Thai
}

# Arabic and Hebrew blocks, including the Arabic presentation forms.
_RTL_RANGES = (
    (0x0590, 0x05FF),  # Hebrew
    (0x0600, 0x06FF),  # Arabic
    (0x0700, 0x074F),  # Syriac
    (0x0750, 0x077F),  # Arabic Supplement
    (0x08A0, 0x08FF),  # Arabic Extended-A
    (0xFB1D, 0xFDFF),  # Hebrew + Arabic presentation forms A
    (0xFE70, 0xFEFF),  # Arabic presentation forms B
)

RTL_LANGUAGES = frozenset({"ar", "he", "fa", "ur"})


def _path(filename):
    return os.path.abspath(os.path.join(FONTS_DIR, filename))


def register_pdf_fonts(pdf):
    """Register the base family plus script fallbacks and enable shaping.

    Call once, right after the FPDF instance is created and before any
    set_font(). Returns the base family name so callers can pass it straight
    into set_font().
    """
    for style, filename in _BASE_FACES.items():
        pdf.add_font(BASE_FONT, style, _path(filename))

    registered = []
    for family, filename in _FALLBACK_FACES.items():
        path = _path(filename)
        if not os.path.exists(path):
            # A missing fallback should degrade to tofu for one script, not
            # take down every PDF in the product.
            continue
        pdf.add_font(family, "", path)
        registered.append(family)

    if registered:
        pdf.set_fallback_fonts(registered, exact_match=False)

    # Needs uharfbuzz. Without it Latin output is still correct, so a missing
    # optional dep must not break PDF generation outright.
    try:
        pdf.set_text_shaping(True)
    except Exception:  # pragma: no cover - depends on optional native dep
        pass

    return BASE_FONT


def is_rtl(text, language=None):
    """True when the text should be laid out right-to-left.

    Prefers the caller's language code when there is one. Otherwise falls back
    to counting characters, so a mostly-English report that happens to quote an
    Arabic name stays left-aligned.
    """
    if language:
        if language.split("-")[0].lower() in RTL_LANGUAGES:
            return True
        return False

    if not text:
        return False

    rtl = ltr = 0
    for ch in text:
        code = ord(ch)
        if any(lo <= code <= hi for lo, hi in _RTL_RANGES):
            rtl += 1
        elif ch.isalpha():
            ltr += 1
    return rtl > ltr


def align_for(text, language=None):
    """"R" for right-to-left content, "L" otherwise — for cell/multi_cell."""
    return "R" if is_rtl(text, language) else "L"
