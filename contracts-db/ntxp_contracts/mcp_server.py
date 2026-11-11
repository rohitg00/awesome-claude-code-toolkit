"""MCP server exposing the Master Contracts DB as tools for NTXP's Claude tools.

Run with ``ntxp-contracts mcp-serve`` (stdio). Other NTXP tools register this in
their MCP config and poll the single source of truth directly — coefficient,
cooperative fee, expiration, allowable scope, the signed PDF link, owner-entity
contact info, and the jobs/sales roll-up — instead of re-parsing spreadsheets.
"""
from __future__ import annotations

import json

from .db import connect, migrate
from .db.repository import Repository
from .model import Contract


def build_server(db_override: str | None = None):
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "The 'mcp' package is required. Install with: "
            "pip install 'ntxp-contracts[mcp]'"
        ) from exc

    mcp = FastMCP("ntxp-contracts")

    def _repo():
        c = connect(db_override)
        migrate(c)
        return Repository(c)

    @mcp.tool()
    def search_contracts(query: str = "", limit: int = 50) -> str:
        """Search the contract log by title, number, owner, location, or scope.
        Empty query returns the full log. This is the primary reference-data poll."""
        return json.dumps(_repo().search(query, limit=limit), default=str)

    @mcp.tool()
    def get_contract(contract_id: int = 0, contract_no: str = "") -> str:
        """Fetch one contract's full profile — terms, owner-entity contact info,
        jobs done under it, and total sales — by id or by contract/RFP number."""
        repo = _repo()
        if not contract_id and contract_no:
            c = repo.get_contract_by_no(contract_no)
            if not c:
                return json.dumps({"error": "not found"})
            contract_id = c["contract_id"]
        return json.dumps(repo.get_profile(contract_id), default=str)

    @mcp.tool()
    def reference_lookup(contract_no: str, fields: str = "") -> str:
        """Lean key/value poll for another tool: return just the requested
        fields (comma-separated, e.g. 'coefficient_multiplier,cooperative_fee,
        expiration_date') for a contract number. Empty `fields` returns the
        commercial essentials."""
        repo = _repo()
        c = repo.get_contract_by_no(contract_no)
        if not c:
            return json.dumps({"error": "not found", "contract_no": contract_no})
        wanted = [f.strip() for f in fields.split(",") if f.strip()] or [
            "contract_title", "contract_type", "coefficient_multiplier",
            "cooperative_fee", "expiration_date", "is_executed", "pdf_url",
            "allowable_scope", "owner_entity"]
        return json.dumps({k: c.get(k) for k in wanted}, default=str)

    @mcp.tool()
    def list_expiring(within_days: int = 90) -> str:
        """List contracts expiring within N days (renewal radar for other tools)."""
        import datetime as dt
        cutoff = (dt.date.today() + dt.timedelta(days=within_days)).isoformat()
        rows = [c for c in _repo().list_contracts()
                if c.get("expiration_date") and c["expiration_date"] <= cutoff]
        return json.dumps(rows, default=str)

    @mcp.tool()
    def upsert_contract(contract_title: str, contract_no: str = "",
                        contract_type: str = "", owner_entity: str = "",
                        location: str = "", coefficient_multiplier: float = 0.0,
                        cooperative_fee: str = "", expiration_date: str = "",
                        pdf_url: str = "", is_executed: bool = False) -> str:
        """Create or idempotently fill a contract (keyed on contract number)."""
        repo = _repo()
        cid, is_new = repo.upsert_contract(Contract(
            contract_title=contract_title, contract_no=contract_no or None,
            contract_type=contract_type or None, owner_entity=owner_entity or None,
            location=location or None,
            coefficient_multiplier=coefficient_multiplier or None,
            cooperative_fee=cooperative_fee or None,
            expiration_date=expiration_date or None, pdf_url=pdf_url or None,
            is_executed=is_executed), actor="mcp")
        repo.conn.commit()
        return json.dumps({"contract_id": cid, "is_new": is_new})

    @mcp.tool()
    def update_field(contract_id: int, field: str, value: str) -> str:
        """Update one editable field on a contract (same path as the dashboard)."""
        repo = _repo()
        try:
            return json.dumps(repo.update_field(contract_id, field, value, actor="mcp"),
                              default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def sync_jobs(contract_no: str, jobs_json: str) -> str:
        """Cache jobs done under a contract (rows pulled from JobTread via its
        MCP). `jobs_json` is a JSON array of {name, customer, status,
        contract_value, sales_amount, external_id}. Powers the profile roll-up."""
        from .jobs import sync_jobs as _sync
        repo = _repo()
        try:
            rows = json.loads(jobs_json)
        except Exception as e:
            return json.dumps({"error": f"bad jobs_json: {e}"})
        return json.dumps(_sync(repo, rows, default_contract_no=contract_no))

    @mcp.tool()
    def stats() -> str:
        """Database statistics: contract counts, unexecuted total, jobs."""
        return json.dumps(_repo().stats())

    @mcp.tool()
    def get_brand() -> str:
        """Return the brand (colors/fonts) resolved live from the newest brand
        skill in Claude's settings — so other tools can render on-brand too."""
        from . import branding
        return json.dumps(branding.resolve_brand().to_dict(), default=str)

    return mcp


def serve(db_override: str | None = None) -> None:
    build_server(db_override).run()
