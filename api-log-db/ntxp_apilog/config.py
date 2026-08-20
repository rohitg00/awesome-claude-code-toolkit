"""Runtime configuration for the NTXP API Log.

Every knob is overridable via environment variables so all NTXP tools — and the
dashboard, CLI, and MCP server — point at the *same* shared database and use the
*same* encryption key without code changes.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Database location -------------------------------------------------------
# Single source of truth, shared by every user/tool. Lives outside the repo
# (the repo descends from a public marketplace; real keys are never committed).
# Point NTXP_APILOG_DB_PATH at a synced/shared location (e.g. a team drive) so
# everyone reads and writes one database.
DEFAULT_DB_PATH = Path.home() / ".ntxp" / "apilog.db"

# --- Encryption key location -------------------------------------------------
# Secret fields (API keys, key numbers, login passwords) are encrypted at rest.
# The key is read from NTXP_APILOG_KEY (a urlsafe-base64 32-byte Fernet key) or,
# if unset, from this file — auto-generated on first use with 0600 perms.
DEFAULT_KEY_PATH = Path.home() / ".ntxp" / "apilog.key"

# --- Dashboard server defaults ----------------------------------------------
# Bind to loopback by default: credentials should never be exposed on a network
# interface without an explicit, deliberate choice.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


def db_path(override: str | os.PathLike | None = None) -> Path:
    """Resolve the DB path: explicit override > NTXP_APILOG_DB_PATH > default."""
    if override:
        return Path(override).expanduser()
    env = os.environ.get("NTXP_APILOG_DB_PATH")
    if env:
        return Path(env).expanduser()
    return DEFAULT_DB_PATH


def key_path() -> Path:
    """Resolve the on-disk encryption-key path (NTXP_APILOG_KEY_PATH > default)."""
    env = os.environ.get("NTXP_APILOG_KEY_PATH")
    return Path(env).expanduser() if env else DEFAULT_KEY_PATH


# --- Controlled vocabularies (kept loose; used for filtering/UX only) --------
CATEGORIES = [
    "llm", "payments", "maps", "email", "sms", "storage", "search",
    "auth", "data", "analytics", "infra", "crm", "government", "other",
]

AUTH_TYPES = ["api_key", "bearer", "basic", "oauth2", "none"]

STATUSES = ["active", "inactive", "revoked", "trial"]
