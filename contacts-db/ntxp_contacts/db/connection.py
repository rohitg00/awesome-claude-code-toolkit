"""Connection factory. Dual-target: SQLite (default, embedded) or PostgreSQL
(cloud canonical store) when NTXP_DB_URL / a postgres:// override is set."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import db_path, db_url


def connect(path_or_url: str | Path | None = None):
    """Open the contacts DB.

    Returns a connection whose interface matches sqlite3.Connection closely
    enough that the repository, loaders and sync engine are backend-agnostic.
    A Postgres connection carries ``.backend == "postgres"``; the SQLite one
    has no such attribute (``getattr(conn, "backend", "sqlite")``).
    """
    dsn = db_url(path_or_url if isinstance(path_or_url, str) else None)
    if dsn:
        from .pg import connect_pg
        return connect_pg(dsn)

    p = db_path(path_or_url)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn
