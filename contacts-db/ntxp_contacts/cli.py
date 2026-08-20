"""`ntxp` command-line interface — the shell-out surface for other NTXP tools."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from .config import db_path
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


@main.command()
@click.pass_context
def init(ctx):
    """Create the database and apply migrations."""
    conn = _conn(ctx)
    applied = migrate(conn)
    click.echo(f"DB ready at {db_path(ctx.obj.get('db'))}")
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


@main.command("mcp-serve")
@click.pass_context
def mcp_serve(ctx):
    """Run the MCP server exposing the contacts DB as tools (Phase 6)."""
    from .mcp_server import serve
    serve(ctx.obj.get("db"))


if __name__ == "__main__":
    main()
