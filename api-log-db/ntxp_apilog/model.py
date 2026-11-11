"""In-memory dataclasses passed between the CLI/MCP layer and the repository.

`ApiEntry` mirrors, but is decoupled from, the SQL schema. Secret fields hold
*plaintext* in memory; the repository encrypts them on write and the cipher
decrypts on read. Callers never touch ciphertext directly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


def name_norm(name: str | None) -> str:
    """Normalized dedup key for an API: lowercased, collapsed whitespace."""
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip().lower())


def parse_tags(value: str | list[str] | None) -> list[str]:
    """Coerce a comma-separated string (or list) into a clean tag list."""
    if isinstance(value, list):
        items = value
    else:
        items = (value or "").split(",")
    return [t.strip() for t in items if t and t.strip()]


@dataclass
class ApiEntry:
    """One registered API: where it lives, how to authenticate, what it costs."""

    name: str
    provider: str | None = None
    category: str | None = None          # see config.CATEGORIES
    base_url: str | None = None
    docs_url: str | None = None
    login_url: str | None = None
    purpose: str | None = None           # free text — helps Claude match intent
    auth_type: str = "api_key"           # see config.AUTH_TYPES

    # --- secret fields (plaintext in memory, encrypted at rest) ---
    api_key: str | None = None           # the token/secret used in requests
    key_number: str | None = None        # key id / account / project number
    login_user: str | None = None        # username/email for the provider console
    login_secret: str | None = None      # console password

    # --- cost ---
    cost_model: str | None = None        # e.g. "$0.01 / 1K tokens", "$20/mo flat"
    currency: str = "USD"
    monthly_budget: float | None = None

    status: str = "active"               # see config.STATUSES
    owner: str | None = None             # who registered it
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)

    api_id: int | None = None

    @property
    def name_norm(self) -> str:
        return name_norm(self.name)


@dataclass
class UsageEvent:
    """One cost/usage record against an API (drives the running spend total)."""

    api_id: int
    cost: float = 0.0
    currency: str = "USD"
    units: float | None = None           # tokens / requests / GB ...
    unit_kind: str | None = None
    description: str | None = None
    requested_by: str | None = None      # system | skill:<name> | user:<email>
    origin: str = "cli"                  # cli | mcp | dashboard
