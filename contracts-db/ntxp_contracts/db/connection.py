"""SQLite connection factory: WAL, foreign keys, row factory.

WAL mode is what lets multiple dashboard editors (and other NTXP tools) write
concurrently without blocking each other — the basis of "multiple users can
edit at once without conflict" at the storage layer.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import db_path


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    """Open (creating parent dirs as needed) the contracts DB."""
    p = db_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn
