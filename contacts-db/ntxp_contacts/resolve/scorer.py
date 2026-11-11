"""Weighted similarity score between a CanonicalRecord and a candidate contact.

No ML. Uses rapidfuzz token_sort_ratio when available, with a stdlib
difflib fallback so the module imports without rapidfuzz.
"""
from __future__ import annotations

from ..config import SCORE_WEIGHTS

try:
    from rapidfuzz import fuzz  # type: ignore

    def _ratio(a: str, b: str) -> float:
        return fuzz.token_sort_ratio(a, b) / 100.0
except Exception:  # pragma: no cover
    from difflib import SequenceMatcher

    def _ratio(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return _ratio(a, b)


def score_contact(rec_name_norm: str, rec_org_norm: str | None,
                  rec_phones: set[str], rec_state: str | None,
                  cand_name_norm: str, cand_org_norm: str | None,
                  cand_phones: set[str], cand_state: str | None) -> float:
    """Return a 0..1 match score."""
    w = SCORE_WEIGHTS
    score = w["name"] * name_similarity(rec_name_norm, cand_name_norm)

    if rec_org_norm and cand_org_norm:
        org = 1.0 if rec_org_norm == cand_org_norm else name_similarity(rec_org_norm, cand_org_norm)
        score += w["org"] * org

    if rec_phones and cand_phones:
        score += w["phone"] * (1.0 if rec_phones & cand_phones else 0.0)

    if rec_state and cand_state and rec_state == cand_state:
        score += w["state"]

    return round(score, 4)
