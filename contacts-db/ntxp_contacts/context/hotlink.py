"""Tool-agnostic context hooks.

Any NTXP tool can call this to (a) pull a compact **context card** for a person
or company, and (b) **annotate** free text — wrapping every contact/company it
recognizes (and any email/phone) in a blue hyperlink hotlink that opens the
contacts page filtered to that entity. This is how non-UI tools inject live
contact context as blue clickable links.

Matching is conservative to avoid false positives: emails and phone numbers are
matched precisely; names are matched only as multi-word full names, and
organizations only by their full name (length-gated). The UI does its own
field-level hotlinking client-side; this serves everything that isn't the page.
"""
from __future__ import annotations

import html
import re

from ..config import contacts_url

BLUE = "color:#2f6fd0;text-decoration:none;border-bottom:1px solid rgba(47,111,208,.35)"

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?!\w)")
_WORD_RE = re.compile(r"[A-Za-z0-9&.'\-]+")
_MAX_NGRAM = 4


def _digits(s: str) -> str:
    d = "".join(ch for ch in s if ch.isdigit())
    return d[1:] if len(d) == 11 and d.startswith("1") else d


class HotlinkIndex:
    """Precomputed lookup of the canonical store for fast annotation."""

    def __init__(self, conn):
        self.conn = conn
        self.base = contacts_url()
        self.emails: dict[str, int] = {}
        self.phones: dict[str, int] = {}
        self.names: dict[str, int] = {}
        self.orgs: dict[str, int] = {}
        self._build()

    def _build(self) -> None:
        for r in self.conn.execute(
                "SELECT email_norm, contact_id FROM emails WHERE contact_id IS NOT NULL"):
            if r["email_norm"]:
                self.emails.setdefault(r["email_norm"].lower(), r["contact_id"])
        for r in self.conn.execute(
                "SELECT phone_e164, contact_id FROM phones WHERE contact_id IS NOT NULL"):
            if r["phone_e164"]:
                self.phones.setdefault(_digits(r["phone_e164"]), r["contact_id"])
        for r in self.conn.execute(
                "SELECT contact_id, full_name FROM contacts WHERE is_deleted=0 AND full_name IS NOT NULL"):
            fn = r["full_name"].strip()
            if len(fn.split()) >= 2:                      # multi-word names only
                self.names.setdefault(fn.lower(), r["contact_id"])
        for r in self.conn.execute(
                "SELECT org_id, name FROM organizations WHERE is_deleted=0 AND name IS NOT NULL"):
            nm = r["name"].strip()
            if len(nm) >= 4:
                self.orgs.setdefault(nm.lower(), r["org_id"])

    # -- hrefs & cards ------------------------------------------------------
    def href(self, kind: str, entity_id: int) -> str:
        return f"{self.base}?focus={kind}:{entity_id}"

    def link(self, label: str, kind: str, entity_id: int) -> str:
        return (f'<a class="ntxp-contact" href="{self.href(kind, entity_id)}" '
                f'style="{BLUE}">{html.escape(label)}</a>')

    def card(self, contact_id: int) -> dict | None:
        from ..db.repository import Repository
        from ..remote.maps import maps_link
        c = Repository(self.conn).get_contact(contact_id)
        if not c:
            return None
        extra = self.conn.execute(
            "SELECT photo_url, linkedin_url FROM contacts WHERE contact_id=?",
            (contact_id,)).fetchone()
        grade = self.conn.execute(
            "SELECT grade, grade_band, is_exposed FROM contact_grade WHERE contact_id=?",
            (contact_id,)).fetchone()
        addr = (c.get("addresses") or [None])[0]
        # Live preview of potential alternate contact info (proposed, not applied).
        alternates = []
        try:
            for r in self.conn.execute(
                    "SELECT field, value, source, grade FROM enrichment_candidates "
                    "WHERE contact_id=? AND status='proposed' ORDER BY grade DESC LIMIT 3",
                    (contact_id,)):
                alternates.append({"field": r["field"], "value": r["value"],
                                   "source": r["source"], "grade": r["grade"]})
        except Exception:
            pass
        peer_facts = {"contracts": [], "assignments": []}
        try:     # peers' facts (Master Contracts / Schedules); absent on a DB without migration 0005
            from ..peers.context import for_contact
            peer_facts = for_contact(self.conn, contact_id, c.get("org_id"))
        except Exception:
            pass
        return {
            "contracts": peer_facts["contracts"], "assignments": peer_facts["assignments"],
            "contact_id": contact_id,
            "name": c.get("full_name"),
            "title": c.get("title"),
            "org": c.get("org_name"),
            "email": (c.get("emails") or [{}])[0].get("email"),
            "phone": (c.get("phones") or [{}])[0].get("phone_e164"),
            "address": _fmt_addr(addr),
            "maps": maps_link(addr) if addr else None,
            "labels": [t["value"] for t in (c.get("tags") or []) if t["kind"] in ("member", "region", "trade", "contact_type", "domain")],
            "photo_url": extra["photo_url"] if extra else None,
            "linkedin_url": extra["linkedin_url"] if extra else None,
            "grade": grade["grade"] if grade else None,
            "grade_band": grade["grade_band"] if grade else None,
            "alternates": alternates,
            "href": self.href("contact", contact_id),
        }

    def card_html(self, contact_id: int) -> str | None:
        d = self.card(contact_id)
        if not d:
            return None
        bits = [self.link(d["name"] or "contact", "contact", contact_id)]
        if d["title"] or d["org"]:
            bits.append(html.escape(" · ".join(x for x in (d["title"], d["org"]) if x)))
        if d["email"]:
            bits.append(f'<a href="mailto:{html.escape(d["email"])}" style="{BLUE}">{html.escape(d["email"])}</a>')
        if d["phone"]:
            bits.append(f'<a href="tel:{html.escape(d["phone"])}" style="{BLUE}">{html.escape(d["phone"])}</a>')
        if d.get("address") and d.get("maps"):
            bits.append(f'<a href="{html.escape(d["maps"])}" style="{BLUE}">📍 {html.escape(d["address"])}</a>')
        return '<span class="ntxp-card">' + " — ".join(bits) + "</span>"

    # -- annotation ---------------------------------------------------------
    def annotate(self, text: str) -> dict:
        """Return {'html': annotated, 'links': [...]}; wraps emails, phones, and
        known multi-word names / org names in blue contact hotlinks."""
        links: list[dict] = []
        spans: list[tuple[int, int, str]] = []  # (start, end, replacement_html)

        for m in _EMAIL_RE.finditer(text):
            cid = self.emails.get(m.group(0).lower())
            if cid:
                spans.append((m.start(), m.end(), self.link(m.group(0), "contact", cid)))
                links.append({"text": m.group(0), "kind": "contact", "id": cid, "via": "email"})
        for m in _PHONE_RE.finditer(text):
            cid = self.phones.get(_digits(m.group(0)))
            if cid:
                spans.append((m.start(), m.end(), self.link(m.group(0), "contact", cid)))
                links.append({"text": m.group(0), "kind": "contact", "id": cid, "via": "phone"})

        # n-gram scan for names/orgs over word tokens
        words = [(w.start(), w.end(), w.group(0)) for w in _WORD_RE.finditer(text)]
        covered = _coverage(spans)
        i = 0
        while i < len(words):
            matched = False
            for n in range(min(_MAX_NGRAM, len(words) - i), 0, -1):
                s = words[i][0]
                e = words[i + n - 1][1]
                if _overlaps(covered, s, e):
                    continue
                phrase = text[s:e].rstrip(".,;:'\"")   # drop trailing punctuation
                e = s + len(phrase)
                key = phrase.lower()
                if n >= 2 and key in self.names:
                    cid = self.names[key]
                    spans.append((s, e, self.link(phrase, "contact", cid)))
                    links.append({"text": phrase, "kind": "contact", "id": cid, "via": "name"})
                    covered.append((s, e))
                    i += n
                    matched = True
                    break
                if key in self.orgs and len(phrase) >= 4:
                    oid = self.orgs[key]
                    spans.append((s, e, self.link(phrase, "org", oid)))
                    links.append({"text": phrase, "kind": "org", "id": oid, "via": "name"})
                    covered.append((s, e))
                    i += n
                    matched = True
                    break
            if not matched:
                i += 1

        # splice replacements right-to-left so offsets stay valid
        out = text
        for s, e, rep in sorted(spans, key=lambda x: x[0], reverse=True):
            out = out[:s] + rep + out[e:]
        return {"html": out, "links": links}


def _fmt_addr(a) -> str | None:
    if not a:
        return None
    parts = [a.get(k) for k in ("line1", "city", "state", "zip") if a.get(k)]
    return ", ".join(str(p) for p in parts) or None


def _coverage(spans):
    return [(s, e) for s, e, _ in spans]


def _overlaps(covered, s, e) -> bool:
    return any(not (e <= cs or s >= ce) for cs, ce in covered)


# -- module-level convenience ------------------------------------------------

def annotate(conn, text: str) -> dict:
    return HotlinkIndex(conn).annotate(text)


def card(conn, contact_id: int) -> dict | None:
    return HotlinkIndex(conn).card(contact_id)
