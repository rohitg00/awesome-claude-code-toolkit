"""Inbound hooks. A peer POSTs a signed event to /api/v1/hooks/in/<peer>:

  schedules  assignment.upserted | assignment.removed   (who is scheduled on which project, when)
  formfill   people.seen                                (people captured on a filled form)

Verified with the peer's HMAC secret (5-minute replay window) and applied exactly once per
event id. Unknown event types are acknowledged and ignored, so peers can add events without
breaking us. Nothing here creates fuzzy matches: Schedules must identify a person by
contact_id or exact email; Form Fill people go through the normal dedup resolver.
"""
from __future__ import annotations

import json
import re
from datetime import date

from .. import normalize as N
from ..model import Address, Tag
from . import context as ctx
from .signing import SIG_HEADER, verify

MAX_PEOPLE = 200
_STATUSES = {"scheduled", "active", "completed", "cancelled"}


def _s(v, n=300) -> str:
    return re.sub(r"[\x00-\x1f]", " ", "" if v is None else str(v)).strip()[:n]


def _iso(v) -> str | None:
    try:
        return date.fromisoformat(_s(v, 10)).isoformat()
    except ValueError:
        return None


def handle(conn, peers: dict, peer_name: str, body: bytes, headers: dict):
    """-> (status, json-able). `headers` keys are lower-case."""
    peer = peers.get(peer_name)
    if peer is None:
        return 404, {"error": "unknown peer"}
    if not verify(peer.secret, body, headers.get(SIG_HEADER.lower())):
        return 401, {"error": "bad or expired signature"}
    try:
        ev = json.loads(body)
        eid, etype, data = _s(ev["id"], 120), _s(ev["type"], 60), ev.get("data") or {}
        if not eid or not isinstance(data, dict):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        return 400, {"error": "body must be {id, type, data}"}
    first = conn.execute("INSERT INTO peer_seen(peer, event_id, seen_at) VALUES (?,?,?) "
                         "ON CONFLICT(peer, event_id) DO NOTHING", (peer_name, eid, ctx.now_ts(conn))).rowcount
    if not first:
        return 200, {"duplicate": True}
    if peer_name == "schedules" and etype in ("assignment.upserted", "assignment.removed"):
        res = _assignment(conn, etype, data)
    elif peer_name == "formfill" and etype == "people.seen":
        res = _people_seen(conn, data)
    elif etype == "ping":
        res = {"pong": True}
    else:
        res = {"ignored": etype}
    conn.commit()
    return 200, res


def _resolve_person(conn, p: dict) -> int | None:
    from ..db.repository import Repository
    if isinstance(p, dict) and p.get("contact_id") is not None:
        try:
            cid = int(p["contact_id"])
        except (TypeError, ValueError):
            return None
        row = conn.execute("SELECT 1 FROM contacts WHERE contact_id=? AND is_deleted=0", (cid,)).fetchone()
        return cid if row else None
    em = N.normalize_email((p or {}).get("email"))
    return Repository(conn).find_contact_by_email(em) if em else None


def _assignment(conn, etype: str, d: dict) -> dict:
    from ..db.repository import Repository
    aid = _s(d.get("assignment_id"), 80)
    if not aid:
        return {"error": "assignment_id required"}
    if etype == "assignment.removed":
        return {"removed": ctx.delete(conn, "schedules", "assignment", aid)}
    cid = _resolve_person(conn, d.get("person") or {})
    if cid is None:
        return {"matched": False}        # no fuzzy matching: send contact_id or an exact email
    status = _s(d.get("status") or "scheduled", 20).lower()
    if status not in _STATUSES:
        return {"error": f"status must be one of {sorted(_STATUSES)}"}
    a = {"assignment_id": aid, "project": _s(d.get("project"), 120), "role": _s(d.get("role"), 60),
         "start": _iso(d.get("start")), "end": _iso(d.get("end")), "status": status}
    ctx.upsert(conn, "schedules", "assignment", aid, a, contact_id=cid)
    repo = Repository(conn)
    if a["project"] and status in ("scheduled", "active"):
        repo.add_tag(Tag("project", a["project"]), "contact", cid)    # makes them filterable by project
    repo.log_change("contact", cid, "update", "peer:schedules", "assignment")
    return {"matched": True, "contact_id": cid}


def _people_seen(conn, d: dict) -> dict:
    from ..collect import ingest
    from ..connectors.base import map_contact
    people = d.get("people") or []
    if not isinstance(people, list) or len(people) > MAX_PEOPLE:
        return {"error": f"people must be a list of at most {MAX_PEOPLE}"}
    recs = []
    for raw in people:
        if not isinstance(raw, dict):
            continue
        clean = {k: _s(raw.get(k)) for k in ("name", "email", "phone", "company", "title")}
        rec = map_contact("formfill", clean)
        if rec is None:
            continue
        a = raw.get("address")
        if isinstance(a, dict):
            addr = Address(line1=_s(a.get("line1")), city=_s(a.get("city")), state=N.normalize_state(a.get("state")),
                           zip=N.normalize_zip(a.get("zip")),
                           addr_norm=N.addr_norm(a.get("line1"), a.get("city"), a.get("state"), a.get("zip")) or "")
            (rec.org_addresses if rec.org_name else rec.addresses).append(addr)
        rec.tags.append(Tag("label", f"Form: {_s(d.get('form'), 60)}")) if d.get("form") else None
        recs.append(rec)
    res = ingest(conn, recs, origin="peer:formfill")
    return {"people": len(recs), "new": res["new"], "updated": res["updated"], "skipped": res["skipped"]}
