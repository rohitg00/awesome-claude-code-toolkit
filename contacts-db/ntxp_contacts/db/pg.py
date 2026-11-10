"""PostgreSQL backend for the NTXP contacts store.

The repository layer is authored once in the SQLite idiom. This wrapper lets
that same SQL run against Postgres by translating the handful of dialect
differences at execute time:

* ``?``            -> ``%s``                 (parameter placeholders)
* ``IFNULL(``      -> ``COALESCE(``
* ``datetime('now')`` -> ``now()``
* ``GROUP_CONCAT(x[, sep])`` -> ``string_agg(x::text, sep)``
* ``INSERT OR IGNORE INTO t VALUES (...)`` -> ``... ON CONFLICT DO NOTHING``

Everything else in the schema (expression unique indexes, ``ON CONFLICT``,
``RETURNING``, ``CHECK ((a IS NOT NULL) <> (b IS NOT NULL))``, CTEs, ``||``
concatenation, temp tables) is already valid Postgres.

Rows are returned as :class:`HybridRow`, which — like ``sqlite3.Row`` — supports
both ``row["col"]`` and ``row[0]`` access and ``dict(row)``, so the repository
needs no row-access changes.
"""
from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any, Iterable, Sequence

try:  # psycopg (v3) is an optional dependency; only needed for the PG backend.
    import psycopg
except ModuleNotFoundError:  # pragma: no cover - import-time guard
    psycopg = None  # type: ignore


# --- SQL translation (SQLite idiom -> Postgres) -----------------------------
_GROUP_CONCAT_2 = re.compile(r"GROUP_CONCAT\(\s*([^,()]+?)\s*,\s*('[^']*')\s*\)", re.I)
_GROUP_CONCAT_1 = re.compile(r"GROUP_CONCAT\(\s*([^,()]+?)\s*\)", re.I)
_INSERT_OR_IGNORE = re.compile(
    r"INSERT\s+OR\s+IGNORE\s+INTO\s+(.+?VALUES\s*\(.*?\))", re.I | re.S)


def translate(sql: str) -> str:
    """Rewrite one SQLite-idiom statement to its Postgres equivalent."""
    sql = sql.replace("IFNULL(", "COALESCE(")
    sql = sql.replace("datetime('now')", "now()")
    sql = _GROUP_CONCAT_2.sub(r"string_agg((\1)::text, \2)", sql)
    sql = _GROUP_CONCAT_1.sub(r"string_agg((\1)::text, ',')", sql)
    sql = _INSERT_OR_IGNORE.sub(r"INSERT INTO \1 ON CONFLICT DO NOTHING", sql)
    # Parameter placeholders last (no literal '?' appears in our SQL strings).
    sql = sql.replace("?", "%s")
    return sql


class HybridRow(Mapping):
    """A psycopg row supporting str keys, int positions, and dict()."""

    __slots__ = ("_cols", "_vals", "_idx")

    def __init__(self, cols: Sequence[str], vals: Sequence[Any]):
        self._cols = cols
        self._vals = vals
        self._idx = {c: i for i, c in enumerate(cols)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        return self._vals[self._idx[key]]

    def __iter__(self):
        return iter(self._cols)

    def __len__(self):
        return len(self._cols)

    def keys(self):  # lets dict(row) copy by key
        return list(self._cols)


def _row_factory(cursor):
    desc = cursor.description
    cols = [d.name for d in desc] if desc else []

    def make(values):
        return HybridRow(cols, values)

    return make


_SCHEMA_RE = re.compile(r"^[a-z_][a-z0-9_]{0,40}$")


def pg_schema() -> str | None:
    """Dedicated schema for this app (NTXP_PG_SCHEMA), validated. None = the
    server/role default (public). Use a dedicated schema whenever the Supabase
    project is shared with other apps, so nothing here can touch their tables."""
    s = os.environ.get("NTXP_PG_SCHEMA", "").strip().lower()
    if not s:
        return None
    if not _SCHEMA_RE.match(s):
        raise ValueError("NTXP_PG_SCHEMA must match [a-z_][a-z0-9_]{0,40}")
    return s


class PgConnection:
    """A minimal sqlite3.Connection-compatible facade over psycopg.

    With a dedicated schema configured, every transaction is primed with
    ``SET LOCAL search_path`` so it also works behind a transaction-mode pooler
    (Supavisor port 6543 / PgBouncer), where session-level SET does not survive
    between transactions."""

    backend = "postgres"

    def __init__(self, raw: "psycopg.Connection", schema: str | None = None):
        self._raw = raw
        self.schema = schema
        self._fresh = True          # next statement starts a new transaction

    def _prime(self) -> None:
        if self.schema and self._fresh:
            self._raw.execute(f'SET LOCAL search_path TO "{self.schema}", pg_catalog')
        self._fresh = False

    # Mirrors sqlite3.Connection.execute: runs SQL, returns a cursor that is
    # iterable and exposes fetchone()/fetchall().
    def execute(self, sql: str, params: Sequence[Any] | None = None):
        self._prime()
        cur = self._raw.cursor(row_factory=_row_factory)
        cur.execute(translate(sql), tuple(params) if params else None)
        return cur

    def executemany(self, sql: str, seq: Iterable[Sequence[Any]]):
        self._prime()
        cur = self._raw.cursor(row_factory=_row_factory)
        cur.executemany(translate(sql), [tuple(p) for p in seq])
        return cur

    def executescript(self, sql: str) -> None:
        # psycopg runs a multi-statement, parameter-free string in one call.
        self._prime()
        self._raw.execute(sql)

    def commit(self) -> None:
        self._raw.commit()
        self._fresh = True

    def rollback(self) -> None:
        self._raw.rollback()
        self._fresh = True

    def close(self) -> None:
        self._raw.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        return False


def connect_pg(dsn: str) -> PgConnection:
    if psycopg is None:  # pragma: no cover - surfaced only without the extra
        raise RuntimeError(
            "PostgreSQL backend requested (NTXP_DB_URL set) but 'psycopg' is "
            "not installed. Install the extra: pip install 'ntxp-contacts[postgres]'."
        )
    kwargs = {"autocommit": False}
    if _needs_no_prepare(dsn):
        # Supabase's transaction-mode pooler (Supavisor, port 6543) / PgBouncer
        # reuse server connections between transactions, which breaks psycopg's
        # server-side prepared statements ("prepared statement ... does not exist").
        kwargs["prepare_threshold"] = None
    raw = psycopg.connect(dsn, **kwargs)
    schema = pg_schema()
    if schema:
        # Create the schema only if missing (an existing one needs no privilege).
        exists = raw.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", (schema,)).fetchone()
        if not exists:
            raw.execute(f'CREATE SCHEMA "{schema}"')
        raw.commit()
    return PgConnection(raw, schema)


def _needs_no_prepare(dsn: str) -> bool:
    import os
    if os.environ.get("NTXP_PG_NO_PREPARE", "").lower() in ("1", "true", "yes"):
        return True
    d = dsn.lower()
    return ":6543/" in d or "pooler.supabase" in d or "pgbouncer=true" in d
