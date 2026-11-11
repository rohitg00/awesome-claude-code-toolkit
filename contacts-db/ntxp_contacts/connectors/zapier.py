"""Zapier as the whitelisted middle layer.

Zapier connects 9,000+ apps; its MCP (`mcp__Zapier__*`) is the secure auth broker
— users authorize their accounts in Zapier, and the agent runs Zapier *read*
actions to fetch contacts, then hands the rows here for mapping + ingestion. No
account secrets touch this repo.

This module is a thin descriptor + convenience; the actual Zapier calls are made
by the agent via the Zapier MCP (outward-facing — gate live workflow creation on
explicit user approval).
"""
from __future__ import annotations

from .base import ingest_contacts

# How the agent drives Zapier, documented for the orchestration layer.
ZAPIER = {
    "mcp": "mcp__Zapier__*",
    "discover": "discover_zapier_actions(app='<service> find contact')",
    "inspect": "inspect_zapier_actions(...)",
    "run_read": "execute_zapier_read_action(selected_api, action, params)  # pull contacts",
    "run_write": "execute_zapier_write_action(...)  # push a contact (approval-gated)",
    "note": "User authorizes accounts in Zapier; secrets stay in Zapier, never here.",
}


def ingest_zapier(conn, service: str, rows: list[dict]) -> dict:
    """Ingest contact rows the agent fetched via a Zapier read action for
    `service` (must be on the allowlist)."""
    return ingest_contacts(conn, service, rows)
