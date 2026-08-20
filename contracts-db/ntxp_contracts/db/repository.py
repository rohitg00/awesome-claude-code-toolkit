"""Thin typed persistence layer over sqlite3. Holds all SQL.

The importer, CLI, web API and MCP server all go through here; none of them
touch SQL directly. Upserts key on natural unique indexes so re-imports are
idempotent, and ``update_field`` is the single chokepoint for the dashboard's
instant, field-level, conflict-light saves.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .. import normalize as N
from ..model import Contract, Job, OwnerEntity

# Columns an editor may change inline from the dashboard. Anything not here is
# rejected by update_field — the API never trusts an arbitrary column name.
EDITABLE_FIELDS = {
    "contract_title", "contract_no", "contract_type", "owner_entity",
    "recipient", "location", "estimated_budget", "award_date", "duration",
    "expiration_date", "coefficient_multiplier", "cooperative_fee",
    "allowable_scope", "notes", "pdf_url", "is_executed",
}
# Free-text columns whose contents feed the FTS index — listed once and used by
# both update_field (when to reindex) and _reindex (what to index), so they
# can't drift apart.
_FTS_FIELDS = ("contract_title", "contract_no", "owner_entity", "location",
               "allowable_scope", "notes")
# How each editable field is coerced before storage.
_COERCE = {
    "estimated_budget": N.normalize_money,
    "coefficient_multiplier": N.normalize_float,
    "award_date": N.normalize_date,
    "expiration_date": N.normalize_date,
    "is_executed": lambda v: 1 if N.truthy(v) or v is True else 0,
}


class ConflictError(Exception):
    """Raised when an inline save targets a stale revision (someone else saved
    the same row first). The API turns this into a 409 + the fresh row so the
    dashboard can reconcile that one cell without losing the editor's other work."""


