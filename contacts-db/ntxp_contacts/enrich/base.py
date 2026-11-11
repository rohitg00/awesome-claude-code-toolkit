"""Enrichment resolver framework + JEV candidate grading.

A *resolver* proposes candidate values for a contact's missing/weak fields. Every
candidate is graded (source weight + cross-source corroboration) before it is
stored; nothing overwrites canonical data automatically — high-grade candidates
are applied on confirm, and LinkedIn/photo always route through confirmation.

Built-in resolvers are deterministic and offline (Gravatar/Libravatar URLs,
company-website and public-entity-directory derivation, LinkedIn search-candidate
generation). Heavy OSINT tools (holehe, maigret, GHunt) are declared in
EXTERNAL_RESOLVERS: the agent runs them out-of-band and feeds candidates back via
`generate(..., extra=...)` — they are never scraped from package code or bundled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

PRIMARY_FIELDS = ("email", "phone", "address", "website", "photo", "linkedin")


@dataclass
class Candidate:
    field: str                 # one of PRIMARY_FIELDS
    value: str
    source: str
    grade: float = 0.0
    evidence: dict = field(default_factory=dict)


class Resolver(Protocol):
    name: str
    provides: tuple[str, ...]

    def resolve(self, contact: dict) -> list[Candidate]:
        ...


RESOLVERS: dict[str, Resolver] = {}


def register(cls):
    RESOLVERS[cls.name] = cls()
    return cls


# Heavy OSINT tools the agent runs out-of-band (free, GitHub, data-driven),
# chosen for breadth + speed. The agent invokes these, then calls
# generate(conn, extra=[Candidate(...), ...]) with what they return.
EXTERNAL_RESOLVERS = {
    "holehe": {
        "github": "megadose/holehe",
        "input": "email",
        "provides": ("account",),
        "note": "email -> 120+ sites via password-recovery probes; fast, no API keys.",
    },
    "maigret": {
        "github": "soxoj/maigret",
        "input": "username",
        "provides": ("account", "photo"),
        "note": "username -> 2000+ sites; broader/faster than Sherlock; returns profile URLs + avatars.",
    },
    "ghunt": {
        "github": "mxrch/GHunt",
        "input": "email",
        "provides": ("account", "photo", "name"),
        "note": "Google account intel for an email (profile photo, name).",
    },
}
