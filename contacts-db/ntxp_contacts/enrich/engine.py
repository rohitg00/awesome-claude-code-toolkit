"""Enrichment engine: detect missing primary fields, generate graded candidates
from the registered resolvers (+ agent-supplied OSINT candidates), and apply
confirmed values back to the canonical contact."""
from __future__ import annotations

import json

from .. import normalize as N
from ..db.repository import Repository
from ..model import Address, Email, Phone
from .base import Candidate, RESOLVERS
from .grade import grade_candidates


def _augment(repo: Repository, contact_id: int) -> dict | None:
    """get_contact + the enrichment columns + org website, as resolvers expect."""
    c = repo.get_contact(contact_id)
    if not c:
        return None
    row = repo.conn.execute(
        "SELECT c.photo_url, c.linkedin_url, o.website AS org_website "
        "FROM contacts c LEFT JOIN organizations o ON o.org_id=c.org_id "
        "WHERE c.contact_id=?", (contact_id,)).fetchone()
    if row:
        c["photo_url"] = row["photo_url"]
        c["linkedin_url"] = row["linkedin_url"]
        c["website"] = row["org_website"]
    return c


def detect_missing(conn, fields: tuple[str, ...] | None = None) -> list[dict]:
    """Live contacts missing one or more primary fields."""
    rows = conn.execute(
        "SELECT c.contact_id AS cid, c.full_name AS name, c.photo_url, c.linkedin_url, "
        "  c.org_id AS org_id, o.website AS org_website, "
        "  (SELECT COUNT(*) FROM emails e WHERE e.contact_id=c.contact_id) AS n_email, "
        "  (SELECT COUNT(*) FROM phones p WHERE p.contact_id=c.contact_id) AS n_phone, "
        "  (SELECT COUNT(*) FROM addresses a WHERE a.contact_id=c.contact_id) AS n_addr "
        "FROM contacts c LEFT JOIN organizations o ON o.org_id=c.org_id "
        "WHERE c.is_deleted=0").fetchall()
    out = []
    for r in rows:
        missing = []
        if not r["n_email"]:
            missing.append("email")
        if not r["n_phone"]:
            missing.append("phone")
        if not r["n_addr"]:
            missing.append("address")
        if r["org_id"] and not r["org_website"]:
            missing.append("website")
        if not r["photo_url"]:
            missing.append("photo")
        if not r["linkedin_url"]:
            missing.append("linkedin")
        if fields:
            missing = [m for m in missing if m in fields]
        if missing:
            out.append({"contact_id": r["cid"], "name": r["name"], "missing": missing})
    return out


def generate(conn, contact_ids: list[int] | None = None,
             extra: list[dict] | None = None, apply: bool = True) -> dict:
    """Run resolvers for the given contacts (default: all with missing fields),
    grade all candidates, and store them (proposed) for review.

    `extra` lets the agent feed candidates from out-of-band OSINT tools
    (holehe/maigret/GHunt/LinkedIn): each is a dict
    {contact_id, field, value, source, evidence?}.
    """
    repo = Repository(conn)
    if contact_ids is None:
        contact_ids = [m["contact_id"] for m in detect_missing(conn)]
    summary = {"contacts": 0, "candidates": 0, "by_field": {}, "by_source": {}}

    # Group agent-supplied extras per contact.
    extra_by_contact: dict[int, list[Candidate]] = {}
    for e in (extra or []):
        extra_by_contact.setdefault(int(e["contact_id"]), []).append(
            Candidate(e["field"], e["value"], e.get("source", "agent"),
                      evidence=e.get("evidence") or {}))

    for cid in contact_ids:
        contact = _augment(repo, cid)
        if not contact:
            continue
        cands: list[Candidate] = []
        for r in RESOLVERS.values():
            try:
                cands.extend(r.resolve(contact))
            except Exception:
                continue
        cands.extend(extra_by_contact.get(cid, []))
        if not cands:
            continue
        grade_candidates(cands)
        summary["contacts"] += 1
        for c in cands:
            summary["candidates"] += 1
            summary["by_field"][c.field] = summary["by_field"].get(c.field, 0) + 1
            summary["by_source"][c.source] = summary["by_source"].get(c.source, 0) + 1
            if apply:
                _store(conn, cid, c)
    if apply:
        conn.commit()
    return summary


def _store(conn, contact_id: int, c: Candidate) -> None:
    conn.execute(
        "INSERT INTO enrichment_candidates(contact_id, field, value, source, grade, "
        "status, evidence) VALUES (?,?,?,?,?,'proposed',?) "
        "ON CONFLICT(contact_id, field, value, source) DO UPDATE SET "
        "grade=excluded.grade, evidence=excluded.evidence",
        (contact_id, c.field, c.value, c.source, c.grade,
         json.dumps(c.evidence, default=str)))


