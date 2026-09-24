from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import has_request_context, request


def local_now() -> datetime:
    """The current time in the caller's time zone, for timestamps printed on
    reports. Both apps send the browser's IANA zone (e.g. "America/New_York")
    as X-Timezone; the server clock is UTC, so without it a report made at
    7:37 PM in New York would say 23:37. Falls back to UTC when the header is
    missing (an older cached app) or not a real zone name."""
    name = request.headers.get("X-Timezone", "").strip() if has_request_context() else ""
    try:
        tz = ZoneInfo(name) if name else timezone.utc
    except (ZoneInfoNotFoundError, ValueError):
        tz = timezone.utc
    return datetime.now(tz)
