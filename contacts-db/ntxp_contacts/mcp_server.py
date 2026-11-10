"""MCP server exposing the master contacts DB as tools for NTXP's Claude tools.

Run with `ntxp mcp-serve` (stdio transport). Other NTXP tools register this in
their MCP config and query the single source of truth directly.
"""
from __future__ import annotations

import json

from .config import db_path
from .db import connect, migrate
from .db.repository import Repository


def build_server(db_override: str | None = None, stateless_http: bool = False):
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "The 'mcp' package is required. Install with: pip install 'ntxp-contacts[mcp]'"
        ) from exc

    mcp = FastMCP("ntxp-contacts", stateless_http=stateless_http)

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

    @mcp.tool()
    def reconcile_plan(system: str, records: list[dict]) -> str:
        """Delta plan (read-only) for records pulled from SYSTEM. Each record is
        a dict with an 'external_id' (or 'id'). Classifies every record as
        create/link/update/conflict/unchanged against the canonical store and
        lists conflicting fields. Lightfield is the canonical hub; other systems
        reconcile back to it. No writes."""
        from .sync.reconcile import reconcile
        return json.dumps(reconcile(_conn(), system, list(records), apply=False), default=str)

    @mcp.tool()
    def reconcile_apply(system: str, records: list[dict]) -> str:
        """Apply records pulled from SYSTEM into the canonical DB (idempotent,
        de-duplicating, linking external ids). Writes ONLY to the local canonical
        store — never to the remote CRM. Returns a counts summary."""
        from .sync.reconcile import reconcile
        return json.dumps(reconcile(_conn(), system, list(records), apply=True), default=str)

    @mcp.tool()
    def workspace_sweep(bundle: dict) -> str:
        """Ingest a Google Workspace sweep bundle into the canonical store.
        bundle buckets raw objects by channel: {"gmail":[...], "gcontacts":[...],
        "calendar":[...], "drive":[...], "people":[...]}. Deterministic
        collection + dedup only — no qualifying. Writes only locally; call
        qualify_contacts afterward and sync_plan to fan out. Returns counts."""
        from .collect import sweep
        return json.dumps(sweep(_conn(), dict(bundle)), default=str)

    @mcp.tool()
    def qualify_contacts(apply: bool = True) -> str:
        """Grade every contact (JEV qualification) on source trust, recency,
        corroboration and distance-from-person, and set the exposure/sync gate
        (outdated/low-grade contacts are kept but flagged is_exposed=0). apply
        writes the grades; apply=False just returns the summary."""
        from .qualify import Grader
        return json.dumps(Grader(_conn()).run(apply=apply), default=str)

    @mcp.tool()
    def connector_import(service: str, contacts: list[dict]) -> str:
        """Ingest contacts a connected service returned into the canonical store
        (idempotent, de-duplicating). `service` must be on the connector
        allowlist (Zapier is the recommended broker; secrets stay in Zapier).
        Returns counts, or an error if the service is not allowlisted."""
        from .connectors import ingest_contacts
        try:
            return json.dumps(ingest_contacts(_conn(), service, list(contacts)), default=str)
        except PermissionError as exc:
            return json.dumps({"error": str(exc)})

    @mcp.tool()
    def council_decide(task: dict) -> str:
        """Decide a qualification task via the model council — JEV (free,
        deterministic) decides, escalating to cheap LLM judges (DeepSeek/Grok/
        OpenAI, key-gated) only when uncertain. task = {kind, question,
        options:[{id,value,grade?,evidence?}]}. Returns choice + confidence +
        provenance."""
        from .council import decide
        return json.dumps(decide(dict(task), conn=_conn()), default=str)

    @mcp.tool()
    def council_report() -> str:
        """Consensus-of-effectiveness summary (decisions, % resolved free by JEV,
        total cost, avg confidence by mode) over persisted council answers."""
        from .council import effectiveness, list_answers
        conn = _conn()
        return json.dumps({"effectiveness": effectiveness(conn),
                           "recent": list_answers(conn, 10)}, default=str)

    @mcp.tool()
    def contact_context(query: str) -> str:
        """Context card for the best contact match of QUERY (name/email/company),
        with blue-link HTML ready to inject into any tool's output."""
        from .context import HotlinkIndex
        conn = _conn()
        res = Repository(conn).search(query, 1)
        if not res:
            return json.dumps({})
        idx = HotlinkIndex(conn)
        cid = res[0].get("contact_id")
        return json.dumps({"card": idx.card(cid) if cid else res[0],
                           "html": idx.card_html(cid) if cid else None}, default=str)

    @mcp.tool()
    def locate_address(address: str) -> str:
        """Live location links (Google + Apple Maps) for an address string — for
        injecting a clickable map link next to any contact address."""
        from .remote.maps import maps_link, apple_maps_link
        return json.dumps({"google": maps_link(address), "apple": apple_maps_link(address)})

    @mcp.tool()
    def hotlink_text(text: str) -> str:
        """Annotate text, wrapping every recognized contact/org/email/phone in a
        blue hyperlink hotlink that opens the contacts page filtered to it.
        Returns {html, links}."""
        from .context import annotate
        return json.dumps(annotate(_conn(), text), default=str)

    @mcp.tool()
    def enrich_detect() -> str:
        """Live contacts missing primary fields (email/phone/address/website/photo/linkedin)."""
        from .enrich import detect_missing
        return json.dumps(detect_missing(_conn()), default=str)

    @mcp.tool()
    def enrich_generate(extra: list[dict] | None = None) -> str:
        """Run resolvers for contacts with missing fields and store graded
        candidates. `extra` folds in out-of-band OSINT results (holehe/maigret/
        GHunt/LinkedIn): dicts {contact_id, field, value, source, evidence?}."""
        from .enrich import generate
        return json.dumps(generate(_conn(), extra=list(extra) if extra else None), default=str)

    @mcp.tool()
    def enrich_candidates(status: str = "proposed", field: str = "", min_grade: float = 0.0) -> str:
        """List enrichment candidates (highest grade first) for review."""
        from .enrich import list_candidates
        return json.dumps(list_candidates(_conn(), status, field or None, min_grade=min_grade), default=str)

    @mcp.tool()
    def enrich_confirm(cand_id: int) -> str:
        """Apply a proposed candidate to the contact and mark it confirmed."""
        from .enrich import confirm
        return json.dumps(confirm(_conn(), cand_id), default=str)

    @mcp.tool()
    def enrich_reject(cand_id: int) -> str:
        """Reject an enrichment candidate."""
        from .enrich import reject
        return json.dumps(reject(_conn(), cand_id), default=str)

    @mcp.tool()
    def confirm_linkedin(contact_id: int, url: str, photo_url: str = "",
                         company_match: bool = True) -> str:
        """Confirm a LinkedIn match the agent verified: saves the URL to the
        contact's LinkedIn field (when it matches the employer) and promotes the
        LinkedIn profile photo to the contact photo."""
        from .enrich import confirm_linkedin as _cl
        return json.dumps(_cl(_conn(), contact_id, url, photo_url or None, company_match), default=str)

    @mcp.tool()
    def get_grade(contact_id: int) -> str:
        """The computed quality grade for one contact (grade, band, sources,
        age, exposure/sync flags, and a short reason)."""
        from .qualify import Grader
        return json.dumps(Grader(_conn()).get_grade(contact_id), default=str)

    return mcp


def serve(db_override: str | None = None) -> None:
    build_server(db_override).run()
