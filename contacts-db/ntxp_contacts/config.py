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


def db_path(override: str | os.PathLike | None = None) -> Path:
    """Resolve the DB path: explicit override > NTXP_DB_PATH > default."""
    if override:
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

# Default country region for phone parsing.
DEFAULT_PHONE_REGION = "US"
