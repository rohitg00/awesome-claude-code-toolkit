"""In-memory dataclasses passed between loaders, resolver, and repository.

`CanonicalRecord` is the normalized shape every source loader produces and the
resolver/repository consume. It deliberately mirrors, but is decoupled from, the
SQL schema so loaders never touch SQL.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Email:
    email: str
    email_norm: str
    is_invalid: bool = False
    is_primary: bool = False


@dataclass
class Phone:
    phone_raw: str
    phone_e164: str | None = None
    kind: str = "main"  # main|office|cell|fax


@dataclass
class Address:
    line1: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    addr_norm: str = ""
    kind: str = "main"


@dataclass
class Tag:
    kind: str   # certification|region|trade|contact_type|cjp|member|event|source
    value: str


@dataclass
class CanonicalRecord:
    """One resolved unit from a source row: an org and/or a person plus comms."""
    source: str
    source_pk: str | None = None

    # Organization
    org_name: str | None = None
    org_name_norm: str | None = None
    website: str | None = None
    license_no: str | None = None
    org_attrs: dict[str, Any] = field(default_factory=dict)
    org_emails: list[Email] = field(default_factory=list)
    org_phones: list[Phone] = field(default_factory=list)
    org_addresses: list[Address] = field(default_factory=list)
    org_tags: list[Tag] = field(default_factory=list)

    # Contact (person)
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    name_norm: str | None = None
    title: str | None = None
    contact_attrs: dict[str, Any] = field(default_factory=dict)
    emails: list[Email] = field(default_factory=list)
    phones: list[Phone] = field(default_factory=list)
    addresses: list[Address] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)

    # Original raw row, for provenance.
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def has_contact(self) -> bool:
        return bool(self.name_norm)

    @property
    def has_org(self) -> bool:
        return bool(self.org_name_norm)
