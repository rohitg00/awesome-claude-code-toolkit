"""Identity resolution: normalize -> block -> score -> decide.

Resolves orgs deterministically by normalized name; resolves contacts by
email short-circuit, then scored fuzzy match against a blocked candidate set.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..config import MATCH_THRESHOLD, REVIEW_THRESHOLD
from ..db.repository import Repository
from ..model import CanonicalRecord
from . import scorer


@dataclass
class MatchDecision:
    contact_id: int | None
    is_new: bool
    needs_review: bool
    score: float = 0.0


class Resolver:
    def __init__(self, repo: Repository):
        self.repo = repo

    # -- organizations: deterministic on normalized name --------------------
    def resolve_org(self, rec: CanonicalRecord, origin: str) -> int | None:
        if not rec.has_org:
            return None
        existing = self.repo.find_org_by_norm(rec.org_name_norm)
        if existing:
            self.repo.update_org(existing, rec, origin)
            return existing
        return self.repo.create_org(rec, origin)

    # -- contacts -----------------------------------------------------------
    def resolve_contact(self, rec: CanonicalRecord, org_id: int | None,
                        origin: str) -> MatchDecision:
        if not rec.has_contact:
            return MatchDecision(contact_id=None, is_new=False, needs_review=False)

        # 1) Email short-circuit (valid emails only).
        for e in rec.emails:
            if e.is_invalid:
                continue
            hit = self.repo.find_contact_by_email(e.email_norm)
            if hit:
                self.repo.update_contact(hit, rec, org_id, origin)
                return MatchDecision(hit, is_new=False, needs_review=False, score=1.0)

        # 2) Blocked scored match.
        from ..normalize import block_key
        bkey = block_key(rec.first_name, rec.last_name, rec.name_norm)
        rec_phones = {p.phone_e164 for p in rec.phones if p.phone_e164}
        rec_state = _record_state(rec)
        best_id, best_score, best_name_sim = None, 0.0, 0.0
        for cand in self.repo.contact_candidates(bkey, org_id):
            cand_phones = set((cand["phones"] or "").split(",")) - {""}
            ns = scorer.name_similarity(rec.name_norm or "", cand["name_norm"] or "")
            s = scorer.score_contact(
                rec.name_norm or "", rec.org_name_norm, rec_phones, rec_state,
                cand["name_norm"] or "", cand["org_norm"], cand_phones,
                cand["org_state"],
            )
            if s > best_score:
                best_id, best_score, best_name_sim = cand["contact_id"], s, ns

        if best_id is not None and best_score >= MATCH_THRESHOLD:
            self.repo.update_contact(best_id, rec, org_id, origin)
            return MatchDecision(best_id, is_new=False, needs_review=False, score=best_score)

        # 3) Create new; flag review-band near-matches. Gate the flag on the
        # NAMES actually being similar so we don't flag two different people who
        # merely share a surname+initial and employer.
        needs_review = (best_id is not None and best_score >= REVIEW_THRESHOLD
                        and best_name_sim >= 0.82)
        new_id = self.repo.create_contact(rec, org_id, origin)
        if needs_review:
            from ..model import Tag
            self.repo.add_tag(Tag("review", f"near_dupe:{best_id}:{best_score}"),
                              "contact", new_id)
        return MatchDecision(new_id, is_new=True, needs_review=needs_review, score=best_score)


def _record_state(rec: CanonicalRecord) -> str | None:
    for a in (rec.addresses or rec.org_addresses):
        if a.state:
            return a.state
    return None
