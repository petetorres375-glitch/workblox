"""Deterministic spreadsheet cleanup.

Every number this module reports -- dates fixed, rows merged, rows flagged --
is counted from work it actually did, never estimated and never produced by a
model. The AI's only role in the Data Cleanup tool is classifying what each
column *means* (see routes/biz_tools.py::_DATA_COLUMN_PLAN_PROMPT); once that
plan exists, or when it can't be obtained and the heuristics below fill in,
the transformation itself is pure Python. That split is what makes the
summary line ("Fixed 14 date formats...") safe to show a client.
"""
import re
from datetime import date, datetime

# Values that mean "blank" in a spreadsheet a human filled in by hand. "none"
# is deliberately NOT here -- it's a plausible real value in a category or
# status column, and silently blanking it would be data loss.
EMPTY_VALUES = {"", "n/a", "na", "-", "--", "null", "nil", "#n/a", "#null!"}

FLAG_AMBIGUOUS_DATE = "ambiguous_date"
FLAG_UNPARSEABLE_DATE = "unparseable_date"
FLAG_DUPLICATE = "duplicate"

MAX_PREVIEW_ROWS = 20

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

_ISO_RE = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$")
_NUM_RE = re.compile(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2}|\d{4})$")
_TEXT_MD_RE = re.compile(r"^([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})$")
_TEXT_DM_RE = re.compile(r"^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})$")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_PHONE_RE = re.compile(r"^[+(]?[\d][\d\s().-]{6,}$")
_NUMBER_RE = re.compile(r"^-?[$€£]?\s?-?[\d,]+(\.\d+)?%?$")


# ── Cell-level normalization ──────────────────────────────────────────────────

def normalize_cell(value) -> str:
    """Trim, collapse internal whitespace runs, and reduce placeholder junk to
    a real blank. Returns a string for everything -- a spreadsheet cell has no
    stable type across .csv and .xlsx, so the engine works in text throughout."""
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return _to_iso(value)
    text = str(value)
    text = " ".join(text.split())
    if text.lower() in EMPTY_VALUES:
        return ""
    return text


def _to_iso(value) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


# ── Date parsing ──────────────────────────────────────────────────────────────

