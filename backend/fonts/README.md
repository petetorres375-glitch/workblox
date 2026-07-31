# PDF fonts

These ship with the app because Railway's build image has no usable font set and
every Workblox PDF has to render all 24 supported UI languages. They are loaded
by `app/services/pdf_fonts.py` — add or swap fonts there, not in individual
generators.

| File | Scripts | Licence |
| --- | --- | --- |
| `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf` | Latin, Cyrillic, Greek, Hebrew, Arabic, Vietnamese | Bitstream Vera / Public Domain |
| `DroidSansFallbackFull.ttf` | Chinese (Simplified + Traditional), Japanese kana and kanji | Apache 2.0 |
| `NotoSansKR-Regular.ttf` | Korean / Hangul | SIL Open Font License 1.1 |
| `NotoSansDevanagari-Regular.ttf`, `-Bold.ttf` | Hindi | SIL Open Font License 1.1 |
| `NotoSansThai-Regular.ttf`, `-Bold.ttf` | Thai | SIL Open Font License 1.1 |

## Every font here must be TrueType

fpdf2 renders CFF / CID-keyed OpenType as **blank glyphs, with no error and no
warning** — the PDF generates "successfully" and the text is simply invisible.
The official Noto Sans CJK release (`.otf` and `.ttc`) is CID-keyed CFF and is
therefore unusable here, which is why Chinese/Japanese come from Droid Sans
Fallback and Korean from a static TrueType instance of Noto Sans KR rather than
from one Noto CJK file.

Before adding a font, check it has TrueType outlines:

```python
from fontTools.ttLib import TTFont
print("glyf" in TTFont("YourFont.ttf"))  # must be True
```

Then render a sample and *look at it* — a successful `pdf.output()` proves
nothing.

## Korean font provenance

`NotoSansKR-Regular.ttf` is a static instance (`wght=400`) of the upstream
variable font, produced with:

```python
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
f = TTFont("NotoSansKR-VF.ttf")  # googlefonts/noto-cjk, Sans/Variable/TTF/Subset
instancer.instantiateVariableFont(f, {"wght": 400}, inplace=False).save("NotoSansKR-Regular.ttf")
```

Only regular weights are shipped for the fallback scripts. `set_fallback_fonts`
is configured with `exact_match=False`, so a bold run falls back to the regular
face rather than losing the glyph — a real glyph at the wrong weight beats tofu.
