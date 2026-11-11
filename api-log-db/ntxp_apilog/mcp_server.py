"""MCP server exposing the shared API Log as tools for Claude.

Run with `ntxp-apilog mcp-serve` (stdio transport). Register it via
`mcp-configs/ntxp-apilog.json`. This is the layer that lets Claude *fill in* an
API the moment a system, skill, or user asks for one: instead of stopping to ask
the user for a URL or key, Claude calls `find_api` / `get_credentials` against
the single source of truth — and records new APIs and their cost as it goes.

Every credential read through `get_credentials` is written to the access log.
"""
from __future__ import annotations

import json

from .crypto import Cipher
from .db import connect, migrate
from .db.repository import Repository
from .model import ApiEntry, UsageEvent, parse_tags


def build_server(db_override: str | None = None):
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "The 'mcp' package is required. Install with: pip install 'ntxp-apilog[mcp]'"
        ) from exc

    mcp = FastMCP("ntxp-apilog")

    # One-time setup: migrate the DB and build a shared Cipher at startup so
    # neither happens on every tool call.
    migrate(connect(db_override))
    shared_cipher = Cipher()

    def _repo() -> Repository:
        return Repository(connect(db_override), cipher=shared_cipher)

    @mcp.tool()
    def find_api(query: str, limit: int = 10) -> str:
        """Search the API Log by name, provider, purpose, category, or tag.

        Use this FIRST whenever you need an API and aren't sure it's registered.
        Returns non-secret metadata plus masked key previews and a
        `has_api_key` flag so you know whether credentials are on file. Does not
        reveal secrets — call `get_credentials` for that."""
        return json.dumps(_repo().search(query, limit=limit), default=str)

    @mcp.tool()
    def list_apis(status: str = "", category: str = "") -> str:
        """List registered APIs (masked). Optionally filter by status/category."""
        return json.dumps(
            _repo().list_apis(status=status or None, category=category or None),
            default=str,
        )

    @mcp.tool()
    def get_api(name_or_id: str) -> str:
        """Fetch one API's full metadata (URL, docs, cost model, masked secrets).

        Non-revealing and not audited — safe for inspecting what's on file."""
        api = _repo().resolve(name_or_id, reveal=False)
        return json.dumps(api or {"error": "not found"}, default=str)

    @mcp.tool()
    def get_credentials(name_or_id: str, requested_by: str = "", purpose: str = "") -> str:
        """Reveal an API's live credentials so you can fill them into a request.

        THIS IS THE FILL-IT-IN PATH. Call it when a system, skill, or user needs
        to actually call an API and you must supply the URL + key/login. Returns
        `base_url`, `auth_type`, `api_key`, `key_number`, `login_user`,
        `login_secret`, and a ready-to-use `auth_header` when applicable.

        Always pass `requested_by` (e.g. "skill:invoice-reconciliation" or
        "user:alex@ntxp.com") and a short `purpose` — every reveal is recorded in
        the access log. Returns `{"error": ...}` if the API isn't registered, so
        you can then `upsert_api` to add it."""
        repo = _repo()
        api = repo.resolve(name_or_id, reveal=True)
        if not api:
            return json.dumps({"error": "not found",
                               "hint": "register it first with upsert_api"})
        repo.log_access(api["api_id"], action="fill",
                        accessor=requested_by or None, purpose=purpose or None,
                        origin="mcp")
        key = api.get("api_key")
        auth_header = None
        if key:
            if api.get("auth_type") == "bearer":
                auth_header = {"Authorization": f"Bearer {key}"}
            elif api.get("auth_type") == "api_key":
                auth_header = {"Authorization": key}
        return json.dumps({
            "name": api["name"],
            "base_url": api.get("base_url"),
            "auth_type": api.get("auth_type"),
            "api_key": key,
            "key_number": api.get("key_number"),
            "login_user": api.get("login_user"),
            "login_secret": api.get("login_secret"),
            "login_url": api.get("login_url"),
            "auth_header": auth_header,
            "cost_model": api.get("cost_model"),
        }, default=str)

    @mcp.tool()
    def upsert_api(name: str, provider: str = "", category: str = "",
                   base_url: str = "", docs_url: str = "", login_url: str = "",
                   purpose: str = "", auth_type: str = "api_key",
                   api_key: str = "", key_number: str = "", login_user: str = "",
                   login_secret: str = "", cost_model: str = "",
                   monthly_budget: float = 0.0, owner: str = "",
                   tags: str = "", notes: str = "") -> str:
        """Register a new API (or update one) in the shared log.

        Use this when you discover/are given an API that isn't on file yet, so
        the next request can reuse it. `name` is the merge key. Omitted secret
        fields are left untouched on an existing entry (they are never wiped by a
        metadata-only update). `tags` is a comma-separated string."""
        repo = _repo()
        entry = ApiEntry(
            name=name, provider=provider or None, category=category or None,
            base_url=base_url or None, docs_url=docs_url or None,
            login_url=login_url or None, purpose=purpose or None,
            auth_type=auth_type or "api_key", api_key=api_key or None,
            key_number=key_number or None, login_user=login_user or None,
            login_secret=login_secret or None, cost_model=cost_model or None,
            monthly_budget=monthly_budget or None, owner=owner or None,
            tags=parse_tags(tags), notes=notes or None,
        )
        api_id, is_new = repo.upsert_api(entry, origin="mcp")
        return json.dumps({"api_id": api_id, "is_new": is_new})

    @mcp.tool()
    def log_usage(name_or_id: str, cost: float, units: float = 0.0,
                  unit_kind: str = "", description: str = "",
                  requested_by: str = "") -> str:
        """Record a cost/usage event against an API (keeps the spend total live).

        Call this after you actually use an API on someone's behalf so the
        dashboard's running cost stays accurate."""
        repo = _repo()
        api = repo.resolve(name_or_id, reveal=False)
        if not api:
            return json.dumps({"error": "not found"})
        log_id = repo.log_usage(UsageEvent(
            api_id=api["api_id"], cost=cost, currency=api.get("currency", "USD"),
            units=units or None, unit_kind=unit_kind or None,
            description=description or None, requested_by=requested_by or None,
            origin="mcp",
        ))
        return json.dumps({"log_id": log_id, "api_id": api["api_id"]})

    @mcp.tool()
    def stats() -> str:
        """API counts (by status/category) and spend totals (by API and month)."""
        return json.dumps(_repo().stats(), default=str)

    return mcp


def serve(db_override: str | None = None) -> None:
    build_server(db_override).run()
