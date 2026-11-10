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

LABEL_PREFIX = "Contract "


def _get(peer, path: str, timeout: float = 10.0):
    req = urllib.request.Request(peer.url.rstrip("/") + path, headers={
        "Accept": "application/json", "User-Agent": "ntxp-contacts/1",
        "Authorization": f"Bearer svc.contacts.{peer.secret}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def pull(conn, peer, force: bool = False, get=_get) -> dict:
    cur = get_cursor(conn, peer.name, "contracts_seq")
    probe = get(peer, f"/api/changes?since={int(cur or 0)}")
    latest = int(probe.get("latest_seq", 0))
    if cur is not None and not probe.get("changed") and not force:
        return {"skipped": "no changes", "seq": latest}
    contracts = get(peer, "/api/contracts").get("contracts", [])
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
