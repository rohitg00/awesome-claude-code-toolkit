"""Built-in deterministic resolvers (offline, zero-cost, no API keys).

Each proposes candidate values for a contact dict (as returned by
Repository.get_contact, augmented with 'photo_url'/'linkedin_url'/'website').
"""
from __future__ import annotations

import hashlib

from .base import Candidate, register

_FREEMAIL = {
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "aol.com", "icloud.com", "me.com", "mac.com", "msn.com", "live.com",
    "proton.me", "protonmail.com", "ymail.com",
}
_PUBLIC_TLDS = (".gov", ".us", ".mil")
_PUBLIC_HINTS = (".k12.", "isd.", "cityof", "countyof", ".edu")


def _emails(contact: dict) -> list[str]:
    return [e.get("email_norm") or e.get("email") for e in (contact.get("emails") or [])
            if (e.get("email_norm") or e.get("email"))]


def _domain(email: str) -> str | None:
    return email.rsplit("@", 1)[1].lower() if email and "@" in email else None


def _is_public(domain: str) -> bool:
    d = (domain or "").lower()
    return d.endswith(_PUBLIC_TLDS) or any(h in d for h in _PUBLIC_HINTS)


@register
class GravatarPhoto:
    name = "gravatar"
    provides = ("photo",)

    def resolve(self, contact: dict) -> list[Candidate]:
        out = []
        for em in _emails(contact):
            h = hashlib.md5(em.strip().lower().encode()).hexdigest()
            out.append(Candidate("photo",
                                 f"https://www.gravatar.com/avatar/{h}?s=256&d=404",
                                 "gravatar", evidence={"email": em, "verify": "GET ?d=404 -> 200 means present"}))
        return out


@register
class LibravatarPhoto:
    name = "libravatar"
    provides = ("photo",)

    def resolve(self, contact: dict) -> list[Candidate]:
        out = []
        for em in _emails(contact):
            h = hashlib.md5(em.strip().lower().encode()).hexdigest()
            out.append(Candidate("photo",
                                 f"https://seccdn.libravatar.org/avatar/{h}?s=256&d=404",
                                 "libravatar", evidence={"email": em}))
        return out


@register
class CompanyWebsite:
    name = "company_website"
    provides = ("website",)

    def resolve(self, contact: dict) -> list[Candidate]:
        if contact.get("website"):
            return []
        for em in _emails(contact):
            dom = _domain(em)
            if dom and dom not in _FREEMAIL:
                return [Candidate("website", f"https://{dom}", "company_website",
                                  evidence={"from_email_domain": dom})]
        return []


@register
class PublicEntityDirectory:
    name = "public_directory"
    provides = ("photo", "phone", "address")

    def resolve(self, contact: dict) -> list[Candidate]:
        """Public entities publish employee directories (photo, title, email,
        phone) on their primary domain — a high-value fetch target. Propose the
        directory URL for the agent to fetch and parse."""
        for em in _emails(contact):
            dom = _domain(em)
            if dom and _is_public(dom) and dom not in _FREEMAIL:
                q = f"https://www.google.com/search?q=site:{dom}+staff+directory+%22{contact.get('full_name','')}%22"
                return [Candidate("website", f"https://{dom}", "public_directory",
                                  evidence={"public_entity": dom,
                                            "directory_search": q,
                                            "note": "fetch employee directory for photo/title/phone"})]
        return []


@register
class LinkedInCandidate:
    name = "linkedin_candidate"
    provides = ("linkedin",)

    def resolve(self, contact: dict) -> list[Candidate]:
        """Generate a LinkedIn search candidate for the agent to confirm via the
        LinkedIn MCP. Never a confirmed URL and never scraped here."""
        if contact.get("linkedin_url"):
            return []
        name = (contact.get("full_name") or "").strip()
        if not name:
            return []
        company = contact.get("org_name") or ""
        q = f'site:linkedin.com/in "{name}" {company}'.strip()
        url = "https://www.google.com/search?q=" + q.replace(" ", "+").replace('"', "%22")
        return [Candidate("linkedin", url, "linkedin_candidate",
                          evidence={"query": q, "name": name, "company": company,
                                    "action": "agent: confirm match via LinkedIn MCP, then confirm_linkedin()"})]
