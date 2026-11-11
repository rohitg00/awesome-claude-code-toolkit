"""Google Workspace sweep collectors.

The nightly sweep's primary agent casts a wide net across all NTXP Workspace
users and platforms (Gmail, Google Contacts, Calendar, Drive, People, Maps) and
hands the raw results here. This module does **deterministic extraction only** —
no inference, no qualifying — turning each Workspace object into normalized
CanonicalRecords tagged with the *channel* they came from and the data point's
own date. Qualification (source/age/distance/corroboration grading) is Layer F's
job, run afterward.

Channel = the `source` each record carries, so the grader's distance-from-person
map (qualify.grader.DISTANCE) scores a Gmail signature or a saved Google Contact
as closest and a Drive-doc mention as farthest. The agent is expected to
normalize each Workspace API response into the small input shapes documented on
each extractor before calling — keeping live-API variance in the skill layer and
the deterministic mapping here.
"""
from __future__ import annotations

from email.utils import getaddresses
from typing import Iterable

from .. import normalize as N
from ..model import CanonicalRecord, Email, Phone, Tag

# Channels, ordered closest -> farthest from the person. Registered in
# qualify.grader.DISTANCE so grading reflects provenance proximity.
CHANNELS = (
    "gcontacts", "gmail_signature", "people_api", "gmail_from",
    "calendar_organizer", "gmail_to", "calendar_attendee", "drive_author",
)

_FREEMAIL = {
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "aol.com", "icloud.com", "me.com", "mac.com", "msn.com", "live.com",
    "proton.me", "protonmail.com", "ymail.com", "comcast.net", "sbcglobal.net",
}


def _domain(email_norm: str | None) -> str | None:
    if not email_norm or "@" not in email_norm:
        return None
    return email_norm.rsplit("@", 1)[1] or None


def _person(channel: str, display: str | None, email: str | None,
            phone: str | None = None, company: str | None = None,
            title: str | None = None, observed_at: str | None = None) -> CanonicalRecord | None:
    """Build one normalized person record from a (name, email, …) tuple."""
    em = N.normalize_email(email)
    first = last = None
    full = (display or "").strip() or None
    if full:
        first, last = N.parse_name(full)
    if not full and em:
        full = em.split("@", 1)[0].replace(".", " ").title()
        first, last = N.parse_name(full)
    nn = N.name_norm(first, last, full)
    if not nn and not em:
        return None  # nothing identifiable
    rec = CanonicalRecord(source=channel, source_pk=em or nn)
    rec.first_name, rec.last_name, rec.full_name = first, last, full
    rec.name_norm = nn
    rec.title = (title or "").strip() or None
    if company:
        rec.org_name = company.strip() or None
        rec.org_name_norm = N.org_name_norm(company) or None
    if em:
        rec.emails.append(Email(email=em, email_norm=em))
    ph = N.normalize_phone(phone) if phone else None
    if phone:
        rec.phones.append(Phone(phone_raw=str(phone), phone_e164=ph))
    rec.tags.append(Tag("source", channel))
    # Auto-group everyone sharing a company (non-freemail) email domain.
    dom = _domain(em)
    if dom and dom not in _FREEMAIL:
        rec.tags.append(Tag("domain", dom))
        if not rec.org_name:  # fall back to the domain as a weak org handle
            rec.contact_attrs["_email_domain"] = dom
    if observed_at:
        rec.contact_attrs["_observed_at"] = observed_at
    return rec


def _addrs(value) -> Iterable[tuple[str | None, str | None]]:
    """Yield (display_name, email) from a header string or list of strings."""
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else [value]
    return getaddresses([str(i) for i in items])


# --- extractors -------------------------------------------------------------

def extract_gmail(msg: dict) -> list[CanonicalRecord]:
    """From a normalized Gmail message:
        {"from": "Eric Vaden <eric@vaden.com>",
         "to": ["a@x.com", "B <b@y.com>"], "cc": [...],
         "date": "2026-01-02", "signature": {"name","phone","title","company"}}
    The sender is closest (signature if present, else From header); recipients
    are farther (gmail_to)."""
    out: list[CanonicalRecord] = []
    date = msg.get("date") or msg.get("internalDate")
    sig = msg.get("signature") or {}
    sender = list(_addrs(msg.get("from")))
    if sender:
        disp, em = sender[0]
        channel = "gmail_signature" if sig else "gmail_from"
        r = _person(channel, sig.get("name") or disp, em,
                    phone=sig.get("phone"), company=sig.get("company"),
                    title=sig.get("title"), observed_at=date)
        if r:
            out.append(r)
    for disp, em in list(_addrs(msg.get("to"))) + list(_addrs(msg.get("cc"))):
        r = _person("gmail_to", disp, em, observed_at=date)
        if r:
            out.append(r)
    return out


def extract_google_contact(person: dict) -> list[CanonicalRecord]:
    """From a People/Contacts resource (`names`, `emailAddresses`,
    `phoneNumbers`, `organizations`). A saved contact is high-trust/close."""
    return _from_people(person, "gcontacts")


def extract_people(person: dict) -> list[CanonicalRecord]:
    """From a People API search result (directory/other contacts)."""
    return _from_people(person, "people_api")


def _from_people(person: dict, channel: str) -> list[CanonicalRecord]:
    names = person.get("names") or []
    display = (names[0].get("displayName") if names else None)
    given = (names[0].get("givenName") if names else None)
    family = (names[0].get("familyName") if names else None)
    orgs = person.get("organizations") or []
    company = orgs[0].get("name") if orgs else None
    title = orgs[0].get("title") if orgs else None
    emails = [e.get("value") for e in (person.get("emailAddresses") or []) if e.get("value")]
    phones = [p.get("value") for p in (person.get("phoneNumbers") or []) if p.get("value")]
    primary_email = emails[0] if emails else None
    primary_phone = phones[0] if phones else None
    name = display or " ".join(x for x in (given, family) if x) or None
    r = _person(channel, name, primary_email, phone=primary_phone,
                company=company, title=title)
    if not r:
        return []
    # attach any additional emails/phones
    for e in emails[1:]:
        em = N.normalize_email(e)
        if em:
            r.emails.append(Email(email=em, email_norm=em))
    for p in phones[1:]:
        r.phones.append(Phone(phone_raw=str(p), phone_e164=N.normalize_phone(p)))
    return [r]


def extract_calendar_event(event: dict) -> list[CanonicalRecord]:
    """From a Calendar event: `organizer` (closer) and `attendees` (farther)."""
    out: list[CanonicalRecord] = []
    when = (event.get("start") or {}).get("dateTime") or (event.get("start") or {}).get("date") \
        or event.get("date")
    org = event.get("organizer") or {}
    if org.get("email"):
        r = _person("calendar_organizer", org.get("displayName"), org.get("email"),
                    observed_at=when)
        if r:
            out.append(r)
    for a in event.get("attendees") or []:
        if a.get("resource"):  # skip rooms/equipment
            continue
        r = _person("calendar_attendee", a.get("displayName"), a.get("email"),
                    observed_at=when)
        if r:
            out.append(r)
    return out


def extract_drive_doc(meta: dict) -> list[CanonicalRecord]:
    """From Drive file metadata: `owners` / `lastModifyingUser` (doc authors)."""
    out: list[CanonicalRecord] = []
    when = meta.get("modifiedTime") or meta.get("createdTime")
    people = list(meta.get("owners") or [])
    if meta.get("lastModifyingUser"):
        people.append(meta["lastModifyingUser"])
    seen = set()
    for u in people:
        em = u.get("emailAddress") or u.get("email")
        if em in seen:
            continue
        seen.add(em)
        r = _person("drive_author", u.get("displayName"), em, observed_at=when)
        if r:
            out.append(r)
    return out


# --- ingest -----------------------------------------------------------------

def sweep(conn, data: dict) -> dict:
    """Run one nightly sweep bundle through the extractors and ingest.

    `data` buckets raw Workspace objects by channel::

        {"gmail": [...], "gcontacts": [...], "calendar": [...],
         "drive": [...], "people": [...]}
    """
    recs: list[CanonicalRecord] = []
    for m in data.get("gmail", []):
        recs += extract_gmail(m)
    for c in data.get("gcontacts", data.get("contacts", [])):
        recs += extract_google_contact(c)
    for e in data.get("calendar", data.get("events", [])):
        recs += extract_calendar_event(e)
    for d in data.get("drive", data.get("files", [])):
        recs += extract_drive_doc(d)
    for p in data.get("people", []):
        recs += extract_people(p)
    return ingest(conn, recs)


def ingest(conn, records: list[CanonicalRecord], origin: str | None = None) -> dict:
    """Resolve collected records into the canonical store (idempotent, dedup),
    stamping each source_record with the data point's own date so the grader
    ages it correctly. Writes only to the local canonical DB; downstream
    fan-out to connectors happens via the change-log on the next sync push."""
    from ..db.repository import Repository
    from ..loaders.base import _attach_comms, _row_hash
    from ..resolve import Resolver

    repo = Repository(conn)
    repo.defer_fts = True
    resolver = Resolver(repo)
    counts = {"records": 0, "new": 0, "updated": 0, "skipped": 0, "by_channel": {}}
    for rec in records:
        if not (rec.has_contact or rec.has_org):
            continue
        counts["records"] += 1
        counts["by_channel"][rec.source] = counts["by_channel"].get(rec.source, 0) + 1
        rhash = _row_hash(rec)
        existing = repo.find_source_record(rec.source, rec.source_pk, rhash)
        if existing is not None:
            # Preserve the data point's own date; don't re-freshen to now.
            repo.touch_source_record(existing["source_record_id"],
                                     observed_at=rec.contact_attrs.get("_observed_at"))
            counts["skipped"] += 1
            continue
        prior = repo.find_source_by_pk(rec.source, rec.source_pk)
        org_id = resolver.resolve_org(rec, origin or f"sweep:{rec.source}")
        decision = resolver.resolve_contact(rec, org_id, origin or f"sweep:{rec.source}")
        _attach_comms(repo, rec, decision.contact_id, org_id)
        repo.record_source(rec.source, rec.source_pk, rhash, rec.raw,
                           decision.contact_id, org_id,
                           observed_at=rec.contact_attrs.get("_observed_at"))
        if prior is None and decision.is_new:
            counts["new"] += 1
        else:
            counts["updated"] += 1
    repo.rebuild_fts()
    conn.commit()
    return counts
