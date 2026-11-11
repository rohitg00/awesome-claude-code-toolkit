"""Shared field normalization. The correctness of every dedup key lives here.

Pure functions, dependency-light. `phonenumbers` is used when available with a
digit-extraction fallback so the module imports cleanly without it.
"""
from __future__ import annotations

import datetime as _dt
import re

try:  # optional, but in install deps
    import phonenumbers  # type: ignore
    _HAVE_PHONENUMBERS = True
except Exception:  # pragma: no cover
    _HAVE_PHONENUMBERS = False

from .config import DEFAULT_PHONE_REGION

# --- US states ---------------------------------------------------------------
_US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
    "south carolina": "SC", "south dakota": "SD", "tennessee": "TN", "texas": "TX",
    "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC", "puerto rico": "PR",
}
_VALID_STATE_CODES = set(_US_STATES.values())

# Legal suffixes / noise words stripped from org names for matching.
_ORG_SUFFIXES = {
    "inc", "incorporated", "llc", "l.l.c", "ltd", "limited", "co", "corp",
    "corporation", "company", "lp", "llp", "pllc", "pc", "the", "and", "&",
    "group", "holdings", "enterprises", "services", "service",
}
_NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
_NAME_TITLES = {"mr", "mrs", "ms", "dr", "miss", "prof"}

_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


# --- IDs ---------------------------------------------------------------------
def strip_float_id(value) -> str:
    """`'696372.0'` -> `'696372'`; leaves non-numeric strings untouched."""
    s = _clean(value)
    if not s:
        return ""
    if re.fullmatch(r"-?\d+\.0+", s):
        return s.split(".")[0]
    # Handle floats like '76177.0' parsed as float by readers
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
    except (ValueError, OverflowError):
        pass
    return s


# --- Email -------------------------------------------------------------------
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def normalize_email(value) -> str | None:
    s = _clean(value).lower().replace("mailto:", "")
    if not s:
        return None
    m = _EMAIL_RE.search(s)
    return m.group(0) if m else None


def is_valid_email(value) -> bool:
    return normalize_email(value) is not None


# --- Phone -------------------------------------------------------------------
def normalize_phone(value, region: str = DEFAULT_PHONE_REGION) -> str | None:
    """Return E.164 (e.g. '+18178478822') or None if not enough digits."""
    s = _clean(value)
    if not s:
        return None
    if _HAVE_PHONENUMBERS:
        try:
            num = phonenumbers.parse(s, region)
            if phonenumbers.is_valid_number(num):
                return phonenumbers.format_number(
                    num, phonenumbers.PhoneNumberFormat.E164
                )
        except Exception:
            pass
    digits = re.sub(r"\D", "", s)
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return None


# --- ZIP ---------------------------------------------------------------------
def normalize_zip(value) -> str | None:
    """Zero-pad to 5 (repairing lost leading zeros) and keep ZIP+4 if present."""
    s = strip_float_id(value)
    if not s:
        return None
    m = re.match(r"(\d{1,5})(?:-?(\d{4}))?", s)
    if not m:
        return None
    base = m.group(1).zfill(5)
    return f"{base}-{m.group(2)}" if m.group(2) else base


# --- State -------------------------------------------------------------------
def normalize_state(value) -> str | None:
    s = _clean(value)
    if not s:
        return None
    up = s.upper()
    if up in _VALID_STATE_CODES:
        return up
    return _US_STATES.get(s.lower())


# --- Dates -------------------------------------------------------------------
_EXCEL_EPOCH = _dt.datetime(1899, 12, 30)


def excel_serial_to_date(value) -> str | None:
    """Excel serial number -> ISO date string ('YYYY-MM-DD')."""
    s = _clean(value)
    if not s:
        return None
    try:
        serial = float(s)
    except ValueError:
        return None
    try:
        return (_EXCEL_EPOCH + _dt.timedelta(days=serial)).date().isoformat()
    except (OverflowError, ValueError):
        return None


def normalize_date(value) -> str | None:
    """Best-effort date parse to ISO. Handles MM/DD/YYYY and Excel serials."""
    s = _clean(value)
    if not s:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%m-%d-%Y"):
        try:
            return _dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    if re.fullmatch(r"\d+(\.\d+)?", s):  # looks like an Excel serial
        return excel_serial_to_date(s)
    return None


# --- Names -------------------------------------------------------------------
def parse_name(full) -> tuple[str | None, str | None]:
    """Split a combined name into (first, last). Drops titles/suffixes."""
    s = _clean(full)
    if not s:
        return None, None
    if "," in s:  # "Last, First"
        last, _, first = s.partition(",")
        return _clean(first) or None, _clean(last) or None
    parts = [p for p in s.split() if p.strip(".").lower() not in _NAME_TITLES]
    parts = [p for p in parts if p.strip(".").lower() not in _NAME_SUFFIXES]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


def name_norm(first: str | None, last: str | None, full: str | None = None) -> str:
    base = " ".join(x for x in (first, last) if x) or _clean(full)
    base = base.lower()
    base = _PUNCT_RE.sub(" ", base)
    tokens = [t for t in base.split() if t not in _NAME_SUFFIXES and t not in _NAME_TITLES]
    return _WS_RE.sub(" ", " ".join(tokens)).strip()


# --- Organizations -----------------------------------------------------------
def block_key(first: str | None, last: str | None, nrm: str | None = None) -> str | None:
    """Indexed dedup blocking key: normalized last name + first initial
    (e.g. 'vaden|e'). Selective enough to keep candidate sets tiny — avoiding
    the O(n^2) cost of comparing every shared-surname pair — while still
    blocking the same person together. Distinct first names (John vs Jane
    Smith) intentionally fall in different blocks."""
    last_c = _PUNCT_RE.sub("", _clean(last).lower()).strip()
    first_c = _PUNCT_RE.sub("", _clean(first).lower()).strip()
    if not last_c and nrm:
        toks = nrm.split()
        if toks:
            last_c = toks[-1]
            if not first_c and len(toks) > 1:
                first_c = toks[0]
    if not last_c:
        return None
    return f"{last_c}|{first_c[:1]}" if first_c else last_c


def org_name_norm(name) -> str:
    s = _clean(name).lower()
    s = _PUNCT_RE.sub(" ", s)
    tokens = [t for t in s.split() if t not in _ORG_SUFFIXES]
    return _WS_RE.sub(" ", " ".join(tokens)).strip()


def addr_norm(line1, city, state, zip_) -> str:
    parts = [_clean(line1), _clean(city), _clean(state), _clean(zip_)]
    s = " ".join(p for p in parts if p).lower()
    s = _PUNCT_RE.sub(" ", s)
    return _WS_RE.sub(" ", s).strip()
