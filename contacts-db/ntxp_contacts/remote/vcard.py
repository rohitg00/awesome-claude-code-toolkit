"""vCard rendering for the one-way iOS/iPhone contact feed.

Only **exposed** contacts are emitted (the grader's exposure gate), so outdated
or held-back records never leave the building. One-way by design: this renders
out; nothing writes back.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..db.repository import Repository


def _esc(v) -> str:
    s = "" if v is None else str(v)
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def uid(contact_id: int) -> str:
    return f"ntxp-{contact_id}"


def contact_vcard(rec: dict, photo_url: str | None = None,
                  linkedin_url: str | None = None) -> str:
    """Render one get_contact() dict as a vCard 3.0 block."""
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"UID:{uid(rec['contact_id'])}"]
    fn = rec.get("full_name") or " ".join(
        x for x in (rec.get("first_name"), rec.get("last_name")) if x) or "NTXP Contact"
    lines.append("FN:" + _esc(fn))
    lines.append(f"N:{_esc(rec.get('last_name'))};{_esc(rec.get('first_name'))};;;")
    if rec.get("org_name"):
        lines.append("ORG:" + _esc(rec["org_name"]))
    if rec.get("title"):
        lines.append("TITLE:" + _esc(rec["title"]))
    for i, e in enumerate(rec.get("emails") or []):
        if e.get("email"):
            pref = ",PREF" if i == 0 else ""
            lines.append(f"EMAIL;TYPE=INTERNET{pref}:" + _esc(e["email"]))
    for i, p in enumerate(rec.get("phones") or []):
        num = p.get("phone_e164") or p.get("phone_raw")
        if num:
            kind = (p.get("kind") or "work").upper()
            t = {"CELL": "CELL", "FAX": "FAX", "OFFICE": "WORK", "MAIN": "WORK"}.get(kind, "WORK")
            lines.append(f"TEL;TYPE={t}:" + _esc(num))
    for a in rec.get("addresses") or []:
        if a.get("line1") or a.get("city"):
            lines.append("ADR;TYPE=WORK:;;%s;%s;%s;%s;" % (
                _esc(a.get("line1")), _esc(a.get("city")),
                _esc(a.get("state")), _esc(a.get("zip"))))
    if rec.get("website"):
        lines.append("URL:" + _esc(rec["website"]))
    if photo_url:
        lines.append("PHOTO;VALUE=URI:" + _esc(photo_url))
    if linkedin_url:
        lines.append("X-SOCIALPROFILE;TYPE=linkedin:" + _esc(linkedin_url))
    labels = [t["value"] for t in (rec.get("tags") or [])
              if t.get("kind") in ("member", "region", "trade", "contact_type")]
    if labels:
        lines.append("CATEGORIES:" + ",".join(_esc(x) for x in labels))
    lines.append("REV:" + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    lines.append("END:VCARD")
    return "\r\n".join(lines)


def _exposed_sql(exposed_only: bool) -> str:
    sql = ("FROM contacts c LEFT JOIN contact_grade g ON g.contact_id=c.contact_id "
           "WHERE c.is_deleted=0")
    if exposed_only:
        sql += " AND (g.is_exposed IS NULL OR g.is_exposed=1)"
    return sql


def exposed_contact_ids(conn, exposed_only: bool = True) -> list[int]:
    rows = conn.execute("SELECT c.contact_id " + _exposed_sql(exposed_only)
                        + " ORDER BY c.contact_id").fetchall()
    return [r["contact_id"] for r in rows]


def is_exposed(conn, contact_id: int, exposed_only: bool = True) -> bool:
    """Whether a single contact may be served (live + exposed) — gates direct
    CardDAV item GETs and multiget, not just the collection listing."""
    row = conn.execute(
        "SELECT c.contact_id " + _exposed_sql(exposed_only) + " AND c.contact_id=?",
        (contact_id,)).fetchone()
    return row is not None


def exposed_rows(conn, exposed_only: bool = True) -> list[tuple[int, str]]:
    """(contact_id, revision) for exposed contacts; revision = updated_at, which
    advances on any representation or exposure change — drives CardDAV validators."""
    rows = conn.execute(
        "SELECT c.contact_id AS cid, c.updated_at AS rev, g.computed_at AS grev "
        + _exposed_sql(exposed_only) + " ORDER BY c.contact_id").fetchall()
    return [(r["cid"], f"{r['rev']}|{r['grev'] or ''}") for r in rows]


def render_one(conn, contact_id: int) -> str | None:
    repo = Repository(conn)
    rec = repo.get_contact(contact_id)
    if not rec:
        return None
    extra = conn.execute(
        "SELECT c.photo_url, c.linkedin_url, o.website AS website "
        "FROM contacts c LEFT JOIN organizations o ON o.org_id=c.org_id "
        "WHERE c.contact_id=?", (contact_id,)).fetchone()
    if extra:
        rec["website"] = extra["website"]
    return contact_vcard(rec, extra["photo_url"] if extra else None,
                         extra["linkedin_url"] if extra else None)


def export_vcards(conn, exposed_only: bool = True) -> str:
    cards = [render_one(conn, cid) for cid in exposed_contact_ids(conn, exposed_only)]
    return "\r\n".join(c for c in cards if c) + ("\r\n" if cards else "")