def list_candidates(conn, status: str = "proposed", field: str | None = None,
                    contact_id: int | None = None, min_grade: float = 0.0) -> list[dict]:
    q = ("SELECT cand_id, contact_id, field, value, source, grade, status, evidence "
         "FROM enrichment_candidates WHERE status=? AND grade>=?")
    params: list = [status, min_grade]
    if field:
        q += " AND field=?"
        params.append(field)
    if contact_id:
        q += " AND contact_id=?"
        params.append(contact_id)
    q += " ORDER BY contact_id, field, grade DESC"
    out = []
    for r in conn.execute(q, params).fetchall():
        d = dict(r)
        d["evidence"] = json.loads(d.get("evidence") or "{}")
        out.append(d)
    return out


def _apply_value(repo: Repository, contact_id: int, field: str, value: str) -> None:
    conn = repo.conn
    if field == "photo":
        conn.execute("UPDATE contacts SET photo_url=?, updated_at=datetime('now') WHERE contact_id=?",
                     (value, contact_id))
    elif field == "linkedin":
        conn.execute("UPDATE contacts SET linkedin_url=?, updated_at=datetime('now') WHERE contact_id=?",
                     (value, contact_id))
    elif field == "website":
        row = conn.execute("SELECT org_id FROM contacts WHERE contact_id=?", (contact_id,)).fetchone()
        if row and row["org_id"]:
            conn.execute("UPDATE organizations SET website=COALESCE(website,?), "
                         "updated_at=datetime('now') WHERE org_id=?", (value, row["org_id"]))
    elif field == "email":
        em = N.normalize_email(value) or value
        repo.add_email(Email(email=value, email_norm=em), contact_id, None)
        repo._reindex_contact(contact_id)
    elif field == "phone":
        repo.add_phone(Phone(phone_raw=value, phone_e164=N.normalize_phone(value)), contact_id, None)
    elif field == "address":
        repo.add_address(Address(line1=value, addr_norm=(value or "").strip().lower()), contact_id, None)
    repo.log_change("contact", contact_id, "update", "enrich", field)


def confirm(conn, cand_id: int) -> dict:
    """Apply one proposed candidate to the canonical contact and mark it confirmed."""
    repo = Repository(conn)
    row = conn.execute(
        "SELECT contact_id, field, value, status FROM enrichment_candidates WHERE cand_id=?",
        (cand_id,)).fetchone()
    if not row:
        return {"ok": False, "error": "no such candidate"}
    _apply_value(repo, row["contact_id"], row["field"], row["value"])
    conn.execute("UPDATE enrichment_candidates SET status='confirmed' WHERE cand_id=?", (cand_id,))
    conn.commit()
    return {"ok": True, "contact_id": row["contact_id"], "field": row["field"], "value": row["value"]}


def reject(conn, cand_id: int) -> dict:
    conn.execute("UPDATE enrichment_candidates SET status='rejected' WHERE cand_id=?", (cand_id,))
    conn.commit()
    return {"ok": True, "cand_id": cand_id}


def confirm_linkedin(conn, contact_id: int, url: str, photo_url: str | None = None,
                     company_match: bool = True) -> dict:
    """Confirm a LinkedIn match the agent verified. Saves the URL to the LinkedIn
    field (only when it matches the contact's employer, per policy) and promotes
    the LinkedIn profile photo to the contact photo (highest priority)."""
    repo = Repository(conn)
    changed = []
    if company_match:
        _apply_value(repo, contact_id, "linkedin", url)
        conn.execute(
            "INSERT INTO enrichment_candidates(contact_id, field, value, source, grade, status, evidence) "
            "VALUES (?,?,?,?,?,'confirmed',?) ON CONFLICT(contact_id, field, value, source) "
            "DO UPDATE SET status='confirmed', grade=excluded.grade",
            (contact_id, "linkedin", url, "linkedin", 0.95,
             json.dumps({"company_match": True})))
        changed.append("linkedin")
    if photo_url:
        _apply_value(repo, contact_id, "photo", photo_url)
        conn.execute(
            "INSERT INTO enrichment_candidates(contact_id, field, value, source, grade, status, evidence) "
            "VALUES (?,?,?,?,?,'confirmed',?) ON CONFLICT(contact_id, field, value, source) "
            "DO UPDATE SET status='confirmed', grade=excluded.grade",
            (contact_id, "photo", photo_url, "linkedin", 0.95,
             json.dumps({"from": "linkedin_profile"})))
        changed.append("photo")
    conn.commit()
    return {"ok": True, "contact_id": contact_id, "changed": changed}
