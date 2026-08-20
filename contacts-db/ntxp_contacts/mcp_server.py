"""MCP server exposing the master contacts DB as tools for NTXP's Claude tools.

Run with `ntxp mcp-serve` (stdio transport). Other NTXP tools register this in
their MCP config and query the single source of truth directly.
"""
from __future__ import annotations

import json

from .config import db_path
from .db import connect, migrate
from .db.repository import Repository


def build_server(db_override: str | None = None):
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "The 'mcp' package is required. Install with: pip install 'ntxp-contacts[mcp]'"
        ) from exc

    mcp = FastMCP("ntxp-contacts")

    def _conn():
        c = connect(db_override)
        migrate(c)
        return c

    @mcp.tool()
    def search_contacts(query: str, limit: int = 25) -> str:
        """Full-text search contacts/organizations by name, org, or email."""
        repo = Repository(_conn())
        return json.dumps(repo.search(query, limit=limit), default=str)

    @mcp.tool()
    def get_contact(contact_id: int) -> str:
        """Fetch a single contact with emails, phones, addresses, and tags."""
        repo = Repository(_conn())
        return json.dumps(repo.get_contact(contact_id), default=str)

    @mcp.tool()
    def get_org(org_id: int) -> str:
        """Fetch a single organization."""
        repo = Repository(_conn())
        return json.dumps(repo.get_org(org_id), default=str)

    @mcp.tool()
    def upsert_contact(first_name: str = "", last_name: str = "", org_name: str = "",
                       email: str = "", phone: str = "", title: str = "") -> str:
        """Create or update a contact in the master DB (email is the merge key)."""
        from . import normalize as N
        from .model import CanonicalRecord, Email, Phone, Tag
        from .resolve import Resolver
        conn = _conn()
        repo = Repository(conn)
        rec = CanonicalRecord(source="mcp")
        rec.first_name, rec.last_name = first_name or None, last_name or None
        rec.full_name = " ".join(x for x in (first_name, last_name) if x) or None
        rec.name_norm = N.name_norm(first_name, last_name)
        rec.title = title or None
        if org_name:
            rec.org_name = org_name
            rec.org_name_norm = N.org_name_norm(org_name)
        em = N.normalize_email(email)
        if em:
            rec.emails.append(Email(email=em, email_norm=em, is_primary=True))
        if phone:
            rec.phones.append(Phone(phone_raw=phone, phone_e164=N.normalize_phone(phone)))
        resolver = Resolver(repo)
        org_id = resolver.resolve_org(rec, origin="mcp")
        decision = resolver.resolve_contact(rec, org_id, origin="mcp")
        for e in rec.emails:
            repo.add_email(e, decision.contact_id, None)
        for p in rec.phones:
            repo.add_phone(p, decision.contact_id, None)
        conn.commit()
        return json.dumps({"contact_id": decision.contact_id, "is_new": decision.is_new})

    @mcp.tool()
    def export_contacts(limit: int = 500) -> str:
        """Export up to `limit` contacts as JSON."""
        from .db.repository import iter_contacts
        conn = _conn()
        out = []
        for c in iter_contacts(conn):
            out.append(c)
            if len(out) >= limit:
                break
        return json.dumps(out, default=str)

    @mcp.tool()
    def stats() -> str:
        """Database statistics: entity counts and per-source provenance."""
        return json.dumps(Repository(_conn()).stats())

    @mcp.tool()
    def sync_plan(system: str, direction: str = "push") -> str:
        """Produce a dry-run sync plan (no writes) for an external CRM. The
        agent executes MCP-mediated CRMs from this plan, then calls
        record_sync_result for each applied op."""
        from .sync.engine import SyncEngine
        return json.dumps(SyncEngine(_conn(), system).plan(direction), default=str)

    @mcp.tool()
    def record_sync_result(system: str, contact_id: int, external_id: str,
                           remote_hash: str) -> str:
        """Persist an external-id mapping after the agent applies a sync op."""
        conn = _conn()
        from .sync.engine import SyncEngine
        SyncEngine(conn, system).record_result(contact_id, external_id, remote_hash)
        return json.dumps({"ok": True})

    return mcp


def serve(db_override: str | None = None) -> None:
    build_server(db_override).run()
