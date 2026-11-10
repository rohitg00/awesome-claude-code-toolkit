"""Runtime configuration for the NTXP contacts database.

All knobs are overridable via environment variables so other NTXP tools can
point at the same master DB without code changes.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Database location -------------------------------------------------------
# Single source of truth. Lives outside the repo (the repo descends from a
# public marketplace; real contact PII is never committed).
DEFAULT_DB_PATH = Path.home() / ".ntxp" / "contacts.db"


def _looks_like_url(s: str) -> bool:
    return s.startswith(("postgres://", "postgresql://"))


def db_url(override: str | os.PathLike | None = None) -> str | None:
    """Resolve a Postgres DSN if one is configured, else None (use SQLite).

    Precedence: an explicit ``postgres://`` override > ``NTXP_DB_URL`` env.
    A non-URL override (a path) means "use SQLite" and returns None so the
    caller falls through to :func:`db_path`.
    """
    if override:
        # An explicit override wins outright: a postgres:// URL selects Postgres;
        # any other explicit value is a filesystem path and forces SQLite (return
        # None) — it must never fall through to NTXP_DB_URL, or `ntxp --db
        # /tmp/x.db` could mutate the cloud database.
        return override if (isinstance(override, str) and _looks_like_url(override)) else None
    env = os.environ.get("NTXP_DB_URL")
    if env and _looks_like_url(env):
        return env
    return None


def backend(override: str | os.PathLike | None = None) -> str:
    """Which engine a connection for `override` will use: 'postgres' | 'sqlite'."""
    return "postgres" if db_url(override) else "sqlite"


def contacts_url() -> str:
    """Base URL of the user-facing contacts page. Hotlinks point here with a
    focus/filter query so clicking a contact opens the page filtered to it."""
    return os.environ.get("NTXP_CONTACTS_URL", "https://contacts.ntxpllc.com").rstrip("/")


def db_path(override: str | os.PathLike | None = None) -> Path:
    """Resolve the SQLite DB path: explicit override > NTXP_DB_PATH > default."""
    if override and not (isinstance(override, str) and _looks_like_url(override)):
        return Path(override).expanduser()
    env = os.environ.get("NTXP_DB_PATH")
    if env:
        return Path(env).expanduser()
    return DEFAULT_DB_PATH


# --- Identity-resolution thresholds -----------------------------------------
MATCH_THRESHOLD = 0.85       # >= auto-merge
REVIEW_THRESHOLD = 0.65      # [REVIEW_THRESHOLD, MATCH_THRESHOLD) -> human queue

# Weights for the scored match (must sum to 1.0).
SCORE_WEIGHTS = {
    "name": 0.45,
    "org": 0.30,
    "phone": 0.20,
    "state": 0.05,
}

# --- Conflict resolution -----------------------------------------------------
# Source trust ranking (higher wins ties when filling canonical fields).
SOURCE_TRUST = {
    "approved_subs": 50,
    "buildingconnectd": 40,
    "tips": 30,
    "luncheon": 20,
    "cjp_pdf": 10,
}

# Fields where the local master always wins over a remote CRM value.
MASTER_WINS_FIELDS = {"license_no", "certifications"}

# --- Reconciliation hub ------------------------------------------------------
# Lightfield is the canonical first source: all tools reconcile back to it, and
# on a field conflict a Lightfield value outranks every other system's. The
# reconcile orchestrator applies the canonical source before the rest so that
# gap-filling from lower-ranked systems never pre-empts canonical values.
CANONICAL_SOURCE = "lightfield"

# Higher rank wins a field conflict (used by the reconcile planner to decide
# which side a disagreement should resolve toward, and to flag the other).
SYSTEM_PRECEDENCE = {
    "lightfield": 100,     # canonical
    "jobtread": 60,
    "quickbooks": 55,
    "buildingconnected": 50,
    "quo": 40,
    # Google Workspace sweep channels (self-reported signature highest)
    "gmail_signature": 48,
    "gcontacts": 45,
    "gmail_from": 40,
    "people_api": 35,
    "calendar_organizer": 35,
    "gmail_to": 25,
    "calendar_attendee": 25,
    "drive_author": 22,
    # bundled spreadsheet/import sources rank below live CRMs
    "approved_subs": 30,
    "buildingconnectd": 28,
    "tips": 20,
    "luncheon": 15,
    "cjp_pdf": 10,
}

# Default country region for phone parsing.
DEFAULT_PHONE_REGION = "US"
