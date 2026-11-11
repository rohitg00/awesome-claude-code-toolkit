"""``ntxp-contracts`` — the command-line surface for the Master Contracts DB.

Has no hard dependency on click so the package installs lean; falls back to a
small argparse driver if click is absent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import __version__, branding
from .config import db_path
from .db import connect, migrate
from .db.repository import Repository
from .importer import import_csv
from .model import Contract


def _repo(db_override=None) -> Repository:
    conn = connect(db_override)
    migrate(conn)
    return Repository(conn)


def cmd_init(args):
    repo = _repo(args.db)
    print(f"Initialized contracts DB at {db_path(args.db)}")
    print(json.dumps(repo.stats(), indent=2))


def cmd_add(args):
    repo = _repo(args.db)
    cid, is_new = repo.upsert_contract(Contract(
        contract_title=args.title, contract_no=args.number,
        contract_type=args.type, owner_entity=args.owner), actor="cli")
    repo.conn.commit()
    print(f"{'created' if is_new else 'updated'} contract #{cid}: {args.title}")


def cmd_list(args):
    repo = _repo(args.db)
    rows = repo.list_contracts()
    if args.json:
        print(json.dumps(rows, indent=2, default=str)); return
    if not rows:
        print("(no contracts)"); return
    for c in rows:
        flag = "EXEC" if c["is_executed"] else "UNEXEC"
        print(f"#{c['contract_id']:>3}  {c.get('contract_no') or '-':<16} "
              f"{(c['contract_title'] or '')[:40]:<40} exp:{c.get('expiration_date') or '-':<11} "
              f"coeff:{c.get('coefficient_multiplier') or '-':<6} [{flag}]")


def cmd_query(args):
    repo = _repo(args.db)
    print(json.dumps(repo.search(args.text, limit=args.limit), indent=2, default=str))


def cmd_show(args):
    repo = _repo(args.db)
    prof = repo.get_profile(args.id)
    if not prof:
        print("not found"); sys.exit(1)
    print(json.dumps(prof, indent=2, default=str))


def cmd_import(args):
    repo = _repo(args.db)
    summary = import_csv(repo, args.file, source=args.source)
    print(json.dumps(summary, indent=2))


def cmd_stats(args):
    print(json.dumps(_repo(args.db).stats(), indent=2))


def cmd_brand(args):
    print(json.dumps(branding.resolve_brand().to_dict(), indent=2, default=str))


def cmd_serve_web(args):
    from .web import serve
    serve(db_override=args.db, host=args.host, port=args.port)


def cmd_mcp_serve(args):
    from .mcp_server import serve
    serve(db_override=args.db)


def build_parser():
    import argparse
    p = argparse.ArgumentParser(prog="ntxp-contracts",
                                description="NTXP Master Contracts database.")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--db", default=None, help="Path to the SQLite DB.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create the DB and run migrations.").set_defaults(fn=cmd_init)

    a = sub.add_parser("add", help="Add or update a contract.")
    a.add_argument("title"); a.add_argument("--number"); a.add_argument("--type")
    a.add_argument("--owner"); a.set_defaults(fn=cmd_add)

    l = sub.add_parser("list", help="List contracts.")
    l.add_argument("--json", action="store_true"); l.set_defaults(fn=cmd_list)

    q = sub.add_parser("query", help="Full-text search.")
    q.add_argument("text"); q.add_argument("--limit", type=int, default=50)
    q.set_defaults(fn=cmd_query)

    s = sub.add_parser("show", help="Show one contract profile (with jobs/sales).")
    s.add_argument("id", type=int); s.set_defaults(fn=cmd_show)

    im = sub.add_parser("import", help="Idempotently import a CSV contract log.")
    im.add_argument("file"); im.add_argument("--source", default="csv")
    im.set_defaults(fn=cmd_import)

    sub.add_parser("stats", help="Counts + unexecuted flag totals.").set_defaults(fn=cmd_stats)
    sub.add_parser("brand", help="Print the brand resolved from Claude settings.").set_defaults(fn=cmd_brand)

    w = sub.add_parser("serve-web", help="Run the editable dashboard + profile web app.")
    w.add_argument("--host", default=None); w.add_argument("--port", type=int, default=None)
    w.set_defaults(fn=cmd_serve_web)

    m = sub.add_parser("mcp-serve", help="Run the MCP server (stdio) for Claude tools.")
    m.set_defaults(fn=cmd_mcp_serve)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
