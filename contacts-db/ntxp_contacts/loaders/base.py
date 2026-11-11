"""SourceLoader protocol + the idempotent import pipeline.

The pipeline is the heart of "update independently": each source row is
content-hashed and tracked in `source_records`, so re-importing an unchanged
file is a no-op, and a changed row updates the same canonical entity rather
than duplicating it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Protocol

from ..db.repository import Repository
from ..model import CanonicalRecord
from ..resolve import Resolver


class SourceLoader(Protocol):
    source: str

    def rows(self, path: str | Path) -> Iterator[dict]:
        """Yield raw dict rows from the source file."""
        ...

    def to_canonical(self, row: dict) -> CanonicalRecord | None:
        """Map a raw row to a normalized CanonicalRecord (or None to skip)."""
        ...


@dataclass
class ImportStats:
    source: str
    rows: int = 0
    skipped_unchanged: int = 0
    updated: int = 0
    new_contacts: int = 0
    new_orgs_seen: int = 0
    needs_review: int = 0
    staged: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "errors"} | {
            "errors": len(self.errors)
        }


def _row_hash(rec: CanonicalRecord) -> str:
    payload = {
        "org": rec.org_name_norm,
        "name": rec.name_norm,
        "title": rec.title,
        "emails": sorted(e.email_norm for e in rec.emails),
        "phones": sorted(p.phone_e164 or p.phone_raw for p in rec.phones),
        "addr": sorted(a.addr_norm for a in (rec.addresses + rec.org_addresses)),
        "tags": sorted(f"{t.kind}:{t.value}" for t in (rec.tags + rec.org_tags)),
        "attrs": {**rec.org_attrs, **rec.contact_attrs},
    }
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _rec_payload(rec: CanonicalRecord) -> dict:
    """Serializable snapshot of a CanonicalRecord for the staging queue."""
    return {
        "source": rec.source,
        "source_pk": rec.source_pk,
        "org_name": rec.org_name,
        "full_name": rec.full_name,
        "first_name": rec.first_name,
        "last_name": rec.last_name,
        "title": rec.title,
        "emails": [e.email for e in rec.emails],
        "phones": [p.phone_raw for p in rec.phones],
        "tags": [f"{t.kind}:{t.value}" for t in (rec.tags + rec.org_tags)],
        "contact_attrs": rec.contact_attrs,
        "raw": rec.raw,
    }


def _attach_comms(repo: Repository, rec: CanonicalRecord,
                  contact_id: int | None, org_id: int | None) -> None:
    for e in rec.emails:
        repo.add_email(e, contact_id, None)
    for p in rec.phones:
        repo.add_phone(p, contact_id, None)
    for a in rec.addresses:
        repo.add_address(a, contact_id, None)
    for t in rec.tags:
        if contact_id:
            repo.add_tag(t, "contact", contact_id)
    # Org-level comms
    if org_id:
        for e in rec.org_emails:
            repo.add_email(e, None, org_id)
        for p in rec.org_phones:
            repo.add_phone(p, None, org_id)
        for a in rec.org_addresses:
            repo.add_address(a, None, org_id)
        for t in rec.org_tags:
            repo.add_tag(t, "org", org_id)


def import_records(conn, loader: SourceLoader, path: str | Path,
                   origin: str = "import", dry_run: bool = False,
                   stage: bool = False) -> ImportStats:
    """Run one source file through the idempotent pipeline.

    When `stage` is True (e.g. OCR-derived sources), rows are quarantined in
    `staging_records` for human review instead of resolved into canonical
    tables.
    """
    repo = Repository(conn)
    repo.defer_fts = True   # bulk-rebuild the FTS index once at the end
    resolver = Resolver(repo)
    stats = ImportStats(source=loader.source)

    for raw in loader.rows(path):
        stats.rows += 1
        try:
            rec = loader.to_canonical(raw)
        except Exception as exc:  # never let one bad row abort the file
            stats.errors.append(f"row {stats.rows}: {exc}")
            continue
        if rec is None or (not rec.has_contact and not rec.has_org):
            continue

        rhash = _row_hash(rec)

        if stage:
            confidence = rec.contact_attrs.get("_confidence")
            repo.stage_record(loader.source, rhash, _rec_payload(rec),
                              confidence if isinstance(confidence, (int, float)) else None)
            stats.staged += 1
            continue

        existing = repo.find_source_record(loader.source, rec.source_pk, rhash)
        if existing is not None:
            repo.touch_source_record(existing["source_record_id"])
            stats.skipped_unchanged += 1
            continue

        prior = repo.find_source_by_pk(loader.source, rec.source_pk)
        org_id = resolver.resolve_org(rec, origin)
        decision = resolver.resolve_contact(rec, org_id, origin)
        _attach_comms(repo, rec, decision.contact_id, org_id)
        repo.record_source(loader.source, rec.source_pk, rhash, rec.raw,
                           decision.contact_id, org_id)

        if prior is not None:
            stats.updated += 1
        elif decision.is_new:
            stats.new_contacts += 1
        else:
            stats.updated += 1
        if decision.needs_review:
            stats.needs_review += 1

    if dry_run:
        conn.rollback()
    else:
        repo.rebuild_fts()
        conn.commit()
    return stats


# Registry populated by the concrete loader modules.
LOADERS: dict[str, SourceLoader] = {}


def register(loader: SourceLoader) -> SourceLoader:
    LOADERS[loader.source] = loader
    return loader


def get_loader(source: str) -> SourceLoader:
    from . import tips, buildingconnectd, approved_subs, luncheon, cjp_pdf  # noqa: F401
    if source not in LOADERS:
        raise KeyError(f"unknown source '{source}'. Known: {sorted(LOADERS)}")
    return LOADERS[source]
