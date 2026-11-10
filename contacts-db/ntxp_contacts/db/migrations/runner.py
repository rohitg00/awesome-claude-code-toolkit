"""Versioned SQL migration runner (no Alembic).

Applies `NNNN_*.sql` files in order, tracking the highest applied version in a
`schema_version` table. Re-running is a cheap no-op once everything is applied.

Dual-target: SQLite reads `NNNN_*.sql`; Postgres reads `NNNN_*.postgres.sql`
when present (falling back to the base file otherwise). The runner detects the
backend from the connection (``getattr(conn, "backend", "sqlite")``).
"""
from __future__ import annotations

import re
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent
_FILE_RE = re.compile(r"^(\d{4})_.*\.sql$")
_PG_SUFFIX = ".postgres.sql"


# Supabase exposes public-schema tables to its anon/authenticated roles through
# the auto-generated Data API. This database holds contact PII and is reached
# only server-side (owner/service role, which bypass RLS), so after every
# migration batch we idempotently enable RLS with NO policies (deny-all) on every
# table and revoke the API roles' grants. Harmless on plain Postgres. Re-running
# it each time means a future migration's new table can never ship exposed.
RLS_LOCKDOWN_SQL = """
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
  END LOOP;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
    REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated;
    REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM authenticated;
  END IF;
END $$;
"""


def _backend(conn) -> str:
    return getattr(conn, "backend", "sqlite")


def _ensure_version_table(conn) -> None:
    if _backend(conn) == "postgres":
        ddl = ("CREATE TABLE IF NOT EXISTS schema_version ("
               " version INTEGER PRIMARY KEY,"
               " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
    else:
        ddl = ("CREATE TABLE IF NOT EXISTS schema_version ("
               " version INTEGER PRIMARY KEY,"
               " applied_at TEXT NOT NULL DEFAULT (datetime('now')))")
    conn.execute(ddl)


def _current_version(conn) -> int:
    row = conn.execute("SELECT COALESCE(MAX(version), 0) AS v FROM schema_version").fetchone()
    return int(row["v"])


def discover(backend: str = "sqlite") -> list[tuple[int, Path]]:
    """Return (version, path) pairs for the given backend, lowest first.

    For Postgres, a `NNNN_*.postgres.sql` file overrides the base `NNNN_*.sql`
    of the same version number; versions with only a base file use it.
    """
    pg = backend == "postgres"
    chosen: dict[int, Path] = {}
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = _FILE_RE.match(f.name)
        if not m:
            continue
        version = int(m.group(1))
        is_pg_file = f.name.endswith(_PG_SUFFIX)
        if pg:
            if is_pg_file:
                chosen[version] = f  # pg-specific always wins
            else:
                chosen.setdefault(version, f)
        else:
            if not is_pg_file:
                chosen[version] = f
    return sorted(chosen.items())


def migrate(conn) -> list[int]:
    """Apply all pending migrations. Returns the list of versions applied."""
    backend = _backend(conn)
    _ensure_version_table(conn)
    conn.commit()
    current = _current_version(conn)
    applied: list[int] = []
    for version, path in discover(backend):
        if version <= current:
            continue
        sql = path.read_text(encoding="utf-8")
        try:
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        applied.append(version)
    if backend == "postgres" and applied:
        conn.executescript(RLS_LOCKDOWN_SQL)
        conn.commit()
    return applied
