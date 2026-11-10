"""Outbound hooks: turn contact changes into signed, durable, retryable webhooks.

  emit_changes  change_log -> peer_outbox   (exposure-gated, echo-guarded, idempotent)
  deliver_due   peer_outbox -> HTTP POST    (HMAC-signed; backoff; dead-letter)

Event types: contact.upserted (full autofill bag), contact.removed (deleted, merged or no
longer exposed). Peers are told only about contacts the grader exposes, the same rule as
the UI, the Sheet and the iOS feed.
"""
from __future__ import annotations

import fnmatch
import json
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

from . import context as ctx
from .signing import SIG_HEADER, sign

MAX_ATTEMPTS = 8
LEASE_S = 120
BACKOFF_BASE_S = 30
BACKOFF_CAP_S = 3600
BATCH = 5000


def contact_bag(conn, cid: int) -> dict | None:
    """The autofill/context bag for one contact, or None if it is not exposed/live."""
    from ..db.repository import Repository
    from ..remote.api import BASE, _shape
    row = conn.execute(f"SELECT * FROM ({BASE}) x WHERE id=?", (cid,)).fetchone()
    if not row:
        return None
    r = _shape(dict(row))
    full = Repository(conn).get_contact(cid) or {}
    addr = next(iter(full.get("addresses") or []), None) or {}
    org_id = conn.execute("SELECT org_id FROM contacts WHERE contact_id=?", (cid,)).fetchone()["org_id"]
    from ..config import contacts_url
    return {
        "id": cid, "first_name": r["first_name"], "last_name": r["last_name"], "full_name": r["full_name"],
        "title": r["title"], "company": r["company"], "website": r["website"],
        "email": r["email"], "emails": [e["email"] for e in full.get("emails") or [] if not e.get("is_invalid")],
        "phone": r["phone"], "phones": [p.get("phone_e164") or p.get("phone_raw") for p in full.get("phones") or []],
        "address": {k: addr.get(k) for k in ("line1", "city", "state", "zip")} if addr else None,
        "role": r["role"], "trade": r["trade"], "project": r["project"], "labels": r["labels"],
        "linkedin_url": r["linkedin_url"], "photo_url": r["photo_url"], "grade_band": r["grade_band"],
        "contracts": ctx.contracts_for_org(conn, org_id),
        "updated_at": r["updated_at"], "href": f"{contacts_url()}?focus=contact:{cid}",
    }


def _cursor(conn, peer: str, stream: str) -> int | None:
    r = conn.execute("SELECT cursor FROM peer_cursor WHERE peer=? AND stream=?", (peer, stream)).fetchone()
    return int(r["cursor"]) if r else None


def set_cursor(conn, peer: str, stream: str, value) -> None:
    conn.execute("INSERT INTO peer_cursor(peer, stream, cursor, updated_at) VALUES (?,?,?,?) "
                 "ON CONFLICT(peer, stream) DO UPDATE SET cursor=excluded.cursor, updated_at=excluded.updated_at",
                 (peer, stream, str(value), ctx.now_ts(conn)))


def get_cursor(conn, peer: str, stream: str):
    r = conn.execute("SELECT cursor FROM peer_cursor WHERE peer=? AND stream=?", (peer, stream)).fetchone()
    return r["cursor"] if r else None


def _wants(peer, event_type: str) -> bool:
    return any(fnmatch.fnmatch(event_type, pat) for pat in peer.events)


def enqueue(conn, peer, event_id: str, event_type: str, data: dict) -> bool:
    if not _wants(peer, event_type):
        return False
    body = {"id": f"{peer.name}:{event_id}", "type": event_type, "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    n = conn.execute("INSERT INTO peer_outbox(peer, event_id, event_type, payload, next_attempt_at) "
                     "VALUES (?,?,?,?,?) ON CONFLICT(peer, event_id) DO NOTHING",
                     (peer.name, event_id, event_type, json.dumps(body, default=str), ctx.now_ts(conn))).rowcount
    return bool(n)


