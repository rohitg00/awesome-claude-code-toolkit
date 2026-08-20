"""`ntxp-apilog` command-line interface — the shell-out surface for NTXP tools."""
from __future__ import annotations

import json
from pathlib import Path

import click

from . import __version__
from .config import DEFAULT_HOST, DEFAULT_PORT, db_path
from .crypto import generate_key
from .db import connect, migrate
from .db.repository import Repository
from .model import ApiEntry, UsageEvent, parse_tags


@click.group()
@click.option("--db", "db_override", default=None, help="Path to the SQLite DB.")
@click.version_option(__version__)
@click.pass_context
def main(ctx: click.Context, db_override: str | None) -> None:
    """NTXP API Log — shared registry of API endpoints, credentials, and cost."""
    ctx.ensure_object(dict)
    ctx.obj["db"] = db_override


def _repo(ctx) -> Repository:
    conn = connect(ctx.obj.get("db"))
    migrate(conn)
    return Repository(conn)


@main.command()
@click.pass_context
def init(ctx):
    """Create the database and apply migrations."""
    conn = connect(ctx.obj.get("db"))
    applied = migrate(conn)
    click.echo(f"DB ready at {db_path(ctx.obj.get('db'))}")
    click.echo(f"Applied migrations: {applied or 'none (up to date)'}")


@main.command("gen-key")
def gen_key():
    """Print a fresh encryption key to export as NTXP_APILOG_KEY."""
    click.echo(generate_key())
    click.echo("# export NTXP_APILOG_KEY=<the value above> on every machine "
               "sharing this DB", err=True)


@main.command()
@click.argument("name")
@click.option("--provider")
@click.option("--category")
@click.option("--base-url")
@click.option("--docs-url")
@click.option("--login-url")
@click.option("--purpose")
@click.option("--auth-type", default="api_key")
@click.option("--api-key", help="Stored encrypted at rest.")
@click.option("--key-number", help="Key id / account / project number (encrypted).")
@click.option("--login-user")
@click.option("--login-secret", help="Console password (encrypted).")
@click.option("--cost-model")
@click.option("--monthly-budget", type=float)
@click.option("--owner")
@click.option("--tags", help="Comma-separated.")
@click.option("--notes")
@click.pass_context
def add(ctx, name, tags, **kw):
    """Register or update an API (NAME is the merge key)."""
    entry = ApiEntry(
        name=name,
        tags=parse_tags(tags),
        **{k: v for k, v in kw.items() if v is not None},
    )
    api_id, is_new = _repo(ctx).upsert_api(entry, origin="cli")
    click.echo(f"{'Added' if is_new else 'Updated'} '{name}' (api_id={api_id})")


@main.command(name="list")
@click.option("--status")
@click.option("--category")
@click.pass_context
def list_cmd(ctx, status, category):
    """List registered APIs (secrets masked)."""
    rows = _repo(ctx).list_apis(status=status, category=category)
    for r in rows:
        budget = f" budget={r['monthly_budget']}" if r.get("monthly_budget") else ""
        click.echo(
            f"{r['api_id']:>3}  {r['name']:<24} {r.get('category') or '-':<12} "
            f"{r.get('status'):<8} key={r.get('api_key_masked') or '-':<10} "
            f"spend=${r.get('spend_total', 0)}{budget}"
        )
    click.echo(f"-- {len(rows)} APIs")


@main.command()
@click.argument("text")
@click.option("--limit", default=25)
@click.pass_context
def search(ctx, text, limit):
    """Full-text search APIs by name, provider, purpose, category, or tag."""
    click.echo(json.dumps(_repo(ctx).search(text, limit=limit), indent=2, default=str))


@main.command()
@click.argument("name_or_id")
@click.option("--reveal", is_flag=True, help="Decrypt and print secrets (audited).")
@click.option("--accessor", help="Who/what is revealing (for the access log).")
@click.option("--purpose")
@click.pass_context
def show(ctx, name_or_id, reveal, accessor, purpose):
    """Show one API. With --reveal, decrypt secrets and record the access."""
    repo = _repo(ctx)
    api = repo.resolve(name_or_id, reveal=reveal)
    if not api:
        raise click.ClickException(f"No API matching '{name_or_id}'")
    if reveal:
        repo.log_access(api["api_id"], action="reveal", accessor=accessor,
                        purpose=purpose, origin="cli")
    click.echo(json.dumps(api, indent=2, default=str))


@main.command("log-cost")
@click.argument("name_or_id")
@click.argument("cost", type=float)
@click.option("--units", type=float)
@click.option("--unit-kind")
@click.option("--description")
@click.option("--requested-by")
@click.pass_context
def log_cost(ctx, name_or_id, cost, units, unit_kind, description, requested_by):
    """Record a cost/usage event against an API."""
    repo = _repo(ctx)
    api = repo.resolve(name_or_id)
    if not api:
        raise click.ClickException(f"No API matching '{name_or_id}'")
    log_id = repo.log_usage(UsageEvent(
        api_id=api["api_id"], cost=cost, currency=api.get("currency", "USD"),
        units=units, unit_kind=unit_kind, description=description,
        requested_by=requested_by, origin="cli",
    ))
    click.echo(f"Logged ${cost} against '{api['name']}' (log_id={log_id})")


@main.command()
@click.pass_context
def stats(ctx):
    """Print database statistics and spend totals."""
    click.echo(json.dumps(_repo(ctx).stats(), indent=2, default=str))


@main.command()
@click.option("--reveal", is_flag=True, help="Include decrypted secrets (dangerous).")
@click.option("--out", type=click.Path(), default="-")
@click.pass_context
def export(ctx, reveal, out):
    """Export all APIs as JSON (masked unless --reveal)."""
    repo = _repo(ctx)
    rows = [repo.get_api(r["api_id"], reveal=reveal) for r in repo.list_apis()]
    payload = json.dumps(rows, indent=2, default=str)
    if out == "-":
        click.echo(payload)
    else:
        Path(out).write_text(payload, encoding="utf-8")
        click.echo(f"Wrote {len(rows)} APIs to {out}")


@main.command()
@click.option("--host", default=DEFAULT_HOST, show_default=True)
@click.option("--port", default=DEFAULT_PORT, show_default=True, type=int)
@click.pass_context
def serve(ctx, host, port):
    """Launch the NTXP-branded dashboard (loopback by default)."""
    from .server import serve as run
    run(host=host, port=port, db_override=ctx.obj.get("db"))


@main.command("mcp-serve")
@click.pass_context
def mcp_serve(ctx):
    """Run the MCP server exposing the API Log as tools for Claude."""
    from .mcp_server import serve
    serve(ctx.obj.get("db"))


if __name__ == "__main__":
    main()
