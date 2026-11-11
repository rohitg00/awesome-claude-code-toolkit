"""Versioned SQL migration runner (no Alembic).

Applies `NNNN_*.sql` files in order, tracking the highest applied version in a
`schema_version` table. Re-running is a cheap no-op once everything is applied.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent
_FILE_RE = re.compile(r"^(\d{4})_.*\.sql$")


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        " version INTEGER PRIMARY KEY,"
        " applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )


def _current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(version), 0) AS v FROM schema_version").fetchone()
    return int(row["v"])


def discover() -> list[tuple[int, Path]]:
    out = []
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = _FILE_RE.match(f.name)
        if m:
            out.append((int(m.group(1)), f))
    return out


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Apply all pending migrations. Returns the list of versions applied."""
    _ensure_version_table(conn)
    current = _current_version(conn)
    applied: list[int] = []
    for version, path in discover():
        if version <= current:
            continue
        sql = path.read_text(encoding="utf-8")
        with conn:  # one transaction per migration
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))
        applied.append(version)
    return applied
