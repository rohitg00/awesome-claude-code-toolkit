"""Concrete CRM adapters.

These define field mappings and transport. REST adapters are headless;
MCP-mediated adapters translate only (the agent performs the MCP calls via the
NTXP MCP server's sync tools). Adapters are intentionally thin and pluggable —
add a new CRM by adding a class with `system`, `transport`, and the four
mapping methods, then registering it.
"""
from __future__ import annotations

from typing import Iterator

from ..model import Address, CanonicalRecord, Email, Phone, Tag
from .base import LocalChange, PushResult, RemoteRecord, register_adapter


@register_adapter
class QuoAdapter:
    """Quo (phone/CRM) — has clear contact CRUD. Transport: REST.

    `pull`/`push` raise until API credentials are wired; `to_canonical` /
    `from_canonical` are usable now for planning and tests.
    """
    system = "quo"
    transport = "rest"

    def pull(self, since):  # pragma: no cover - needs live creds
        raise NotImplementedError("Set QUO_API_KEY and implement Quo REST pull.")

    def push(self, batch: list[LocalChange]) -> list[PushResult]:  # pragma: no cover
        raise NotImplementedError("Set QUO_API_KEY and implement Quo REST push.")

    def to_canonical(self, remote: RemoteRecord) -> CanonicalRecord:
        p = remote.payload
        rec = CanonicalRecord(source="quo", source_pk=remote.external_id, raw=p)
        rec.first_name = p.get("firstName") or p.get("first_name")
        rec.last_name = p.get("lastName") or p.get("last_name")
        rec.full_name = " ".join(x for x in (rec.first_name, rec.last_name) if x) or None
        from .. import normalize as N
        rec.name_norm = N.name_norm(rec.first_name, rec.last_name, rec.full_name)
        rec.org_name = p.get("company")
        rec.org_name_norm = N.org_name_norm(p.get("company") or "") or None
        for e in (p.get("emails") or ([p["email"]] if p.get("email") else [])):
            em = N.normalize_email(e)
            if em:
                rec.emails.append(Email(email=em, email_norm=em))
        for ph in (p.get("phoneNumbers") or ([p["phone"]] if p.get("phone") else [])):
            rec.phones.append(Phone(phone_raw=str(ph), phone_e164=N.normalize_phone(str(ph))))
        rec.tags.append(Tag("source", "quo"))
        return rec

    def from_canonical(self, rec: dict, external_id: str | None) -> dict:
        return {
            "firstName": rec.get("first_name"),
            "lastName": rec.get("last_name"),
            "company": rec.get("org_name"),
            "email": rec.get("email"),
            "phoneNumbers": [rec["phone"]] if rec.get("phone") else [],
        }


def _first(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return None


def _emails_phones(rec: CanonicalRecord, emails, phones) -> None:
    from .. import normalize as N
    for e in emails:
        em = N.normalize_email(e)
        if em:
            rec.emails.append(Email(email=em, email_norm=em))
    for ph in phones:
        if ph:
            rec.phones.append(Phone(phone_raw=str(ph), phone_e164=N.normalize_phone(str(ph))))


def _finish_person(rec: CanonicalRecord, system: str) -> CanonicalRecord:
    from .. import normalize as N
    rec.full_name = rec.full_name or " ".join(
        x for x in (rec.first_name, rec.last_name) if x) or None
    rec.name_norm = N.name_norm(rec.first_name, rec.last_name, rec.full_name)
    rec.org_name_norm = N.org_name_norm(rec.org_name or "") or None
    rec.tags.append(Tag("source", system))
    return rec


@register_adapter
class JobTreadAdapter:
    """JobTread — construction CRM/ERP. Transport: mcp (the `JobTread.query`
    GraphQL-style tool). Translate-only here; the agent runs the MCP calls."""
    system = "jobtread"
    transport = "mcp"

    def pull(self, since):  # pragma: no cover - MCP-mediated
        raise NotImplementedError("JobTread pull is performed by the agent via MCP (JobTread.query).")

    def push(self, batch):  # pragma: no cover - MCP-mediated
        raise NotImplementedError("JobTread push is performed by the agent via MCP (JobTread.query).")

    def to_canonical(self, remote: RemoteRecord) -> CanonicalRecord:
        p = remote.payload
        rec = CanonicalRecord(source=self.system, source_pk=remote.external_id, raw=p)
        rec.first_name = _first(p, "firstName", "first_name")
        rec.last_name = _first(p, "lastName", "last_name")
        rec.full_name = _first(p, "name", "fullName")
        rec.title = _first(p, "title", "role")
        rec.org_name = _first(p, "company", "organization", "account", "accountName")
        _emails_phones(
            rec,
            p.get("emails") or ([p["email"]] if p.get("email") else []),
            p.get("phones") or ([_first(p, "phone", "phoneNumber")] if _first(p, "phone", "phoneNumber") else []),
        )
        return _finish_person(rec, self.system)

    def from_canonical(self, rec: dict, external_id: str | None) -> dict:
        return {
            "name": rec.get("full_name"),
            "firstName": rec.get("first_name"),
            "lastName": rec.get("last_name"),
            "company": rec.get("org_name"),
            "email": rec.get("email"),
            "phone": rec.get("phone"),
        }


@register_adapter
class QuickBooksAdapter:
    """QuickBooks Online — Customers/Vendors. Transport: rest (QBO API).
    Translate-only until QBO OAuth credentials are wired."""
    system = "quickbooks"
    transport = "rest"

    def pull(self, since):  # pragma: no cover - needs live creds
        raise NotImplementedError("Wire QBO OAuth and implement QuickBooks pull.")

    def push(self, batch):  # pragma: no cover - needs live creds
        raise NotImplementedError("Wire QBO OAuth and implement QuickBooks push.")

    def to_canonical(self, remote: RemoteRecord) -> CanonicalRecord:
        p = remote.payload
        rec = CanonicalRecord(source=self.system, source_pk=remote.external_id, raw=p)
        rec.first_name = _first(p, "GivenName", "first_name")
        rec.last_name = _first(p, "FamilyName", "last_name")
        rec.full_name = _first(p, "DisplayName", "FullyQualifiedName")
        rec.org_name = _first(p, "CompanyName")
        email = (p.get("PrimaryEmailAddr") or {}).get("Address") if isinstance(p.get("PrimaryEmailAddr"), dict) else p.get("email")
        phone = (p.get("PrimaryPhone") or {}).get("FreeFormNumber") if isinstance(p.get("PrimaryPhone"), dict) else p.get("phone")
        _emails_phones(rec, [email] if email else [], [phone] if phone else [])
        return _finish_person(rec, self.system)

    def from_canonical(self, rec: dict, external_id: str | None) -> dict:
        out = {
            "GivenName": rec.get("first_name"),
            "FamilyName": rec.get("last_name"),
            "DisplayName": rec.get("full_name"),
            "CompanyName": rec.get("org_name"),
        }
        if rec.get("email"):
            out["PrimaryEmailAddr"] = {"Address": rec["email"]}
        if rec.get("phone"):
            out["PrimaryPhone"] = {"FreeFormNumber": rec["phone"]}
        return out


@register_adapter
class BuildingConnectedAdapter:
    """Autodesk BuildingConnected — Pro / Bid Board Pro contacts & users.
    Transport: mcp (the `bc_*` tools). Translate-only here."""
    system = "buildingconnected"
    transport = "mcp"

    def pull(self, since):  # pragma: no cover - MCP-mediated
        raise NotImplementedError("BuildingConnected pull is performed by the agent via MCP (bc_* tools).")

    def push(self, batch):  # pragma: no cover - MCP-mediated
        raise NotImplementedError("BuildingConnected push is performed by the agent via MCP (bc_* tools).")

    def to_canonical(self, remote: RemoteRecord) -> CanonicalRecord:
        p = remote.payload
        rec = CanonicalRecord(source=self.system, source_pk=remote.external_id, raw=p)
        rec.first_name = _first(p, "firstName", "first_name")
        rec.last_name = _first(p, "lastName", "last_name")
        rec.full_name = _first(p, "name", "fullName")
        rec.title = _first(p, "title", "position")
        rec.org_name = _first(p, "company", "companyName", "office", "officeName")
        _emails_phones(
            rec,
            p.get("emails") or ([p["email"]] if p.get("email") else []),
            p.get("phones") or ([_first(p, "phone", "phoneNumber")] if _first(p, "phone", "phoneNumber") else []),
        )
        return _finish_person(rec, self.system)

    def from_canonical(self, rec: dict, external_id: str | None) -> dict:
        return {
            "name": rec.get("full_name"),
            "firstName": rec.get("first_name"),
            "lastName": rec.get("last_name"),
            "company": rec.get("org_name"),
            "email": rec.get("email"),
            "phone": rec.get("phone"),
        }


@register_adapter
class LightfieldAdapter:
    """Lightfield CRM — reachable only via interactive MCP tools.

    Transport: mcp. The agent executes `read_from_lightfield` /
    `write_to_lightfield` from the sync plan this adapter helps build, then
    feeds results back through the NTXP MCP server. API paths/shapes are
    discovered at runtime via the Lightfield docs flow — never hardcoded here.
    """
    system = "lightfield"
    transport = "mcp"

    def pull(self, since):  # MCP-mediated: no direct network from here
        raise NotImplementedError("Lightfield pull is performed by the agent via MCP.")

    def push(self, batch):  # MCP-mediated
        raise NotImplementedError("Lightfield push is performed by the agent via MCP.")

    def to_canonical(self, remote: RemoteRecord) -> CanonicalRecord:
        from .. import normalize as N
        p = remote.payload
        rec = CanonicalRecord(source="lightfield", source_pk=remote.external_id, raw=p)
        rec.first_name = p.get("first_name")
        rec.last_name = p.get("last_name")
        rec.full_name = p.get("name") or " ".join(
            x for x in (rec.first_name, rec.last_name) if x) or None
        rec.name_norm = N.name_norm(rec.first_name, rec.last_name, rec.full_name)
        rec.org_name = p.get("company") or p.get("account")
        rec.org_name_norm = N.org_name_norm(rec.org_name or "") or None
        em = N.normalize_email(p.get("email"))
        if em:
            rec.emails.append(Email(email=em, email_norm=em))
        rec.tags.append(Tag("source", "lightfield"))
        return rec

    def from_canonical(self, rec: dict, external_id: str | None) -> dict:
        return {
            "first_name": rec.get("first_name"),
            "last_name": rec.get("last_name"),
            "company": rec.get("org_name"),
            "email": rec.get("email"),
            "phone": rec.get("phone"),
        }
