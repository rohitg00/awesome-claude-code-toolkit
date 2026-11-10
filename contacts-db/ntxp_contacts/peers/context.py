"""Facts pulled from / pushed by peers (contracts, schedule assignments), cached
locally so contact cards and the prompt hook can inject them instantly and offline."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone


def now_ts(conn, offset_s: float = 0.0):
    """A 'now' value in the form this backend compares/stores: aware datetime on
    Postgres, 'YYYY-MM-DD HH:MM:SS' (UTC) on SQLite."""
    dt = datetime.now(timezone.utc) + timedelta(seconds=offset_s)
    return dt if getattr(conn, "backend", "sqlite") == "postgres" else dt.strftime("%Y-%m-%d %H:%M:%S")


def upsert(conn, peer: str, kind: str, ref: str, payload: dict,
           org_id: int | None = None, contact_id: int | None = None) -> None:
    conn.execute(
        "INSERT INTO peer_context(peer, kind, ref, org_id, contact_id, payload, observed_at) "
        "VALUES (?,?,?,?,?,?,?) ON CONFLICT(peer, kind, ref) DO UPDATE SET "
        "org_id=excluded.org_id, contact_id=excluded.contact_id, payload=excluded.payload, "
        "observed_at=excluded.observed_at",
        (peer, kind, str(ref), org_id, contact_id, json.dumps(payload, default=str), now_ts(conn)))


def delete(conn, peer: str, kind: str, ref: str) -> int:
    return conn.execute("DELETE FROM peer_context WHERE peer=? AND kind=? AND ref=?",
                        (peer, kind, str(ref))).rowcount


def delete_missing(conn, peer: str, kind: str, keep_refs: set[str]) -> int:
    n = 0
    for r in conn.execute("SELECT ref FROM peer_context WHERE peer=? AND kind=?", (peer, kind)).fetchall():
        if r["ref"] not in keep_refs:
            n += delete(conn, peer, kind, r["ref"])
    return n


def _days_until(iso: str | None, today: date) -> int | None:
    try:
        return (date.fromisoformat((iso or "")[:10]) - today).days
    except ValueError:
        return None


def contracts_for_org(conn, org_id: int | None, today: date | None = None) -> list[dict]:
    """Master Contracts entries for an organization, with live flags computed at read
    time (expired / expiring within 90 days / unexecuted) so a cached row never goes stale."""
    if not org_id:
        return []
    today = today or date.today()
    out = []
    for r in conn.execute("SELECT ref, payload FROM peer_context WHERE peer='contracts' AND kind='contract' "
                          "AND org_id=? ORDER BY ref", (org_id,)).fetchall():
        c = json.loads(r["payload"])
        d = _days_until(c.get("expires"), today)
        c["days_to_expiry"] = d
        c["flags"] = [f for f, on in (("expired", d is not None and d < 0),
                                      ("expiring", d is not None and 0 <= d <= 90),
                                      ("unexecuted", c.get("executed") is False)) if on]
        out.append(c)
    return sorted(out, key=lambda c: (c.get("days_to_expiry") is None, c.get("days_to_expiry") or 0))


def assignments_for_contact(conn, contact_id: int, today: date | None = None) -> list[dict]:
    """Schedules assignments for a contact that haven't ended yet."""
    today = (today or date.today()).isoformat()
    out = []
    for r in conn.execute("SELECT ref, payload FROM peer_context WHERE peer='schedules' AND kind='assignment' "
                          "AND contact_id=? ORDER BY ref", (contact_id,)).fetchall():
        a = json.loads(r["payload"])
        if (a.get("end") or "9999-12-31") >= today and a.get("status") != "cancelled":
            out.append(a)
    return sorted(out, key=lambda a: a.get("start") or "")


def for_contact(conn, contact_id: int, org_id: int | None) -> dict:
    return {"contracts": contracts_for_org(conn, org_id),
            "assignments": assignments_for_contact(conn, contact_id)}
