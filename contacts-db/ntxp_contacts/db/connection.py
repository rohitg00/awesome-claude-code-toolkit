"""SQLite connection factory: WAL, foreign keys, row factory."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import db_path


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    """Open (creating parent dirs as needed) the contacts DB."""
    p = db_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn
