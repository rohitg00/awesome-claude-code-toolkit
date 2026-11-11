"""JEV candidate grading: source trust + cross-source corroboration.

Weights encode the user's priority (saved contacts / iCloud, public-entity
employee directories, and confirmed LinkedIn highest; generic OSINT lowest).
A value proposed by several independent sources is boosted, capped.
"""
from __future__ import annotations

from .base import Candidate

SOURCE_WEIGHTS = {
    "gcontacts": 0.90, "icloud": 0.90, "publicdata": 0.85,
    "public_directory": 0.85, "linkedin": 0.90, "linkedin_candidate": 0.50,
    "gravatar": 0.60, "libravatar": 0.55, "company_website": 0.60,
    "ghunt": 0.55, "google": 0.45, "holehe": 0.40, "maigret": 0.45,
    "whois": 0.50,
}
DEFAULT_WEIGHT = 0.40
CORROBORATION_BONUS = 0.08
CORROBORATION_CAP = 0.20


def base_grade(source: str) -> float:
    return SOURCE_WEIGHTS.get(source, DEFAULT_WEIGHT)


def _norm(field: str, value: str) -> str:
    v = (value or "").strip().lower()
    if field in ("email", "website", "linkedin", "photo"):
        return v.rstrip("/")
    if field == "phone":
        return "".join(ch for ch in v if ch.isdigit())
    return v


def grade_candidates(cands: list[Candidate]) -> list[Candidate]:
    """Set each candidate's grade from its source weight plus a bonus for every
    *additional* independent source proposing the same (field, value)."""
    agree: dict[tuple[str, str], set[str]] = {}
    for c in cands:
        agree.setdefault((c.field, _norm(c.field, c.value)), set()).add(c.source)
    for c in cands:
        others = agree[(c.field, _norm(c.field, c.value))]
        extra = max(0, len(others) - 1)
        bonus = min(CORROBORATION_CAP, extra * CORROBORATION_BONUS)
        c.grade = round(min(1.0, base_grade(c.source) + bonus), 4)
        if extra:
            c.evidence = {**c.evidence, "corroborated_by": sorted(others)}
    return cands
