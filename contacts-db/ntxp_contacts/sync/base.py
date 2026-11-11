"""Sync adapter interface + shared data shapes.

Every CRM integration implements `CrmAdapter`. Two transports share the same
interface:
  * transport="rest"  — headless adapters that call a CRM REST API directly.
  * transport="mcp"   — CRMs reachable only via interactive MCP tools. These
                        adapters do NOT touch the network; they translate
                        between canonical records and remote payloads, and the
                        agent (driven by the NTXP MCP server's sync_plan /
                        record_sync_result tools) performs the actual MCP calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Literal, Protocol

from ..model import CanonicalRecord


@dataclass
class RemoteRecord:
    external_id: str
    payload: dict[str, Any]
    modified_at: str | None = None


@dataclass
class LocalChange:
    entity_type: str            # contact|org
    entity_id: int
    op: str                     # insert|update|delete
    external_id: str | None     # None => create remote
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class PushResult:
    entity_type: str
    entity_id: int
    external_id: str
    remote_hash: str
    ok: bool = True
    error: str | None = None


class CrmAdapter(Protocol):
    system: str
    transport: Literal["rest", "mcp"]

    def pull(self, since: str | None) -> Iterator[RemoteRecord]:
        ...

    def push(self, batch: list[LocalChange]) -> list[PushResult]:
        ...

    def to_canonical(self, remote: RemoteRecord) -> CanonicalRecord:
        ...

    def from_canonical(self, rec: dict, external_id: str | None) -> dict:
        ...


# Adapter registry, populated by each adapter module on import.
ADAPTERS: dict[str, type] = {}


def register_adapter(cls):
    ADAPTERS[cls.system] = cls
    return cls


def get_adapter(system: str):
    from . import adapters  # noqa: F401  (triggers registration)
    if system not in ADAPTERS:
        raise KeyError(f"no adapter for '{system}'. Known: {sorted(ADAPTERS)}")
    return ADAPTERS[system]()
