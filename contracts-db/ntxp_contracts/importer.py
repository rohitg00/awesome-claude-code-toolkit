"""Idempotent CSV importer for the contract log.

Re-running an import never duplicates: every source row is anchored by
``(source, source_pk, row_hash)`` in ``source_records``; unchanged rows are
skipped, and contract upserts fill blanks without clobbering curated fields.

Header matching is forgiving — columns are matched case-insensitively against a
set of aliases — so an export from a spreadsheet "Contract Log" loads without
hand-editing headers.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from . import normalize as N
from .config import DEFAULT_RECIPIENT
from .db.repository import Repository
from .model import Contract

# Map our model fields to the header aliases we accept in a CSV.
_COLS = {
    "contract_title": ("contract title", "title", "contract", "name"),
    "contract_no": ("contract / rfp #", "contract/rfp #", "contract #", "contract no",
                    "contract number", "rfp #", "rfp", "number"),
    "contract_type": ("type of contract", "type", "contract type"),
    "owner_entity": ("owner entity", "owner", "issuing entity", "authority"),
    "recipient": ("recipient",),
    "location": ("location", "region"),
    "estimated_budget": ("estimated budget", "budget", "est budget", "est. budget"),
    "award_date": ("award date", "awarded", "date awarded"),
    "duration": ("duration", "term"),
    "expiration_date": ("expiration date", "expiration", "expires", "exp date", "exp"),
    "coefficient_multiplier": ("coefficient multiplier", "coefficient", "coeff",
                               "multiplier"),
    "cooperative_fee": ("cooperative fee", "co-op fee", "coop fee", "fee"),
    "allowable_scope": ("allowable scope terms", "allowable scope", "scope", "scope terms"),
    "notes": ("notes", "note", "comments"),
    "pdf_url": ("pdf link", "pdf", "signed copy", "signed pdf", "pdf url", "link"),
    "is_executed": ("executed", "is executed", "signed", "status"),
}


def _build_header_index(fieldnames: list[str]) -> dict[str, str]:
    """Return {model_field: actual_csv_header}."""
    lower = {h.lower().strip(): h for h in fieldnames if h}
    out: dict[str, str] = {}
    for field, aliases in _COLS.items():
        for a in aliases:
            if a in lower:
                out[field] = lower[a]
                break
    return out


def _row_hash(row: dict) -> str:
    return hashlib.sha256(
        json.dumps(row, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def import_csv(repo: Repository, path: str | Path, source: str = "csv") -> dict:
    path = Path(path)
    created = updated = skipped = 0
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        hidx = _build_header_index(reader.fieldnames or [])
        if "contract_title" not in hidx:
            raise ValueError(
                "CSV needs a contract title column. Found headers: "
                + ", ".join(reader.fieldnames or [])
            )
        for raw in reader:
            title = (raw.get(hidx["contract_title"]) or "").strip()
            if not title:
                continue
            rh = _row_hash(raw)
            source_pk = (raw.get(hidx.get("contract_no", "")) or title).strip()
            seen = repo.conn.execute(
                "SELECT 1 FROM source_records WHERE source=? AND source_pk=? AND row_hash=?",
                (source, source_pk, rh),
            ).fetchone()
            if seen:
                repo.conn.execute(
                    "UPDATE source_records SET last_seen_at=datetime('now') "
                    "WHERE source=? AND source_pk=? AND row_hash=?",
                    (source, source_pk, rh),
                )
                skipped += 1
                continue

            c = Contract(
                contract_title=title,
                contract_no=_g(raw, hidx, "contract_no"),
                contract_type=_g(raw, hidx, "contract_type"),
                owner_entity=_g(raw, hidx, "owner_entity"),
                recipient=_g(raw, hidx, "recipient") or DEFAULT_RECIPIENT,
                location=_g(raw, hidx, "location"),
                estimated_budget=N.normalize_money(_g(raw, hidx, "estimated_budget")),
                award_date=N.normalize_date(_g(raw, hidx, "award_date")),
                duration=_g(raw, hidx, "duration"),
                expiration_date=N.normalize_date(_g(raw, hidx, "expiration_date")),
                coefficient_multiplier=N.normalize_float(
                    _g(raw, hidx, "coefficient_multiplier")),
                cooperative_fee=_g(raw, hidx, "cooperative_fee"),
                allowable_scope=_g(raw, hidx, "allowable_scope"),
                notes=_g(raw, hidx, "notes"),
                pdf_url=_g(raw, hidx, "pdf_url"),
                is_executed=N.truthy(_g(raw, hidx, "is_executed")),
                source=source,
                source_pk=source_pk,
            )
            cid, is_new = repo.upsert_contract(c, actor=f"import:{source}")
            repo.conn.execute(
                "INSERT OR REPLACE INTO source_records"
                "(source, source_pk, row_hash, raw, contract_id) VALUES (?,?,?,?,?)",
                (source, source_pk, rh, json.dumps(raw, default=str), cid),
            )
            created += int(is_new)
            updated += int(not is_new)
    repo.conn.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


def _g(raw: dict, hidx: dict, field: str):
    h = hidx.get(field)
    if not h:
        return None
    v = raw.get(h)
    return v.strip() if isinstance(v, str) else v
