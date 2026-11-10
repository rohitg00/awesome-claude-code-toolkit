"""`ntxp` command-line interface — the shell-out surface for other NTXP tools."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from .config import backend, db_path, db_url
from .db import connect, migrate
from .db.repository import Repository

# Map a source name to a default filename glob, for `import --all <dir>`.
SOURCE_GLOBS = {
    "tips": "*TipsMembers*.xlsx",
    "buildingconnectd": "*buildingconnect*.xlsx",
    "approved_subs": "*APPROVED_SUBCONTRACTORS*.xls",
    "luncheon": "*Luncheon*.xls",
}


@click.group()
@click.option("--db", "db_override", default=None, help="Path to the SQLite DB.")
@click.version_option(__version__)
@click.pass_context
def main(ctx: click.Context, db_override: str | None) -> None:
    """NTXP master contacts database."""
    ctx.ensure_object(dict)
    ctx.obj["db"] = db_override


def _conn(ctx):
    return connect(ctx.obj.get("db"))


def _redact_dsn(dsn: str | None) -> str:
    """Hide any password in a postgres:// DSN before echoing it."""
    if not dsn:
        return "(none)"
    import re
    return re.sub(r"(://[^:/@]+):[^@]+@", r"\1:***@", dsn)


@main.command()
@click.pass_context
def init(ctx):
    """Create the database and apply migrations."""
    conn = _conn(ctx)
    applied = migrate(conn)
    ov = ctx.obj.get("db")
    target = _redact_dsn(db_url(ov)) if backend(ov) == "postgres" else str(db_path(ov))
    click.echo(f"DB ready ({backend(ov)}) at {target}")
    click.echo(f"Applied migrations: {applied or 'none (up to date)'}")


@main.command()
@click.pass_context
def migrate_cmd(ctx):
    """Apply pending migrations."""
    conn = _conn(ctx)
    click.echo(f"Applied: {migrate(conn) or 'none (up to date)'}")


main.add_command(migrate_cmd, name="migrate")


@main.command(name="import")
@click.argument("source")
@click.argument("path", required=False, type=click.Path(exists=True))
@click.option("--all", "all_dir", type=click.Path(exists=True, file_okay=False),
              help="Import every known spreadsheet source found in this directory.")
@click.option("--dry-run", is_flag=True, help="Resolve but roll back; print a summary.")
@click.option("--stage", is_flag=True, help="Quarantine rows into staging instead of resolving.")
@click.pass_context
def import_cmd(ctx, source, path, all_dir, dry_run, stage):
    """Import a SOURCE file (or --all from a directory).

    SOURCE is one of: tips, buildingconnectd, approved_subs, luncheon, cjp_pdf.
    Use SOURCE='all' with --all <dir> to load every spreadsheet source.
    """
    from .loaders import get_loader, import_records

    conn = _conn(ctx)
    migrate(conn)

    jobs: list[tuple[str, Path]] = []
    if all_dir or source == "all":
        base = Path(all_dir or path)
        for src, glob in SOURCE_GLOBS.items():
            matches = list(base.glob(glob))
            if matches:
                jobs.append((src, matches[0]))
            else:
                click.echo(f"  (no file matched {glob} for {src})", err=True)
    else:
        if not path:
            raise click.UsageError("PATH is required unless using --all.")
        jobs.append((source, Path(path)))

    for src, fpath in jobs:
        loader = get_loader(src)
        stats = import_records(conn, loader, fpath, dry_run=dry_run,
                               stage=stage or src == "cjp_pdf")
        click.echo(f"[{src}] {json.dumps(stats.as_dict())}")
    click.echo(json.dumps(Repository(conn).stats(), indent=2))


@main.command()
@click.argument("text")
@click.option("--limit", default=25)
@click.pass_context
def query(ctx, text, limit):
    """Full-text search contacts and organizations."""
    repo = Repository(_conn(ctx))
    results = repo.search(text, limit=limit)
    click.echo(json.dumps(results, indent=2, default=str))