class Repository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._not_null_cache: set[str] | None = None

    def _not_null_cols(self) -> set[str]:
        """NOT NULL columns of `contracts`, read from the schema (cached). Used
        to reject clearing a required field rather than writing NULL and hitting
        an uncaught IntegrityError — and it can never drift from the schema."""
        if self._not_null_cache is None:
            self._not_null_cache = {
                r["name"] for r in self.conn.execute("PRAGMA table_info(contracts)")
                if r["notnull"]
            }
        return self._not_null_cache

    # -- owner entities -----------------------------------------------------
    def upsert_owner(self, owner: OwnerEntity, actor: str = "system") -> int:
        name_norm = owner.name_norm or N.norm_key(owner.name)
        row = self.conn.execute(
            "SELECT owner_id FROM owner_entities WHERE name_norm = ?", (name_norm,)
        ).fetchone()
        if row:
            oid = int(row["owner_id"])
            self.conn.execute(
                "UPDATE owner_entities SET "
                "website = COALESCE(?, website), main_phone = COALESCE(?, main_phone), "
                "customer_service_phone = COALESCE(?, customer_service_phone), "
                "accounting_phone = COALESCE(?, accounting_phone), "
                "email = COALESCE(?, email), address = COALESCE(?, address), "
                "updated_at = datetime('now') WHERE owner_id = ?",
                (N.normalize_website(owner.website), N.normalize_phone(owner.main_phone),
                 N.normalize_phone(owner.customer_service_phone),
                 N.normalize_phone(owner.accounting_phone), owner.email,
                 owner.address, oid),
            )
            return oid
        cur = self.conn.execute(
            "INSERT INTO owner_entities(name, name_norm, website, main_phone, "
            "customer_service_phone, accounting_phone, email, address, attrs) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (owner.name, name_norm, N.normalize_website(owner.website),
             N.normalize_phone(owner.main_phone),
             N.normalize_phone(owner.customer_service_phone),
             N.normalize_phone(owner.accounting_phone), owner.email, owner.address,
             json.dumps(owner.attrs, sort_keys=True)),
        )
        return int(cur.lastrowid)

    def get_owner(self, owner_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM owner_entities WHERE owner_id = ?", (owner_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None

    def get_owner_by_name(self, name: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM owner_entities WHERE name_norm = ?", (N.norm_key(name),)
        ).fetchone()
        return _row_to_dict(row) if row else None

    # -- contracts ----------------------------------------------------------
    def upsert_contract(self, c: Contract, actor: str = "import") -> tuple[int, bool]:
        """Idempotent create-or-fill keyed on the normalized contract number
        (falling back to the title when there is no number). Returns
        (contract_id, is_new)."""
        no_norm = N.contract_no_norm(c.contract_no) if c.contract_no else None
        owner_id = None
        if c.owner_entity:
            owner_id = self.upsert_owner(OwnerEntity(name=c.owner_entity), actor)

        existing = None
        if no_norm:
            existing = self.conn.execute(
                "SELECT contract_id FROM contracts WHERE contract_no_norm = ? "
                "AND is_deleted = 0 LIMIT 1", (no_norm,)
            ).fetchone()
        if not existing:
            existing = self.conn.execute(
                "SELECT contract_id FROM contracts WHERE contract_title = ? "
                "AND COALESCE(contract_no_norm,'') = COALESCE(?, '') AND is_deleted = 0 LIMIT 1",
                (c.contract_title, no_norm),
            ).fetchone()

        if existing:
            cid = int(existing["contract_id"])
            # Fill blanks only; never clobber a value an editor curated.
            self.conn.execute(
                "UPDATE contracts SET "
                "contract_type = COALESCE(contract_type, ?), "
                "owner_id = COALESCE(owner_id, ?), owner_entity = COALESCE(owner_entity, ?), "
                "location = COALESCE(location, ?), estimated_budget = COALESCE(estimated_budget, ?), "
                "award_date = COALESCE(award_date, ?), duration = COALESCE(duration, ?), "
                "expiration_date = COALESCE(expiration_date, ?), "
                "coefficient_multiplier = COALESCE(coefficient_multiplier, ?), "
                "cooperative_fee = COALESCE(cooperative_fee, ?), "
                "allowable_scope = COALESCE(allowable_scope, ?), notes = COALESCE(notes, ?), "
                "pdf_url = COALESCE(pdf_url, ?), updated_at = datetime('now') "
                "WHERE contract_id = ?",
                (c.contract_type, owner_id, c.owner_entity, c.location,
                 c.estimated_budget, c.award_date, c.duration, c.expiration_date,
                 c.coefficient_multiplier, c.cooperative_fee, c.allowable_scope,
                 c.notes, c.pdf_url, cid),
            )
            # Log the touch so dashboards polling changes_since() refresh after
            # an import (callers reach this branch only for new/changed rows).
            self.conn.execute(
                "INSERT INTO change_log(contract_id, op, actor) VALUES (?, 'update', ?)",
                (cid, actor),
            )
            self._reindex(cid)
            return cid, False

        cur = self.conn.execute(
            "INSERT INTO contracts(contract_title, contract_no, contract_no_norm, "
            "contract_type, owner_id, owner_entity, recipient, location, estimated_budget, "
            "award_date, duration, expiration_date, coefficient_multiplier, cooperative_fee, "
            "allowable_scope, notes, pdf_url, is_executed, attrs) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c.contract_title, c.contract_no, no_norm, c.contract_type, owner_id,
             c.owner_entity, c.recipient, c.location, c.estimated_budget, c.award_date,
             c.duration, c.expiration_date, c.coefficient_multiplier, c.cooperative_fee,
             c.allowable_scope, c.notes, c.pdf_url, 1 if c.is_executed else 0,
             json.dumps(c.attrs, sort_keys=True)),
        )
        cid = int(cur.lastrowid)
        self.conn.execute(
            "INSERT INTO change_log(contract_id, op, actor) VALUES (?, 'insert', ?)",
            (cid, actor),
        )
        self._reindex(cid)
        return cid, True

    def update_field(self, contract_id: int, field: str, value: Any,
                     actor: str = "web", expected_rev: int | None = None) -> dict:
        """Save one field. The chokepoint for inline dashboard edits.

        Concurrency model: editors PATCH a single field at a time, so two people
        editing *different* cells never conflict. For the *same* cell, an
        optional ``expected_rev`` enables optimistic locking — a stale write
        raises ConflictError instead of silently overwriting fresher data.
        Without expected_rev it is last-write-wins (fine for a small team)."""
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"field not editable: {field}")
        row = self.conn.execute(
            f"SELECT {field} AS cur, rev FROM contracts WHERE contract_id = ? AND is_deleted = 0",
            (contract_id,),
        ).fetchone()
        if not row:
            raise KeyError(contract_id)
        if expected_rev is not None and int(row["rev"]) != int(expected_rev):
            raise ConflictError(self.get_contract(contract_id))

        coerced = _COERCE.get(field, _default_coerce)(value)
        if coerced is None and field in self._not_null_cols():
            raise ValueError(f"{field} cannot be empty")
        old = row["cur"]

        # (column, value) pairs: the field itself plus any derived columns it
        # drives. One list keeps the SET clause and its params in lockstep.
        sets: list[tuple[str, Any]] = [(field, coerced)]
        if field == "owner_entity" and coerced:
            sets.append(("owner_id", self.upsert_owner(OwnerEntity(name=str(coerced)), actor)))
        if field == "contract_no":
            sets.append(("contract_no_norm", N.contract_no_norm(coerced) if coerced else None))

        set_sql = ", ".join(f"{col} = ?" for col, _ in sets)
        self.conn.execute(
            f"UPDATE contracts SET {set_sql}, rev = rev + 1, "
            "updated_at = datetime('now') WHERE contract_id = ?",
            [v for _, v in sets] + [contract_id],
        )
        self.conn.execute(
            "INSERT INTO change_log(contract_id, field, old_value, new_value, op, actor) "
            "VALUES (?,?,?,?, 'update', ?)",
            (contract_id, field, _s(old), _s(coerced), actor),
        )
        if field in _FTS_FIELDS:
            self._reindex(contract_id)
        self.conn.commit()
        return self.get_contract(contract_id)

    def create_contract(self, title: str = "Untitled Contract", actor: str = "web") -> dict:
        cid, _ = self.upsert_contract(Contract(contract_title=title), actor)
        self.conn.commit()
        return self.get_contract(cid)

    def soft_delete(self, contract_id: int, actor: str = "web") -> None:
        self.conn.execute(
            "UPDATE contracts SET is_deleted = 1, updated_at = datetime('now') "
            "WHERE contract_id = ?", (contract_id,)
        )
        self.conn.execute(
            "INSERT INTO change_log(contract_id, op, actor) VALUES (?, 'delete', ?)",
            (contract_id, actor),
        )
        self.conn.commit()

    def list_contracts(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM contracts WHERE is_deleted = 0 "
            "ORDER BY (expiration_date IS NULL), expiration_date, contract_title"
        ).fetchall()
        return [_contract_row(r) for r in rows]

    def get_contract(self, contract_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM contracts WHERE contract_id = ? AND is_deleted = 0",
            (contract_id,),
        ).fetchone()
        if not row:
            return None
        return _contract_row(row)

    def get_contract_by_no(self, contract_no: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM contracts WHERE contract_no_norm = ? AND is_deleted = 0 LIMIT 1",
            (N.contract_no_norm(contract_no),),
        ).fetchone()
        return _contract_row(row) if row else None

    def get_profile(self, contract_id: int) -> dict | None:
        """Everything the single-contract screen needs in one call: the
        contract, its owner entity (contact info), the job list and totals."""
        c = self.get_contract(contract_id)
        if not c:
            return None
        owner = self.get_owner(c["owner_id"]) if c.get("owner_id") else None
        jobs = self.list_jobs(contract_id)
        total_sales = sum(j["sales_amount"] or 0 for j in jobs)
        total_value = sum(j["contract_value"] or 0 for j in jobs)
        return {
            "contract": c,
            "owner": owner,
            "jobs": jobs,
            "totals": {
                "job_count": len(jobs),
                "total_sales": total_sales,
                "total_contract_value": total_value,
            },
        }

    # -- jobs ---------------------------------------------------------------
    def upsert_job(self, job: Job) -> int:
        contract = self.get_contract_by_no(job.contract_no)
        contract_id = contract["contract_id"] if contract else None
        row = None
        if job.external_id:
            row = self.conn.execute(
                "SELECT job_id FROM jobs WHERE source = ? AND external_id = ?",
                (job.source, job.external_id),
            ).fetchone()
        if row:
            jid = int(row["job_id"])
            self.conn.execute(
                "UPDATE jobs SET contract_id = ?, name = ?, customer = ?, status = ?, "
                "contract_value = ?, sales_amount = ?, attrs = ?, synced_at = datetime('now') "
                "WHERE job_id = ?",
                (contract_id, job.name, job.customer, job.status, job.contract_value,
                 job.sales_amount, json.dumps(job.attrs, sort_keys=True), jid),
            )
            return jid
        cur = self.conn.execute(
            "INSERT INTO jobs(contract_id, name, customer, status, contract_value, "
            "sales_amount, source, external_id, attrs) VALUES (?,?,?,?,?,?,?,?,?)",
            (contract_id, job.name, job.customer, job.status, job.contract_value,
             job.sales_amount, job.source, job.external_id,
             json.dumps(job.attrs, sort_keys=True)),
        )
        return int(cur.lastrowid)

    def list_jobs(self, contract_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM jobs WHERE contract_id = ? ORDER BY name", (contract_id,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    # -- search / stats -----------------------------------------------------
    def search(self, query: str, limit: int = 50) -> list[dict]:
        q = (query or "").strip()
        if not q:
            return self.list_contracts()[:limit]
        try:
            rows = self.conn.execute(
                "SELECT c.* FROM contracts_fts f JOIN contracts c "
                "ON c.contract_id = f.contract_id "
                "WHERE contracts_fts MATCH ? AND c.is_deleted = 0 LIMIT ?",
                (_fts_query(q), limit),
            ).fetchall()
            if rows:
                return [_contract_row(r) for r in rows]
        except sqlite3.OperationalError:
            pass
        like = f"%{q}%"
        rows = self.conn.execute(
            "SELECT * FROM contracts WHERE is_deleted = 0 AND ("
            "contract_title LIKE ? OR contract_no LIKE ? OR owner_entity LIKE ? "
            "OR location LIKE ? OR allowable_scope LIKE ?) LIMIT ?",
            (like, like, like, like, like, limit),
        ).fetchall()
        return [_contract_row(r) for r in rows]

    def stats(self) -> dict:
        c = self.conn.execute(
            "SELECT COUNT(*) n, SUM(is_executed=0) unexecuted FROM contracts WHERE is_deleted=0"
        ).fetchone()
        by_type = {
            r["contract_type"] or "Unclassified": r["n"]
            for r in self.conn.execute(
                "SELECT contract_type, COUNT(*) n FROM contracts WHERE is_deleted=0 "
                "GROUP BY contract_type"
            ).fetchall()
        }
        jobs = self.conn.execute("SELECT COUNT(*) n FROM jobs").fetchone()["n"]
        return {
            "contracts": c["n"],
            "unexecuted": c["unexecuted"] or 0,
            "by_type": by_type,
            "jobs": jobs,
        }

    def changes_since(self, seq: int) -> dict:
        """Lightweight delta probe for the dashboard's live polling."""
        row = self.conn.execute("SELECT COALESCE(MAX(seq),0) m FROM change_log").fetchone()
        return {"latest_seq": int(row["m"]), "changed": int(row["m"]) > seq}

    # -- internals ----------------------------------------------------------
    def _reindex(self, contract_id: int) -> None:
        row = self.conn.execute(
            f"SELECT {', '.join(_FTS_FIELDS)} FROM contracts WHERE contract_id = ?",
            (contract_id,),
        ).fetchone()
        if not row:
            return
        text = " ".join(str(v) for v in tuple(row) if v)
        self.conn.execute("DELETE FROM contracts_fts WHERE contract_id = ?", (contract_id,))
        self.conn.execute(
            "INSERT INTO contracts_fts(contract_id, text) VALUES (?, ?)",
            (contract_id, text),
        )


# --- row helpers -------------------------------------------------------------
def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if "attrs" in d and isinstance(d["attrs"], str):
        try:
            d["attrs"] = json.loads(d["attrs"])
        except Exception:
            d["attrs"] = {}
    return d


def _contract_row(row: sqlite3.Row) -> dict:
    d = _row_to_dict(row)
    d["is_executed"] = bool(d.get("is_executed"))
    return d


def _default_coerce(v: Any) -> Any:
    """Text fields: trim and treat blank/whitespace-only as NULL (matching the
    importer's strip semantics, so inline edits and imports agree)."""
    if isinstance(v, str):
        return v.strip() or None
    return v


def _s(v: Any) -> str | None:
    return None if v is None else str(v)


def _fts_query(q: str) -> str:
    terms = re.findall(r"\w+", q)
    return " ".join(f"{t}*" for t in terms) if terms else q