def parse_date(text: str):
    """Classify one cell as a date.

    Returns one of:
      ("exact", date)              -- order is unambiguous on its own
      ("ordered", (a, b, year))    -- numeric, needs a column-wide M/D vs D/M ruling
      None                         -- not a date at all
    """
    if not text:
        return None

    m = _ISO_RE.match(text)
    if m:
        year, month, day = (int(g) for g in m.groups())
        built = _safe_date(year, month, day)
        return ("exact", built) if built else None

    m = _TEXT_MD_RE.match(text)
    if m:
        month = _MONTHS.get(m.group(1).lower())
        if month:
            built = _safe_date(int(m.group(3)), month, int(m.group(2)))
            if built:
                return ("exact", built)

    m = _TEXT_DM_RE.match(text)
    if m:
        month = _MONTHS.get(m.group(2).lower())
        if month:
            built = _safe_date(int(m.group(3)), month, int(m.group(1)))
            if built:
                return ("exact", built)

    m = _NUM_RE.match(text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        year = _expand_year(m.group(3))
        if a == 0 or b == 0 or a > 31 or b > 31:
            return None
        return ("ordered", (a, b, year))

    return None


def _expand_year(raw: str) -> int:
    year = int(raw)
    if len(raw) == 4:
        return year
    # Two-digit years: the same pivot Excel uses, so a spreadsheet round-trips
    # to the century the author meant rather than flipping 99 to 2099.
    return 2000 + year if year < 30 else 1900 + year


def _safe_date(year: int, month: int, day: int):
    try:
        return date(year, month, day)
    except ValueError:
        return None


def resolve_date_order(values, mode: str = "auto") -> str:
    """Decide whether a column's ambiguous numeric dates are M/D/Y or D/M/Y.

    "mdy"/"dmy" force the ruling. "auto" reads it off the column itself: a
    single value with a component above 12 settles the whole column (04/25/2024
    can only be M/D). If nothing in the column disambiguates, we return
    "unknown" rather than guessing -- those rows get flagged for the user
    instead of being silently reinterpreted, which is the one outcome that
    could quietly corrupt a client's records.
    """
    if mode in ("mdy", "dmy"):
        return mode

    saw_mdy = saw_dmy = False
    for raw in values:
        parsed = parse_date(raw)
        if not parsed or parsed[0] != "ordered":
            continue
        a, b, _ = parsed[1]
        if a > 12 and b <= 12:
            saw_dmy = True
        elif b > 12 and a <= 12:
            saw_mdy = True

    if saw_mdy and not saw_dmy:
        return "mdy"
    if saw_dmy and not saw_mdy:
        return "dmy"
    # Either no evidence at all, or the column contradicts itself (some rows
    # only make sense as M/D, others only as D/M) -- both are undecidable.
    return "unknown"


def apply_date_order(parsed, order: str):
    """Turn a parse_date() result into a real date given a column-wide order.
    Returns (date|None, ambiguous: bool)."""
    kind, payload = parsed
    if kind == "exact":
        return payload, False

    a, b, year = payload
    if a > 12 and b <= 12:
        return _safe_date(year, b, a), False
    if b > 12 and a <= 12:
        return _safe_date(year, a, b), False

    # Genuinely ambiguous on its own -- both readings are valid dates.
    if order == "mdy":
        return _safe_date(year, a, b), False
    if order == "dmy":
        return _safe_date(year, b, a), False
    return None, True


# ── Column typing ─────────────────────────────────────────────────────────────

def detect_column_types(headers, rows) -> dict:
    """Heuristic fallback for when no AI column plan is available. Samples each
    column and picks the type that the majority of its non-blank values match."""
    types = {}
    for index, header in enumerate(headers):
        sample = [normalize_cell(r[index]) for r in rows[:200] if index < len(r)]
        sample = [v for v in sample if v]
        types[header] = _type_of_sample(sample) if sample else "text"
    return types


def _is_phone(value: str) -> bool:
    return bool(_PHONE_RE.match(value)) and len(re.sub(r"\D", "", value)) >= 7


# Checked most-specific first rather than by picking the highest score. These
# patterns genuinely overlap -- "2024-03-05" satisfies the phone pattern as
# readily as the date one -- so an argmax over independent scores silently
# types date columns as phone, which then suppresses date normalization AND
# drags the column into the dedupe identity key. Order is what resolves it.
_TYPE_TESTS = (
    ("email", lambda v: bool(_EMAIL_RE.match(v))),
    ("date", lambda v: parse_date(v) is not None),
    ("phone", _is_phone),
    ("number", lambda v: bool(_NUMBER_RE.match(v))),
)


def _type_of_sample(sample) -> str:
    total = len(sample)
    for name, matches in _TYPE_TESTS:
        # A strict majority, not a plurality -- a "notes" column with a few
        # dates scattered through it stays text. Majority rather than a higher
        # bar because real columns carry bad rows: a 20-row date column with 4
        # typos is still a date column, and refusing to treat it as one would
        # leave exactly the mess this tool exists to clean.
        if sum(1 for v in sample if matches(v)) > total * 0.5:
            return name
    return "text"


_IDENTITY_TYPES = ("email", "phone")
_IDENTITY_HEADER_HINTS = ("name", "email", "phone", "id", "customer", "client", "company", "account")


def infer_identity_columns(headers, types) -> list:
    """Which columns decide whether two rows are the same record. Prefers
    genuinely identifying types, then header names that read like identifiers,
    and falls back to every column -- which makes dedupe strictly safer, since
    more columns in the key means fewer rows qualify as duplicates."""
    identity = [h for h in headers if types.get(h) in _IDENTITY_TYPES]
    if identity:
        return identity
    identity = [h for h in headers if any(hint in h.lower() for hint in _IDENTITY_HEADER_HINTS)]
    return identity or list(headers)


# ── The engine ────────────────────────────────────────────────────────────────

class _Row:
    __slots__ = ("original", "values", "flags", "changed", "merged_count")

    def __init__(self, original, values):
        self.original = original
        self.values = values
        self.flags = []
        self.changed = set()
        self.merged_count = 0

    def flag(self, name):
        if name not in self.flags:
            self.flags.append(name)


def clean_table(headers, rows, date_format="auto", duplicate_handling="flag", column_plan=None):
    """Clean a parsed table. Pure and deterministic -- no network, no clock,
    no randomness, so the same input always produces the same counts."""
    headers = list(headers)
    width = len(headers)
    records = []
    cells_trimmed = 0

    for raw in rows:
        padded = list(raw[:width]) + [""] * max(0, width - len(raw))
        original = ["" if v is None else (_to_iso(v) if isinstance(v, (datetime, date)) else str(v)) for v in padded]
        values = [normalize_cell(v) for v in padded]
        record = _Row(original, values)
        for i in range(width):
            if values[i] != original[i]:
                cells_trimmed += 1
                record.changed.add(i)
        records.append(record)

    types = dict((column_plan or {}).get("types") or {})
    for header in headers:
        if header not in types:
            types[header] = None
    if any(v is None for v in types.values()):
        heuristic = detect_column_types(headers, [r.values for r in records])
        for header, value in types.items():
            if value is None:
                types[header] = heuristic[header]

    dates_fixed = _normalize_date_columns(headers, records, types, date_format)

    identity = (column_plan or {}).get("identity") or infer_identity_columns(headers, types)
    identity = [h for h in identity if h in headers] or list(headers)
    kept, duplicates_merged = _handle_duplicates(headers, records, identity, duplicate_handling)

    rows_flagged = sum(1 for r in kept if r.flags)
    return {
        "headers": headers,
        "column_types": types,
        "identity_columns": identity,
        "rows": [r.values for r in kept],
        "row_meta": [
            {"flags": r.flags, "changed": sorted(r.changed), "merged_count": r.merged_count}
            for r in kept
        ],
        "preview": [
            {
                "before": r.original,
                "after": r.values,
                "flags": r.flags,
                "changed": sorted(r.changed),
                "merged_count": r.merged_count,
            }
            for r in kept[:MAX_PREVIEW_ROWS]
        ],
        "total_rows_in": len(records),
        "total_rows_out": len(kept),
        "counts": {
            "dates_fixed": dates_fixed,
            "duplicates_merged": duplicates_merged,
            "rows_flagged": rows_flagged,
            "cells_trimmed": cells_trimmed,
        },
    }


def _normalize_date_columns(headers, records, types, date_format) -> int:
    dates_fixed = 0
    for index, header in enumerate(headers):
        if types.get(header) != "date":
            continue
        column = [r.values[index] for r in records]
        order = resolve_date_order(column, date_format)

        for record in records:
            raw = record.values[index]
            if not raw:
                continue
            parsed = parse_date(raw)
            if parsed is None:
                record.flag(FLAG_UNPARSEABLE_DATE)
                continue
            resolved, ambiguous = apply_date_order(parsed, order)
            if ambiguous or resolved is None:
                record.flag(FLAG_AMBIGUOUS_DATE)
                continue
            iso = resolved.isoformat()
            if iso != raw:
                record.values[index] = iso
                record.changed.add(index)
                dates_fixed += 1
    return dates_fixed


def _identity_key(record, headers, identity):
    positions = [headers.index(h) for h in identity]
    return tuple(_comparable(record.values[p]) for p in positions)


def _comparable(value: str) -> str:
    """Normalization used ONLY for deciding sameness -- never written back to
    the user's data."""
    text = " ".join(value.split()).lower()
    if _PHONE_RE.match(value or ""):
        digits = re.sub(r"\D", "", text)
        if digits:
            return digits
    return text


def _handle_duplicates(headers, records, identity, mode):
    groups = {}
    for record in records:
        key = _identity_key(record, headers, identity)
        groups.setdefault(key, []).append(record)

    merged = 0
    dropped = set()

    for key, group in groups.items():
        if len(group) < 2:
            continue
        # An all-blank identity isn't evidence that two rows are the same
        # record -- it's evidence we have nothing to compare them on.
        if all(part == "" for part in key):
            continue

        if mode == "merge":
            keeper = group[0]
            for other in group[1:]:
                for i in range(len(headers)):
                    # Strictly additive: a blank in the keeper can be filled
                    # from a later duplicate, but a value never overwrites a
                    # value. Nothing the client typed is lost to a merge.
                    if not keeper.values[i] and other.values[i]:
                        keeper.values[i] = other.values[i]
                        keeper.changed.add(i)
                    if other.flags:
                        for flag in other.flags:
                            keeper.flag(flag)
                dropped.add(id(other))
                merged += 1
                keeper.merged_count += 1
        else:
            for record in group:
                record.flag(FLAG_DUPLICATE)

    kept = [r for r in records if id(r) not in dropped]
    return kept, merged
