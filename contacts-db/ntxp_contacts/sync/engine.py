"""Sync engine: turns the change_log into a per-system push plan, and applies
remote records on pull. Conflict policy: field-level last-write-wins with a
configurable `master_wins` allowlist. Push is always plan-then-apply.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3

from ..config import MASTER_WINS_FIELDS
from ..db.repository import Repository


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


class SyncEngine:
    def __init__(self, conn: sqlite3.Connection, system: str):
        self.conn = conn
        self.system = system
        self.repo = Repository(conn)

    def _high_water(self) -> int:
        row = self.conn.execute(
            "SELECT last_seq FROM sync_state WHERE system = ?", (self.system,)).fetchone()
        return int(row["last_seq"]) if row else 0

    def set_high_water(self, seq: int) -> None:
        self.conn.execute(
            "INSERT INTO sync_state(system, last_seq, last_pull_at) VALUES (?,?,datetime('now')) "
            "ON CONFLICT(system) DO UPDATE SET last_seq = excluded.last_seq",
            (self.system, seq))
        self.conn.commit()

    def pending_changes(self) -> list[sqlite3.Row]:
        hw = self._high_water()
        return self.conn.execute(
            "SELECT * FROM change_log WHERE seq > ? ORDER BY seq", (hw,)).fetchall()

    def plan(self, direction: str) -> list[dict]:
        """Return a JSON-serializable list of intended sync operations.

        This performs NO network I/O — it is the dry-run / plan stage that the
        REST executor or the MCP-mediated agent then carries out.
        """
        if direction == "push":
            return self._plan_push()
        return self._plan_pull()

    def _plan_push(self) -> list[dict]:
        seen: dict[tuple[str, int], dict] = {}
        for ch in self.pending_changes():
            key = (ch["entity_type"], ch["entity_id"])
            if ch["entity_type"] != "contact":
                continue
            rec = self.repo.get_contact(ch["entity_id"])
            if not rec or rec.get("is_deleted"):
                continue
            ext = self.conn.execute(
                "SELECT external_id, remote_hash FROM external_ids "
                "WHERE system = ? AND contact_id = ?",
                (self.system, ch["entity_id"])).fetchone()
            fields = _contact_to_fields(rec)
            op = "update" if ext else "create"
            new_hash = payload_hash(fields)
            if ext and ext["remote_hash"] == new_hash:
                continue  # remote already current — skip
            seen[key] = {
                "system": self.system,
                "op": op,
                "entity_type": "contact",
                "entity_id": ch["entity_id"],
                "external_id": ext["external_id"] if ext else None,
                "master_wins_fields": sorted(MASTER_WINS_FIELDS),
                "fields": fields,
                "payload_hash": new_hash,
            }
        return list(seen.values())

    def _plan_pull(self) -> list[dict]:
        # The plan for a pull is "fetch since high-water"; the actual records
        # come from the adapter's transport at apply time.
        return [{
            "system": self.system,
            "op": "pull",
            "since": (self.conn.execute(
                "SELECT last_pull_at FROM sync_state WHERE system = ?",
                (self.system,)).fetchone() or {"last_pull_at": None})["last_pull_at"],
        }]

    def record_result(self, entity_id: int, external_id: str, remote_hash: str) -> None:
        """Persist an external mapping after a successful push (or MCP apply)."""
        self.conn.execute(
            "INSERT INTO external_ids(system, external_id, contact_id, remote_hash, "
            "last_synced_at, sync_state) VALUES (?,?,?,?,datetime('now'),'linked') "
            "ON CONFLICT(system, external_id) DO UPDATE SET "
            "contact_id = excluded.contact_id, remote_hash = excluded.remote_hash, "
            "last_synced_at = datetime('now'), sync_state = 'linked'",
            (self.system, external_id, entity_id, remote_hash))
        seq = self.conn.execute("SELECT COALESCE(MAX(seq),0) s FROM change_log").fetchone()["s"]
        self.set_high_water(seq)


def _contact_to_fields(rec: dict) -> dict:
    emails = rec.get("emails") or []
    phones = rec.get("phones") or []
    return {
        "first_name": rec.get("first_name"),
        "last_name": rec.get("last_name"),
        "title": rec.get("title"),
        "company": rec.get("org_name"),
        "email": emails[0]["email"] if emails else None,
        "phone": (phones[0].get("phone_e164") or phones[0].get("phone_raw")) if phones else None,
    }
