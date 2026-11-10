"""Delta reconciliation against the canonical store.

Lightfield is the canonical hub (see config.CANONICAL_SOURCE): every system
reconciles back to it. This module turns a batch of records pulled from one
system into:

  * a **plan** (read-only) — per record: create / link / update / conflict /
    unchanged, plus the specific fields that disagree with canonical; and
  * an **apply** (writes to OUR canonical DB only, never to the remote CRM) —
    idempotent enrich via the normal resolver pipeline, linking external_ids
    and recording provenance.

Change-only by construction: a record whose remote payload hash already matches
the stored `external_ids.remote_hash` is skipped. Applying a pull writes
change_log rows tagged `pull:<system>`; the push planner skips those for that
same system (no echo), while fan-out to the *other* systems still happens.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import SYSTEM_PRECEDENCE
from ..db.repository import Repository
from ..loaders.base import _attach_comms, _row_hash
from ..resolve import Resolver
from .base import RemoteRecord, get_adapter
from .engine import payload_hash

# Canonical fields compared when deciding whether a remote disagrees with us.
_COMPARE_FIELDS = ("first_name", "last_name", "title", "org_name")


@dataclass
class ReconcileOp:
    external_id: str
    op: str                       # create|link|update|conflict|unchanged
    contact_id: int | None = None
    conflicts: list[str] = field(default_factory=list)


@dataclass
class ReconcileStats:
    system: str
    total: int = 0
    created: int = 0
    linked: int = 0
    updated: int = 0
    unchanged: int = 0
    conflicts: int = 0
    needs_review: int = 0

    def as_dict(self) -> dict:
        return dict(self.__dict__)


class Reconciler:
    """Reconcile one system's pulled records into the canonical store."""

    def __init__(self, conn, system: str):
        self.conn = conn
        self.system = system
        self.repo = Repository(conn)
        self.resolver = Resolver(self.repo)
        self.adapter = get_adapter(system)
        self.rank = SYSTEM_PRECEDENCE.get(system, 0)

    # -- linkage ------------------------------------------------------------
    def _linked(self, external_id: str):
        return self.conn.execute(
            "SELECT contact_id, remote_hash FROM external_ids "
            "WHERE system = ? AND external_id = ?",
            (self.system, external_id)).fetchone()

    def _match_by_email(self, rec) -> int | None:
        for e in rec.emails:
            cid = self.repo.find_contact_by_email(e.email_norm)
            if cid:
                return cid
        return None

    def _conflicts(self, rec, contact_id: int) -> list[str]:
        """Fields where the remote has a value that differs from an existing,
        non-empty canonical value. Lower-ranked systems lose these on apply
        (the resolver only fills blanks), so the plan surfaces them for review."""
        cur = self.repo.get_contact(contact_id) or {}
        out = []
        remote_vals = {
            "first_name": rec.first_name, "last_name": rec.last_name,
            "title": rec.title, "org_name": rec.org_name,
        }
        for f in _COMPARE_FIELDS:
            rv, ev = remote_vals.get(f), cur.get(f)
            if rv and ev and str(rv).strip().lower() != str(ev).strip().lower():
                out.append(f)
        return out

    # -- plan (read-only) ---------------------------------------------------
    def plan(self, remotes: list[RemoteRecord]) -> dict:
        ops: list[ReconcileOp] = []
        st = ReconcileStats(system=self.system)
        for r in remotes:
            st.total += 1
            rec = self.adapter.to_canonical(r)
            rhash = payload_hash(r.payload)
            link = self._linked(r.external_id)
            if link is not None:
                cid = link["contact_id"]
                if link["remote_hash"] == rhash:
                    ops.append(ReconcileOp(r.external_id, "unchanged", cid))
                    st.unchanged += 1
                    continue
                conflicts = self._conflicts(rec, cid)
                if conflicts:
                    ops.append(ReconcileOp(r.external_id, "conflict", cid, conflicts))
                    st.conflicts += 1
                else:
                    ops.append(ReconcileOp(r.external_id, "update", cid))
                    st.updated += 1
                continue
            cid = self._match_by_email(rec)
            if cid:
                conflicts = self._conflicts(rec, cid)
                ops.append(ReconcileOp(r.external_id, "link", cid, conflicts))
                st.linked += 1
                st.conflicts += 1 if conflicts else 0
            else:
                ops.append(ReconcileOp(r.external_id, "create"))
                st.created += 1
        return {
            "system": self.system,
            "summary": st.as_dict(),
            "ops": [o.__dict__ for o in ops],
        }

    # -- apply (writes to OUR canonical DB only) ----------------------------
    def apply(self, remotes: list[RemoteRecord], origin: str | None = None) -> dict:
        origin = origin or f"pull:{self.system}"
        self.repo.defer_fts = True
        st = ReconcileStats(system=self.system)
        for r in remotes:
            st.total += 1
            rec = self.adapter.to_canonical(r)
            if not (rec.has_contact or rec.has_org):
                continue
            link = self._linked(r.external_id)
            if link is not None and link["remote_hash"] == payload_hash(r.payload):
                st.unchanged += 1   # already current — don't re-resolve or re-log
                continue
            had_link = link is not None
            org_id = self.resolver.resolve_org(rec, origin)
            decision = self.resolver.resolve_contact(rec, org_id, origin)
            _attach_comms(self.repo, rec, decision.contact_id, org_id)
            self.repo.record_source(self.system, r.external_id, _row_hash(rec),
                                    rec.raw, decision.contact_id, org_id)
            self._link(r.external_id, decision.contact_id, payload_hash(r.payload))
            if decision.is_new:
                st.created += 1
            elif had_link:
                st.updated += 1
            else:
                st.linked += 1
            if decision.needs_review:
                st.needs_review += 1
        self.repo.rebuild_fts()
        self.conn.commit()
        return st.as_dict()

    def _link(self, external_id: str, contact_id: int | None, remote_hash: str) -> None:
        if contact_id is None:
            return
        self.conn.execute(
            "INSERT INTO external_ids(system, external_id, contact_id, remote_hash, "
            "last_synced_at, sync_state) VALUES (?,?,?,?,datetime('now'),'linked') "
            "ON CONFLICT(system, external_id) DO UPDATE SET contact_id = excluded.contact_id, "
            "remote_hash = excluded.remote_hash, last_synced_at = datetime('now'), "
            "sync_state = 'linked'",
            (self.system, external_id, contact_id, remote_hash))


def reconcile(conn, system: str, payloads: list[dict], apply: bool = False) -> dict:
    """Convenience entry: build RemoteRecords from raw payload dicts (each with
    an 'external_id') and plan (default) or apply them for `system`."""
    remotes = [
        RemoteRecord(external_id=str(p.get("external_id") or p.get("id") or i),
                     payload=p, modified_at=p.get("modified_at"))
        for i, p in enumerate(payloads)
    ]
    r = Reconciler(conn, system)
    return r.apply(remotes) if apply else r.plan(remotes)
