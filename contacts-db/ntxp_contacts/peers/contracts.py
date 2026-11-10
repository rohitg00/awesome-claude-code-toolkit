"""Watch NTXP Master Contracts and inject its facts into contacts.

Polls the Master Contracts HTTP API (`GET /api/changes?since=` as a cheap delta probe, then
`GET /api/contracts`), links each contract's owner entity to our organizations by normalized
name, caches the facts (number, type, coefficient, co-op fee, expiry, executed, signed-PDF link)
and tags the organization `Contract <no>` so the live page can filter contacts by contract.
It never creates organizations or contacts from contract data and never writes to Master Contracts.
"""
from __future__ import annotations

import json
import urllib.request

from .. import normalize as N
from ..db.repository import Repository
from ..model import Tag
from . import context as ctx
from .events import get_cursor, set_cursor

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Peers talk to fixed https hosts; a redirect would carry the bearer/secret elsewhere (or inward)."""
    def redirect_request(self, *a, **k):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


LABEL_PREFIX = "Contract "


def _get(peer, path: str, timeout: float = 10.0):
    req = urllib.request.Request(peer.url.rstrip("/") + path, headers={
        "Accept": "application/json", "User-Agent": "ntxp-contacts/1",
        "Authorization": f"Bearer svc.contacts.{peer.secret}"})
    with _OPENER.open(req, timeout=timeout) as r:
        return json.load(r)


def pull(conn, peer, force: bool = False, get=_get) -> dict:
    cur = get_cursor(conn, peer.name, "contracts_seq")
    probe = get(peer, f"/api/changes?since={int(cur or 0)}")
    latest = int(probe.get("latest_seq", 0))
    if cur is not None and not probe.get("changed") and not force:
        return {"skipped": "no changes", "seq": latest}
    body = get(peer, "/api/contracts")
    contracts = body.get("contracts") if isinstance(body, dict) else None
    if not isinstance(contracts, list):
        return {"skipped": "unexpected response from peer", "seq": latest}
    if not contracts and not force:
        had = conn.execute("SELECT COUNT(*) FROM peer_context WHERE peer=? AND kind='contract'",
                           (peer.name,)).fetchone()[0]
        if had:
            # One empty answer is indistinguishable from a proxy/peer fault: keep the cache, and only accept
            # "no contracts" when the peer says so on two polls in a row (so a real wind-down still propagates).
            seen = int(get_cursor(conn, peer.name, "contracts_empty") or 0)
            if seen < 1:
                set_cursor(conn, peer.name, "contracts_empty", seen + 1)
                conn.commit()
                return {"skipped": "peer returned no contracts; kept cached (confirm on next poll)", "seq": latest}
    set_cursor(conn, peer.name, "contracts_empty", 0)
    repo = Repository(conn)
    keep, matched, wanted_labels = set(), 0, {}
    for c in contracts:
        ref = str(c["contract_id"])
        keep.add(ref)
        owner = (c.get("owner_entity") or "").strip()
        org_id = repo.find_org_by_norm(N.org_name_norm(owner)) if owner else None
        matched += 1 if org_id else 0
        ctx.upsert(conn, peer.name, "contract", ref, {
            "contract_id": c["contract_id"], "number": c.get("contract_no"), "title": c.get("contract_title"),
            "type": c.get("contract_type"), "owner": owner or None,
            "coefficient": c.get("coefficient_multiplier"), "cooperative_fee": c.get("cooperative_fee"),
            "expires": c.get("expiration_date"), "executed": bool(c.get("is_executed")),
            "scope": c.get("allowable_scope"), "pdf_url": c.get("pdf_url"),
            "link": f"{peer.url.rstrip('/')}/contract?id={c['contract_id']}"}, org_id=org_id)
        if org_id and (c.get("contract_no") or c.get("contract_title")):
            wanted_labels.setdefault(org_id, set()).add(LABEL_PREFIX + str(c.get("contract_no") or c.get("contract_title"))[:60])
    removed = ctx.delete_missing(conn, peer.name, "contract", keep)
    _sync_labels(conn, repo, wanted_labels)
    set_cursor(conn, peer.name, "contracts_seq", latest)
    conn.commit()
    return {"contracts": len(contracts), "linked_to_orgs": matched, "removed": removed, "seq": latest}


def _sync_labels(conn, repo: Repository, wanted: dict[int, set[str]]) -> None:
    """Org-level `Contract <no>` labels: add the wanted ones, drop ones no longer backed by a contract."""
    for org_id, labels in wanted.items():
        for l in labels:
            repo.add_tag(Tag("label", l), "org", org_id)
    existing = conn.execute(
        "SELECT et.entity_id AS org_id, t.value AS value, t.tag_id AS tag_id FROM entity_tags et "
        "JOIN tags t ON t.tag_id=et.tag_id WHERE et.entity_type='org' AND t.kind='label' AND t.value LIKE ?",
        (LABEL_PREFIX + "%",)).fetchall()
    for r in existing:
        if r["value"] not in wanted.get(r["org_id"], set()):
            conn.execute("DELETE FROM entity_tags WHERE tag_id=? AND entity_type='org' AND entity_id=?",
                         (r["tag_id"], r["org_id"]))
