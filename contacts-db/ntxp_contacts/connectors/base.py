"""Whitelisted multi-platform connector middle-layer.

A Zapier-style layer: users securely connect their accounts (via the Zapier MCP
or a service's own connector), and this maps the contacts those services return
into the canonical store through the normal idempotent resolver/dedup pipeline.

Security model: a **service allowlist** gates what can be ingested (override with
``NTXP_CONNECTOR_ALLOWLIST``), and **no secrets live in the repo** — auth is held
by the connecting platform (Zapier / the service's OAuth); this layer only ever
receives already-fetched contact records.
"""
from __future__ import annotations

import os
from typing import Protocol

from .. import normalize as N
from ..model import CanonicalRecord, Email, Phone, Tag

# Default whitelist of platforms users may connect to pull contacts from.
_DEFAULT_ALLOW = {
    "google", "gmail", "google_contacts", "microsoft", "outlook", "office365",
    "apple", "icloud", "hubspot", "salesforce", "pipedrive", "mailchimp",
    "constant_contact", "quickbooks", "jobtread", "buildingconnected",
    "lightfield", "zapier", "linkedin", "slack", "zoho", "airtable", "notion",
    "formfill", "schedules",
}


def ALLOWED_SERVICES() -> set[str]:
    env = os.environ.get("NTXP_CONNECTOR_ALLOWLIST")
    if env:
        return {s.strip().lower() for s in env.split(",") if s.strip()}
    return set(_DEFAULT_ALLOW)


def is_allowed(service: str) -> bool:
    return (service or "").lower() in ALLOWED_SERVICES()


class Connector(Protocol):
    service: str

    def list_contacts(self, auth: dict) -> list[dict]:
        """Return raw contact dicts the agent fetched for this service."""
        ...


_NAME = ("name", "full_name", "fullName", "displayName", "Name", "DisplayName")
_FIRST = ("firstName", "first_name", "GivenName", "given_name", "first")
_LAST = ("lastName", "last_name", "FamilyName", "family_name", "last")
_EMAIL = ("email", "Email", "emailAddress", "email_address", "primaryEmail")
_PHONE = ("phone", "Phone", "phoneNumber", "mobile", "cell", "tel")
_COMPANY = ("company", "organization", "Company", "account", "org", "employer")
_TITLE = ("title", "jobTitle", "role", "position", "job_title")


def _pick(d: dict, keys) -> str | None:
    for k in keys:
        v = d.get(k)
        if v:
            return v if isinstance(v, str) else str(v)
    return None


def map_contact(service: str, raw: dict) -> CanonicalRecord | None:
    """Map a raw connector contact dict into a normalized CanonicalRecord."""
    src = f"connector:{service.lower()}"
    first = _pick(raw, _FIRST)
    last = _pick(raw, _LAST)
    full = _pick(raw, _NAME) or " ".join(x for x in (first, last) if x) or None
    if not (first or last) and full:
        first, last = N.parse_name(full)
    email_vals = []
    for k in _EMAIL:
        v = raw.get(k)
        if v:
            email_vals.append(v)
    for e in raw.get("emails") or []:
        email_vals.append(e.get("value") if isinstance(e, dict) else e)
    phone_vals = []
    for k in _PHONE:
        v = raw.get(k)
        if v:
            phone_vals.append(v)
    for p in raw.get("phones") or []:
        phone_vals.append(p.get("value") if isinstance(p, dict) else p)

    em0 = N.normalize_email(email_vals[0]) if email_vals else None
    nn = N.name_norm(first, last, full)
    if not nn and not em0:
        return None
    rec = CanonicalRecord(source=src, source_pk=em0 or nn, raw=raw)
    rec.first_name, rec.last_name, rec.full_name = first, last, full
    rec.name_norm = nn
    rec.title = _pick(raw, _TITLE)
    company = _pick(raw, _COMPANY)
    if company:
        rec.org_name = company
        rec.org_name_norm = N.org_name_norm(company) or None
    for e in email_vals:
        em = N.normalize_email(e)
        if em:
            rec.emails.append(Email(email=em, email_norm=em))
    for p in phone_vals:
        rec.phones.append(Phone(phone_raw=str(p), phone_e164=N.normalize_phone(str(p))))
    rec.tags.append(Tag("source", src))
    return rec


def ingest_contacts(conn, service: str, raws: list[dict]) -> dict:
    """Map + ingest a service's contacts into the canonical store.

    Raises PermissionError if the service is not on the allowlist.
    """
    if not is_allowed(service):
        raise PermissionError(
            f"service '{service}' is not on the connector allowlist "
            f"(set NTXP_CONNECTOR_ALLOWLIST to permit it)")
    from ..collect import ingest
    recs = [r for r in (map_contact(service, raw) for raw in raws) if r]
    result = ingest(conn, recs, origin=f"connector:{service.lower()}")
    result["service"] = service.lower()
    return result