@main.command()
@click.option("--format", "fmt", type=click.Choice(["csv", "json"]), default="csv")
@click.option("--out", type=click.Path(), default="-")
@click.pass_context
def export(ctx, fmt, out):
    """Export all contacts as CSV or JSON."""
    from .db.repository import iter_contacts
    conn = _conn(ctx)
    contacts = [c for c in iter_contacts(conn) if c]
    stream = sys.stdout if out == "-" else open(out, "w", newline="", encoding="utf-8")
    try:
        if fmt == "json":
            json.dump(contacts, stream, indent=2, default=str)
        else:
            import csv
            cols = ["contact_id", "full_name", "title", "org_name",
                    "primary_email", "primary_phone", "city", "state"]
            w = csv.DictWriter(stream, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for c in contacts:
                emails = c.get("emails") or []
                phones = c.get("phones") or []
                addrs = c.get("addresses") or []
                w.writerow({
                    "contact_id": c["contact_id"],
                    "full_name": c.get("full_name"),
                    "title": c.get("title"),
                    "org_name": c.get("org_name"),
                    "primary_email": emails[0]["email"] if emails else "",
                    "primary_phone": (phones[0].get("phone_e164") or phones[0].get("phone_raw")) if phones else "",
                    "city": addrs[0]["city"] if addrs else "",
                    "state": addrs[0]["state"] if addrs else "",
                })
    finally:
        if stream is not sys.stdout:
            stream.close()
            click.echo(f"Wrote {len(contacts)} contacts to {out}")


@main.command()
@click.pass_context
def stats(ctx):
    """Print database statistics."""
    click.echo(json.dumps(Repository(_conn(ctx)).stats(), indent=2))


@main.command()
@click.option("--source", required=True, help="Source whose members to prune, e.g. tips.")
@click.option("--keep-states", required=True,
              help="Comma-separated 2-letter states to KEEP, e.g. TX,OK. All others are removed.")
@click.option("--hard", is_flag=True, help="Permanently delete instead of tombstoning (default: reversible tombstone).")
@click.option("--dry-run", is_flag=True, help="Report what would be removed; make no changes.")
@click.pass_context
def prune(ctx, source, keep_states, hard, dry_run):
    """Remove members of a SOURCE whose state is not in --keep-states.

    Example: ntxp prune --source tips --keep-states TX,OK
    Tombstoned records are filtered from every query/export/stat but remain
    recoverable; use --hard to delete permanently.
    """
    conn = _conn(ctx)
    repo = Repository(conn)
    summary = repo.prune_by_state(source, keep_states.split(","), hard=hard, dry_run=dry_run)
    if not dry_run:
        conn.commit()
    click.echo(json.dumps(summary, indent=2))


@main.group()
def dedup():
    """De-duplication review tools."""


@dedup.command("review")
@click.option("--limit", default=50)
@click.pass_context
def dedup_review(ctx, limit):
    """List contacts flagged for near-duplicate review."""
    conn = _conn(ctx)
    rows = conn.execute(
        "SELECT c.contact_id, c.full_name, t.value FROM contacts c "
        "JOIN entity_tags et ON et.entity_type='contact' AND et.entity_id=c.contact_id "
        "JOIN tags t ON t.tag_id=et.tag_id WHERE t.kind='review' AND c.is_deleted=0 LIMIT ?",
        (limit,)).fetchall()
    for r in rows:
        click.echo(f"{r['contact_id']}\t{r['full_name']}\t{r['value']}")
    click.echo(f"-- {len(rows)} flagged")


@dedup.command("merge")
@click.argument("survivor", type=int)
@click.argument("loser", type=int)
@click.pass_context
def dedup_merge(ctx, survivor, loser):
    """Merge LOSER contact into SURVIVOR (reversible tombstone)."""
    conn = _conn(ctx)
    Repository(conn).merge_contacts(survivor, loser, origin="cli")
    conn.commit()
    click.echo(f"Merged {loser} -> {survivor}")


@main.group()
def staging():
    """OCR/low-confidence staging queue."""


@staging.command("list")
@click.option("--status", default="pending")
@click.option("--limit", default=50)
@click.pass_context
def staging_list(ctx, status, limit):
    conn = _conn(ctx)
    rows = conn.execute(
        "SELECT staging_id, confidence, payload FROM staging_records "
        "WHERE status = ? ORDER BY confidence LIMIT ?", (status, limit)).fetchall()
    for r in rows:
        p = json.loads(r["payload"])
        click.echo(f"{r['staging_id']}\t{r['confidence']}\t{p.get('full_name')}\t{p.get('org_name')}")
    click.echo(f"-- {len(rows)} {status}")


@staging.command("promote")
@click.argument("staging_id", type=int, required=False)
@click.option("--all-above", type=float, help="Promote all pending rows with confidence >= X.")
@click.pass_context
def staging_promote(ctx, staging_id, all_above):
    """Promote staged row(s) into the canonical tables."""
    from .loaders.base import import_records  # reuse resolver via a synthetic loader
    from .model import CanonicalRecord, Email, Phone, Tag
    from .resolve import Resolver
    conn = _conn(ctx)
    repo = Repository(conn)
    resolver = Resolver(repo)

    where = "status='pending'"
    params: list = []
    if staging_id:
        where += " AND staging_id = ?"
        params.append(staging_id)
    if all_above is not None:
        where += " AND confidence >= ?"
        params.append(all_above)
    rows = conn.execute(f"SELECT * FROM staging_records WHERE {where}", params).fetchall()
    n = 0
    for r in rows:
        p = json.loads(r["payload"])
        rec = CanonicalRecord(source=p["source"], source_pk=p.get("source_pk"))
        rec.org_name = p.get("org_name")
        rec.org_name_norm = __import__("ntxp_contacts.normalize", fromlist=["org_name_norm"]).org_name_norm(p.get("org_name") or "") or None
        rec.full_name = p.get("full_name")
        rec.first_name = p.get("first_name")
        rec.last_name = p.get("last_name")
        rec.name_norm = __import__("ntxp_contacts.normalize", fromlist=["name_norm"]).name_norm(p.get("first_name"), p.get("last_name"), p.get("full_name"))
        rec.tags = [Tag("cjp", "holder"), Tag("source", p["source"])]
        rec.raw = p.get("raw", {})
        org_id = resolver.resolve_org(rec, origin="staging")
        resolver.resolve_contact(rec, org_id, origin="staging")
        conn.execute("UPDATE staging_records SET status='promoted' WHERE staging_id=?", (r["staging_id"],))
        n += 1
    conn.commit()
    click.echo(f"Promoted {n} staged rows")


@main.command("extract-cjp")
@click.argument("pdf", type=click.Path(exists=True))
@click.argument("out_jsonl", type=click.Path())
@click.pass_context
def extract_cjp(ctx, pdf, out_jsonl):
    """Extract embedded page images from the CJP PDF for OCR (Phase 4)."""
    from .loaders.extract_cjp import extract_images
    paths = extract_images(pdf, out_dir=str(Path(out_jsonl).parent / "cjp_images"))
    click.echo(f"Extracted {len(paths)} page images. OCR them and write JSONL to {out_jsonl}.")
    for p in paths:
        click.echo(f"  {p}")


@main.command("sync")
@click.argument("direction", type=click.Choice(["pull", "push"]))
@click.option("--system", required=True)
@click.option("--dry-run", is_flag=True, default=True)
@click.option("--plan-out", type=click.Path(), default=None)
@click.pass_context
def sync_cmd(ctx, direction, system, dry_run, plan_out):
    """Sync with an external CRM (Phase 7). Defaults to --dry-run."""
    from .sync.engine import SyncEngine
    conn = _conn(ctx)
    engine = SyncEngine(conn, system)
    plan = engine.plan(direction)
    if plan_out:
        Path(plan_out).write_text(json.dumps(plan, indent=2, default=str))
        click.echo(f"Wrote sync plan ({len(plan)} ops) to {plan_out}")
    else:
        click.echo(json.dumps(plan, indent=2, default=str))
    if not dry_run:
        click.echo("Live sync requires the MCP-mediated executor; see README.", err=True)


@main.command("reconcile")
@click.option("--system", required=True,
              help="Source system: lightfield|jobtread|quickbooks|buildingconnected|quo")
@click.argument("payloads", type=click.Path(exists=True))
@click.option("--apply", "do_apply", is_flag=True,
              help="Apply into the canonical DB (local write only). Default: plan.")
@click.pass_context
def reconcile_cmd(ctx, system, payloads, do_apply):
    """Reconcile records pulled from SYSTEM into the canonical store.

    PAYLOADS is a JSON file: a list of record dicts (each with an 'external_id'
    or 'id'), as dumped by the agent after pulling via that system's MCP/REST.
    Lightfield is the canonical hub; others reconcile back to it. Planning is
    read-only; --apply writes only to the local canonical DB, never to the CRM.
    """
    from .sync.reconcile import reconcile as _reconcile
    conn = _conn(ctx)
    migrate(conn)
    data = json.loads(Path(payloads).read_text())
    if not isinstance(data, list):
        data = data.get("records") or data.get("items") or [data]
    result = _reconcile(conn, system, data, apply=do_apply)
    click.echo(json.dumps(result, indent=2, default=str))


@main.command("sweep")
@click.argument("bundle", type=click.Path(exists=True))
@click.option("--qualify/--no-qualify", "do_qualify", default=True,
              help="Re-grade affected contacts after the sweep (default on).")
@click.pass_context
def sweep_cmd(ctx, bundle, do_qualify):
    """Ingest a nightly Google Workspace sweep BUNDLE (JSON) into the canonical DB.

    BUNDLE buckets raw Workspace objects by channel:
    {"gmail":[...], "gcontacts":[...], "calendar":[...], "drive":[...], "people":[...]}.
    Collection only — deterministic extraction + dedup; grading runs after.
    Writes only to the local canonical store (fan-out to connectors happens on
    the next `ntxp sync push`).
    """
    from .collect import sweep as _sweep
    conn = _conn(ctx)
    migrate(conn)
    data = json.loads(Path(bundle).read_text())
    result = _sweep(conn, data)
    if do_qualify:
        from .qualify import Grader
        result["qualify"] = Grader(conn).run()
    click.echo(json.dumps(result, indent=2, default=str))


@main.command("qualify")
@click.option("--apply/--plan", "do_apply", default=True,
              help="--apply writes grades (default); --plan computes without writing.")
@click.pass_context
def qualify_cmd(ctx, do_apply):
    """Grade every contact (JEV qualification) and set the exposure/sync gate.

    Scores each contact on source trust, recency, corroboration and
    distance-from-person; outdated/low-grade contacts keep all their references
    but are flagged is_exposed=0 / is_synced=0 so the UI and sync hold them back.
    """
    from .qualify import Grader
    conn = _conn(ctx)
    migrate(conn)
    click.echo(json.dumps(Grader(conn).run(apply=do_apply), indent=2, default=str))


@main.command("connector-import")
@click.option("--service", required=True, help="Source platform (must be allowlisted).")
@click.argument("contactsfile", type=click.Path(exists=True))
@click.pass_context
def connector_import_cmd(ctx, service, contactsfile):
    """Ingest contacts a connected service returned (via Zapier or its own OAuth).

    CONTACTSFILE is JSON: a list of raw contact dicts the agent fetched.
    Allowlist-gated (NTXP_CONNECTOR_ALLOWLIST).
    """
    from .connectors import ingest_contacts
    conn = _conn(ctx)
    migrate(conn)
    rows = json.loads(Path(contactsfile).read_text())
    if not isinstance(rows, list):
        rows = rows.get("contacts") or rows.get("records") or [rows]
    try:
        click.echo(json.dumps(ingest_contacts(conn, service, rows), indent=2, default=str))
    except PermissionError as exc:
        click.echo(json.dumps({"error": str(exc)}))
        raise SystemExit(1)


@main.command("council")
@click.argument("taskfile", type=click.Path(exists=True))
@click.option("--escalate", type=int, default=1, help="Max LLM judges to consult on escalation.")
@click.option("--save/--no-save", default=True, help="Persist the answer to the database (default).")
@click.pass_context
def council_cmd(ctx, taskfile, escalate, save):
    """Decide a qualification task via the model council (JEV free; cheap LLMs on
    escalation). TASKFILE is JSON: {kind, question, options:[{id,value,grade?}]}.
    The consensus + provenance are persisted (council_answers) unless --no-save."""
    from .council import decide
    task = json.loads(Path(taskfile).read_text())
    conn = None
    if save:
        conn = _conn(ctx)
        migrate(conn)
    click.echo(json.dumps(decide(task, conn=conn, escalate=escalate), indent=2, default=str))


@main.command("council-report")
@click.pass_context
def council_report_cmd(ctx):
    """Consensus-of-effectiveness summary over all persisted council answers."""
    from .council import effectiveness, list_answers
    conn = _conn(ctx)
    migrate(conn)
    click.echo(json.dumps({"effectiveness": effectiveness(conn),
                           "recent": list_answers(conn, 10)}, indent=2, default=str))


@main.command("context")
@click.argument("query")
@click.pass_context
def context_cmd(ctx, query):
    """Context card (with blue-link HTML) for the best contact match of QUERY."""
    from .context import HotlinkIndex
    conn = _conn(ctx)
    res = Repository(conn).search(query, 1)
    if not res:
        click.echo("{}")
        return
    cid = res[0].get("contact_id")
    idx = HotlinkIndex(conn)
    if cid:
        click.echo(json.dumps({"card": idx.card(cid), "html": idx.card_html(cid)},
                              indent=2, default=str))
    else:
        click.echo(json.dumps(res[0], indent=2, default=str))


@main.command("hotlink")
@click.argument("textfile", type=click.Path(exists=True))
@click.pass_context
def hotlink_cmd(ctx, textfile):
    """Annotate a text file: wrap known contacts/orgs/emails/phones in blue hotlinks."""
    from .context import annotate
    conn = _conn(ctx)
    click.echo(json.dumps(annotate(conn, Path(textfile).read_text()), indent=2, default=str))


@main.group("peers")
def peers_grp():
    """Interlink with NTXP Schedules, Master Contracts and Form Fill."""


@peers_grp.command("keygen")
@click.argument("name")
def peers_keygen(name):
    """Print a new shared secret for peer NAME (it is NOT stored — put it in NTXP_PEERS and in the peer)."""
    import secrets
    sec = secrets.token_urlsafe(32)
    click.echo(json.dumps({"peer": name, "secret": sec,
                           "service_token": f"svc.{name}.{sec}",
                           "note": "Add to NTXP_PEERS and give the same secret to the peer app. Shown once."}, indent=2))


@peers_grp.command("status")
@click.pass_context
def peers_status_cmd(ctx):
    """Peer config health, outbox counts and watch cursors (never prints secrets)."""
    from .peers import load_peers
    from .peers.events import outbox_stats
    conn = _conn(ctx)
    migrate(conn)
    peers, errors = load_peers()
    cursors = [dict(r) for r in conn.execute("SELECT peer, stream, cursor FROM peer_cursor").fetchall()]
    dead = [dict(r) for r in conn.execute(
        "SELECT outbox_id, peer, event_type, attempts, last_error FROM peer_outbox WHERE status='dead' "
        "ORDER BY outbox_id DESC LIMIT 10").fetchall()]
    click.echo(json.dumps({
        "peers": {n: {"url": p.url, "hook": p.hook_url, "events": list(p.events),
                      "receives_events": p.receives_events, "pulls": p.pulls} for n, p in peers.items()},
        "config_errors": errors, "outbox": outbox_stats(conn), "cursors": cursors, "dead_letters": dead}, indent=2, default=str))


@peers_grp.command("run")
@click.option("--watch", is_flag=True, help="Loop forever (use when NTXP_PEERS_AUTORUN=0).")
@click.option("--interval", type=float, default=30.0)
@click.pass_context
def peers_run_cmd(ctx, watch, interval):
    """One watch cycle: pull Master Contracts, queue contact events, deliver webhooks."""
    import time
    from .peers.runner import run_cycle
    while True:
        conn = _conn(ctx)
        migrate(conn)
        click.echo(json.dumps(run_cycle(conn), default=str))
        conn.close()
        if not watch:
            return
        time.sleep(interval)


@peers_grp.command("backfill")
@click.argument("name")
@click.pass_context
def peers_backfill_cmd(ctx, name):
    """Queue every exposed contact once for peer NAME (do this when first connecting it)."""
    from .peers import load_peers
    from .peers.events import backfill
    peers, _ = load_peers()
    if name not in peers:
        raise click.ClickException(f"peer '{name}' is not configured")
    conn = _conn(ctx)
    migrate(conn)
    click.echo(json.dumps({"queued": backfill(conn, peers[name])}))


@peers_grp.command("retry")
@click.argument("outbox_id", type=int)
@click.pass_context
def peers_retry_cmd(ctx, outbox_id):
    """Re-queue a dead-lettered event."""
    from .peers.context import now_ts
    conn = _conn(ctx)
    n = conn.execute("UPDATE peer_outbox SET status='pending', attempts=0, next_attempt_at=? "
                     "WHERE outbox_id=? AND status='dead'", (now_ts(conn), outbox_id)).rowcount
    conn.commit()
    click.echo(json.dumps({"requeued": n}))


@main.group("enrich")
def enrich_grp():
    """Backfill missing fields, photos, and LinkedIn via graded candidates."""


@enrich_grp.command("detect")
@click.pass_context
def enrich_detect_cmd(ctx):
    """List live contacts missing primary fields (email/phone/address/website/photo/linkedin)."""
    from .enrich import detect_missing
    conn = _conn(ctx)
    migrate(conn)
    click.echo(json.dumps(detect_missing(conn), indent=2, default=str))


@enrich_grp.command("generate")
@click.option("--extra", type=click.Path(exists=True), default=None,
              help="JSON list of agent/OSINT candidates to fold in.")
@click.pass_context
def enrich_generate_cmd(ctx, extra):
    """Run resolvers for contacts with missing fields and store graded candidates."""
    from .enrich import generate
    conn = _conn(ctx)
    migrate(conn)
    extras = json.loads(Path(extra).read_text()) if extra else None
    click.echo(json.dumps(generate(conn, extra=extras), indent=2, default=str))


@enrich_grp.command("candidates")
@click.option("--status", default="proposed")
@click.option("--field", default=None)
@click.option("--min-grade", type=float, default=0.0)
@click.pass_context
def enrich_candidates_cmd(ctx, status, field, min_grade):
    """List enrichment candidates (highest grade first)."""
    from .enrich import list_candidates
    conn = _conn(ctx)
    migrate(conn)
    click.echo(json.dumps(list_candidates(conn, status, field, min_grade=min_grade),
                          indent=2, default=str))


@enrich_grp.command("confirm")
@click.argument("cand_id", type=int)
@click.pass_context
def enrich_confirm_cmd(ctx, cand_id):
    """Apply a candidate to the contact and mark it confirmed."""
    from .enrich import confirm
    click.echo(json.dumps(confirm(_conn(ctx), cand_id), default=str))


@enrich_grp.command("reject")
@click.argument("cand_id", type=int)
@click.pass_context
def enrich_reject_cmd(ctx, cand_id):
    """Reject a candidate."""
    from .enrich import reject
    click.echo(json.dumps(reject(_conn(ctx), cand_id), default=str))


@enrich_grp.command("linkedin")
@click.option("--contact-id", type=int, required=True)
@click.option("--url", required=True)
@click.option("--photo", default=None, help="LinkedIn profile photo URL to promote.")
@click.pass_context
def enrich_linkedin_cmd(ctx, contact_id, url, photo):
    """Confirm a LinkedIn match (saves the LinkedIn field + promotes the photo)."""
    from .enrich import confirm_linkedin
    click.echo(json.dumps(confirm_linkedin(_conn(ctx), contact_id, url, photo), default=str))


@main.command("mcp-serve")
@click.pass_context
def mcp_serve(ctx):
    """Run the MCP server exposing the contacts DB as tools (stdio)."""
    from .mcp_server import serve
    serve(ctx.obj.get("db"))


@main.command("vcard-export")
@click.option("--out", type=click.Path(), default=None, help="Write to a .vcf file.")
@click.option("--all", "include_all", is_flag=True, help="Include held-back (not-exposed) contacts too.")
@click.pass_context
def vcard_export(ctx, out, include_all):
    """Export exposed contacts as vCards (the one-way iOS feed, offline)."""
    from .remote.vcard import export_vcards
    conn = _conn(ctx)
    migrate(conn)
    data = export_vcards(conn, exposed_only=not include_all)
    if out:
        Path(out).write_text(data, encoding="utf-8")
        click.echo(f"Wrote {data.count('BEGIN:VCARD')} vCards to {out}")
    else:
        click.echo(data)


@main.command("serve-http")
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8080, type=int)
@click.pass_context
def serve_http(ctx, host, port):
    """Run the stateless cloud MCP over streamable HTTP, gated by an OAuth token.

    Auth via env NTXP_MCP_AUTH=google|static|none (see remote/auth.py). The MCP
    endpoint is at /mcp; GET /health is open. Point NTXP_DB_URL at the cloud
    Postgres so every caller shares one canonical store.
    """
    from .remote import serve as serve_remote
    click.echo(f"NTXP contacts MCP (stateless HTTP) on {host}:{port} — endpoint /mcp", err=True)
    serve_remote(ctx.obj.get("db"), host, port)


if __name__ == "__main__":
    main()
