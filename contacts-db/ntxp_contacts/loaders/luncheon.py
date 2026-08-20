"""North Texas Luncheon event registrants (legacy .xls). Small, event-tagged."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .. import normalize as N
from ..model import CanonicalRecord, Tag
from ._excel import read_xls
from .base import register

EVENT = "north_texas_luncheon_2023"


class LuncheonLoader:
    source = "luncheon"

    def rows(self, path: str | Path) -> Iterator[dict]:
        yield from read_xls(path)

    def to_canonical(self, row: dict) -> CanonicalRecord | None:
        first = str(row.get("First name") or "").strip()
        last = str(row.get("Last name") or "").strip()
        org_name = str(row.get("Organization") or "").strip()
        if not first and not last and not org_name:
            return None

        rec = CanonicalRecord(source=self.source, raw=dict(row))
        rec.source_pk = "|".join([N.name_norm(first, last), N.org_name_norm(org_name)])

        if org_name:
            rec.org_name = org_name
            rec.org_name_norm = N.org_name_norm(org_name)
            rec.org_tags.append(Tag("source", "luncheon"))

        if first or last:
            rec.first_name = first or None
            rec.last_name = last or None
            rec.full_name = " ".join(p for p in (first, last) if p) or None
            rec.name_norm = N.name_norm(first, last)
            rec.title = str(row.get("Position") or "").strip() or None
            reg = N.normalize_date(row.get("Event registration date"))
            if reg:
                rec.contact_attrs["event_registration_date"] = reg
            rec.tags.append(Tag("event", EVENT))
            rec.tags.append(Tag("source", "luncheon"))
            if str(row.get("Member") or "").strip().lower() in ("yes", "true", "1"):
                rec.tags.append(Tag("member", "yes"))
        return rec


register(LuncheonLoader())
