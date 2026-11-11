"""Contacts view: people/organizations in, hotlinked cards + vCards out."""
from __future__ import annotations

from ..registry import AppSpec, FieldSpec, FuncSpec

F = FieldSpec
FIELDS = [
    F("full_name", entity="person", joins="person_name"), F("first_name", entity="person"),
    F("last_name", entity="person"), F("title", entity="person"),
    F("email", entity="person", joins="email"), F("phone", entity="person", joins="phone"),
    F("address", entity="person", joins="address"), F("org_id", "int", "person"),
    F("name", entity="org", joins="org_name"), F("website", entity="org", joins="website"),
    F("grade", "float", "person", note="JEV exposure/sync gate"),
    F("labels", "list", "person"), F("projects", "list", "person"),
]


def _conn():
    from ntxp_contacts.db import connect, migrate
    c = connect(None)
    migrate(c)
    return c


def search_contacts(query: str, limit: int = 25):
    from ntxp_contacts.db.repository import Repository
    return Repository(_conn()).search(query, limit=limit)


def get_contact(contact_id: int):
    from ntxp_contacts.db.repository import Repository
    return Repository(_conn()).get_contact(int(contact_id))


def get_org(org_id: int):
    from ntxp_contacts.db.repository import Repository
    return Repository(_conn()).get_org(int(org_id))


def contact_context(query: str):
    from ntxp_contacts.context import HotlinkIndex
    from ntxp_contacts.db.repository import Repository
    conn = _conn()
    res = Repository(conn).search(query, 1)
    if not res:
        return {}
    cid = res[0].get("contact_id")
    return {"card": HotlinkIndex(conn).card(cid) if cid else res[0]}


def org_people(org_name: str, limit: int = 50):
    """People whose organization name matches (case-insensitive, normalised)."""
    from ntxp_contacts.normalize import org_name_norm
    conn = _conn()
    rows = conn.execute(
        "SELECT c.contact_id, c.full_name, c.title FROM contacts c "
        "JOIN organizations o ON o.org_id = c.org_id "
        "WHERE o.name_norm = ? AND c.is_deleted = 0 LIMIT ?",
        (org_name_norm(org_name), int(limit))).fetchall()
    return [dict(r) for r in rows]


SPEC = AppSpec(
    "contacts", "NTXP Contacts", "contacts.ntxpllc.cloud", "ntxp_contacts",
    "In: imports, CRM/Workspace sync, inline edits. Out: live table, reports, vCard/CardDAV, "
    "context hotlinks, signed peer webhooks.", FIELDS,
    [FuncSpec("search_contacts", "Full-text search people/orgs", {"query": "str", "limit": "int?"}, handler=search_contacts),
     FuncSpec("get_contact", "One contact with emails/phones/addresses", {"contact_id": "int"}, handler=get_contact),
     FuncSpec("get_org", "One organization", {"org_id": "int"}, handler=get_org),
     FuncSpec("contact_context", "Context card for a name/email/company", {"query": "str"}, handler=contact_context),
     FuncSpec("org_people", "People at an organization", {"org_name": "str", "limit": "int?"}, handler=org_people)])
