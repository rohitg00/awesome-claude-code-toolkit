"""Shared, dependency-light field normalization.

Pure functions. Keeps the dashboard, importer and repository agreeing on what a
phone / money / date / contract-number / scope value *is*.
"""
from __future__ import annotations

import datetime as _dt
import re

_WS_RE = re.compile(r"\s+")


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


def norm_key(value) -> str:
    """Lowercase, punctuation-light key used to dedup names / contract numbers."""
    s = _WS_RE.sub(" ", re.sub(r"[^\w\s]", " ", _clean(value).lower())).strip()
    return s


def contract_no_norm(value) -> str:
    """Normalize a contract / RFP number for matching: upper, alnum-collapsed."""
    s = _clean(value).upper()
    return re.sub(r"[^A-Z0-9]", "", s)


def normalize_phone(value) -> str | None:
    """Return E.164-ish ('+1XXXXXXXXXX') for US numbers, else None."""
    s = _clean(value)
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return None


def normalize_website(value) -> str | None:
    s = _clean(value)
    if not s:
        return None
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    return s


def normalize_money(value) -> float | None:
    """'$1,250,000.00' / '1.25M' / 1250000 -> float, or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = _clean(value).replace(",", "").replace("$", "").strip()
    if not s:
        return None
    mult = 1.0
    if s[-1:].lower() == "k":
        mult, s = 1_000.0, s[:-1]
    elif s[-1:].lower() == "m":
        mult, s = 1_000_000.0, s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def normalize_float(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = _clean(value).replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


# Yearless formats are deliberately excluded: "%m/%d" would silently parse
# "12/31" to a year-1900 date and mis-sort the contract as long-expired.
_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%b %d, %Y",
                 "%B %d, %Y", "%Y/%m/%d")


def normalize_date(value) -> str | None:
    """Return ISO yyyy-mm-dd, or None if unparseable."""
    s = _clean(value)
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return _dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    # already ISO-ish?
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    return None


def truthy(value) -> bool:
    return _clean(value).lower() in {"1", "true", "yes", "y", "executed", "signed", "t"}
