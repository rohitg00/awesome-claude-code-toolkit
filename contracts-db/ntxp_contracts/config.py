"""Runtime configuration for the NTXP Master Contracts database.

Every knob is overridable via an environment variable so other NTXP tools can
point at the same master DB (and the same web dashboard) without code changes.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Database location -------------------------------------------------------
# Single source of truth. Lives outside the repo (this directory descends from
# a public marketplace; real contract data and signed PDFs are never committed).
DEFAULT_DB_PATH = Path.home() / ".ntxp" / "contracts.db"


def db_path(override: str | os.PathLike | None = None) -> Path:
    """Resolve the DB path: explicit override > NTXP_CONTRACTS_DB > default."""
    if override:
        return Path(override).expanduser()
    env = os.environ.get("NTXP_CONTRACTS_DB")
    if env:
        return Path(env).expanduser()
    return DEFAULT_DB_PATH


# --- Defaults requested by the business -------------------------------------
# Recipient on every contract unless overridden (NTXP is always the recipient).
DEFAULT_RECIPIENT = os.environ.get("NTXP_DEFAULT_RECIPIENT", "NTXP LLC")

# The three contract families the log tracks. Kept as a controlled vocabulary
# so the dashboard, importer and MCP layer agree, but new types only need to be
# added here — nothing else hard-codes the set.
CONTRACT_TYPES = (
    "Job Order Contract",
    "Cooperative Contract",
    "Master Subcontract Agreement",
)

# Suggested allowable-scope terms surfaced as quick-pick chips in the UI. Free
# text is always allowed; this is a convenience list, not a constraint.
SCOPE_VOCAB = (
    "General Contractor",
    "Electrical",
    "Trade Work",
    "Professional Services",
    "Painting",
    "Roofing",
    "HVAC",
    "Plumbing",
    "Mechanical",
    "Civil / Sitework",
    "Concrete",
)

# --- Web dashboard -----------------------------------------------------------
WEB_HOST = os.environ.get("NTXP_CONTRACTS_WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.environ.get("NTXP_CONTRACTS_WEB_PORT", "8787"))

# How often (ms) the dashboard polls the API so concurrent editors see each
# other's saved fields without a refresh.
WEB_POLL_MS = int(os.environ.get("NTXP_CONTRACTS_POLL_MS", "4000"))
