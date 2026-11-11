"""Jobs / sales ingestion for the per-contract profile.

NTXP's jobs live in JobTread. Rather than couple this package to a JobTread
client, ingestion is **MCP-mediated** (same pattern as the contacts CRM sync):
a Claude agent queries the JobTread MCP, then hands the rows here to be cached
into the local ``jobs`` table. The profile screen and any other tool then poll
the cache — fast, offline-capable, and a single source of truth for "jobs done
under this contract" and "total sales".

A row handed in is just a dict; ``coerce_job`` maps common JobTread-ish field
names onto our Job model so the agent doesn't have to reshape anything.
"""
from __future__ import annotations

from typing import Any, Iterable

from . import normalize as N
from .db.repository import Repository
from .model import Job

# Accept several aliases per field so callers (or JobTread exports) can pass
# whatever they have.
_ALIASES = {
    "contract_no": ("contract_no", "contract", "contract_number", "rfp", "rfp_no"),
    "name": ("name", "job_name", "title", "project"),
    "customer": ("customer", "client", "owner", "account"),
    "status": ("status", "stage", "state"),
    "contract_value": ("contract_value", "value", "amount", "budget", "total"),
    "sales_amount": ("sales_amount", "sales", "invoiced", "revenue", "billed"),
    "external_id": ("external_id", "id", "job_id", "jobtread_id"),
}


# Lowercased set of every key _pick may consume, so attrs excludes them
# regardless of the source header's casing.
_CONSUMED_KEYS = {a for al in _ALIASES.values() for a in al} | {"source"}


def _pick(low: dict, keys: tuple[str, ...]):
    """First non-empty value among the (lowercase) alias keys. `low` is a
    once-built case-folded view of the row, so each lookup is an O(1) dict hit."""
    for k in keys:
        v = low.get(k)
        if v not in (None, ""):
            return v
    return None


def coerce_job(row: dict, default_contract_no: str | None = None) -> Job | None:
    low = {k.lower(): v for k, v in row.items()}   # one case-folding pass
    contract_no = _pick(low, _ALIASES["contract_no"]) or default_contract_no
    name = _pick(low, _ALIASES["name"])
    if not contract_no or not name:
        return None
    return Job(
        contract_no=str(contract_no),
        name=str(name),
        customer=_opt(_pick(low, _ALIASES["customer"])),
        status=_opt(_pick(low, _ALIASES["status"])),
        contract_value=N.normalize_money(_pick(low, _ALIASES["contract_value"])),
        sales_amount=N.normalize_money(_pick(low, _ALIASES["sales_amount"])),
        external_id=_opt(_pick(low, _ALIASES["external_id"])),
        source=str(row.get("source") or "jobtread"),
        # Keep only genuinely-extra columns. Compare case-insensitively (and
        # against 'source') so a capitalized header like "Name" that _pick
        # already consumed isn't also duplicated into attrs.
        attrs={k: v for k, v in row.items()
               if k.lower() not in _CONSUMED_KEYS},
    )


def sync_jobs(repo: Repository, rows: Iterable[dict],
              default_contract_no: str | None = None) -> dict:
    """Upsert a batch of job rows into the cache. Idempotent on
    (source, external_id). Returns a small summary."""
    upserted = 0
    skipped = 0
    for row in rows:
        job = coerce_job(row, default_contract_no)
        if job is None:
            skipped += 1
            continue
        repo.upsert_job(job)
        upserted += 1
    repo.conn.commit()
    return {"upserted": upserted, "skipped": skipped}


def _opt(v: Any):
    return None if v in (None, "") else str(v)