def emit_changes(conn, peers: dict) -> dict:
    """Queue events for contacts changed since each peer's cursor. The first run only
    records the starting point (no flood); use backfill() to send everything once."""
    summary = {}
    head = conn.execute("SELECT COALESCE(MAX(seq),0) m FROM change_log").fetchone()["m"]
    for name, peer in peers.items():
        if not peer.receives_events:
            continue
        cur = _cursor(conn, name, "change_log")
        if cur is None:
            set_cursor(conn, name, "change_log", head)
            summary[name] = {"queued": 0, "initialised_at": int(head)}
            continue
        rows = conn.execute("SELECT seq, entity_id, origin FROM change_log WHERE entity_type='contact' "
                            "AND seq > ? ORDER BY seq LIMIT ?", (cur, BATCH)).fetchall()
        echo = f"peer:{name}"
        by_id: dict[int, dict] = {}
        for r in rows:
            e = by_id.setdefault(r["entity_id"], {"seq": 0, "all_echo": True})
            e["seq"] = max(e["seq"], r["seq"])
            e["all_echo"] = e["all_echo"] and r["origin"] == echo     # don't tell a peer about its own write
        queued = 0
        for cid, e in by_id.items():
            if e["all_echo"]:
                continue
            bag = contact_bag(conn, cid)
            if bag is None:
                m = conn.execute("SELECT merged_into FROM contacts WHERE contact_id=?", (cid,)).fetchone()
                queued += enqueue(conn, peer, f"{cid}-{e['seq']}", "contact.removed",
                                  {"id": cid, "merged_into": m["merged_into"] if m else None})
            else:
                queued += enqueue(conn, peer, f"{cid}-{e['seq']}", "contact.upserted", bag)
        if rows:
            set_cursor(conn, name, "change_log", rows[-1]["seq"])
        summary[name] = {"queued": queued, "changes": len(rows)}
    conn.commit()
    return summary


def backfill(conn, peer) -> int:
    """Send every exposed contact once (e.g. when a peer is first connected)."""
    from ..remote.api import BASE
    n = 0
    for r in conn.execute(f"SELECT id FROM ({BASE}) x ORDER BY id").fetchall():
        bag = contact_bag(conn, r["id"])
        if bag:
            n += enqueue(conn, peer, f"{r['id']}-backfill-{uuid.uuid4().hex[:8]}", "contact.upserted", bag)
    conn.commit()
    return n


def _post(url: str, body: bytes, headers: dict, timeout: float = 8.0) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as e:
        return e.code, f"HTTP {e.code}"
    except Exception as e:                                    # network error, timeout, DNS
        return 0, f"{type(e).__name__}: {e}"[:200]


def deliver_due(conn, peers: dict, limit: int = 50, post=_post) -> dict:
    """Deliver due events. 2xx = delivered; 4xx (other than 408/425/429) = dead at once (the
    peer rejected it for good); anything else retries with exponential backoff, then dead."""
    out = {"delivered": 0, "retried": 0, "dead": 0}
    due = conn.execute("SELECT outbox_id, peer, event_id, event_type, payload, attempts FROM peer_outbox "
                       "WHERE status IN ('pending','sending') AND next_attempt_at <= ? ORDER BY outbox_id LIMIT ?",
                       (ctx.now_ts(conn), limit)).fetchall()
    for r in due:
        claimed = conn.execute("UPDATE peer_outbox SET status='sending', next_attempt_at=? "
                               "WHERE outbox_id=? AND status IN ('pending','sending') AND next_attempt_at <= ?",
                               (ctx.now_ts(conn, LEASE_S), r["outbox_id"], ctx.now_ts(conn))).rowcount
        conn.commit()
        if not claimed:
            continue                                          # another worker took it
        peer = peers.get(r["peer"])
        attempts = r["attempts"] + 1
        if peer is None:
            status, err = 0, "peer no longer configured"
        else:
            body = r["payload"].encode()
            ts, sig = sign(peer.secret, body)
            status, err = post(peer.hook_url, body, {
                "Content-Type": "application/json", "User-Agent": "ntxp-contacts/1",
                "X-NTXP-Event": r["event_type"], "X-NTXP-Event-Id": json.loads(r["payload"])["id"],
                "X-NTXP-Timestamp": str(ts), SIG_HEADER: sig})
        if 200 <= status < 300:
            conn.execute("UPDATE peer_outbox SET status='delivered', attempts=?, delivered_at=?, last_error=NULL "
                         "WHERE outbox_id=?", (attempts, ctx.now_ts(conn), r["outbox_id"]))
            out["delivered"] += 1
        elif (400 <= status < 500 and status not in (408, 425, 429)) or attempts >= MAX_ATTEMPTS or peer is None:
            conn.execute("UPDATE peer_outbox SET status='dead', attempts=?, last_error=? WHERE outbox_id=?",
                         (attempts, err or f"HTTP {status}", r["outbox_id"]))
            out["dead"] += 1
        else:
            delay = min(BACKOFF_BASE_S * 2 ** (attempts - 1), BACKOFF_CAP_S)
            conn.execute("UPDATE peer_outbox SET status='pending', attempts=?, last_error=?, next_attempt_at=? "
                         "WHERE outbox_id=?", (attempts, err or f"HTTP {status}", ctx.now_ts(conn, delay), r["outbox_id"]))
            out["retried"] += 1
        conn.commit()
    return out


def outbox_stats(conn) -> dict:
    return {r["status"]: r["n"] for r in conn.execute(
        "SELECT status, COUNT(*) n FROM peer_outbox GROUP BY status").fetchall()}
