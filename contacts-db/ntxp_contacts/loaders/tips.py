"""TIPS purchasing-cooperative members. One org (MemberID) -> many contacts."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .. import normalize as N
from ..model import Address, CanonicalRecord, Email, Phone, Tag
from ._excel import read_xlsx
from .base import register


class TipsLoader:
    source = "tips"

    def rows(self, path: str | Path) -> Iterator[dict]:
        yield from read_xlsx(path)

    def to_canonical(self, row: dict) -> CanonicalRecord | None:
        member_id = N.strip_float_id(row.get("MemberID"))
        org_name = str(row.get("Member") or "").strip()
        contact_full = str(row.get("Contact") or "").strip()
        if not org_name and not contact_full:
            return None

        first, last = N.parse_name(contact_full)
        rec = CanonicalRecord(source=self.source, raw=dict(row))
        rec.source_pk = f"{member_id}|{N.name_norm(first, last, contact_full)}" if member_id \
            else N.name_norm(first, last, contact_full)

        # Org
        rec.org_name = org_name or None
        rec.org_name_norm = N.org_name_norm(org_name) or None
        if member_id:
            rec.org_attrs["tips_member_id"] = member_id
        md = N.normalize_date(row.get("Membership Date"))
        if md:
            rec.org_attrs["membership_date"] = md
        addr = Address(
            line1=str(row.get("Address1") or "").strip() or None,
            city=str(row.get("City") or "").strip() or None,
            state=N.normalize_state(row.get("State")),
            zip=N.normalize_zip(row.get("ZIP")),
        )
        addr.addr_norm = N.addr_norm(addr.line1, addr.city, addr.state, addr.zip)
        if addr.addr_norm:
            rec.org_addresses.append(addr)
        rec.org_tags.append(Tag("source", "tips"))

        # Contact
        if contact_full:
            rec.first_name, rec.last_name = first, last
            rec.full_name = contact_full
            rec.name_norm = N.name_norm(first, last, contact_full)
            rec.title = str(row.get("Contact_Title") or "").strip() or None
            for col, kind in (("Phone", "main"), ("Fax", "fax")):
                raw = str(row.get(col) or "").strip()
                if raw:
                    rec.phones.append(Phone(phone_raw=raw, phone_e164=N.normalize_phone(raw), kind=kind))
            region = str(row.get("Region") or "").strip()
            if region:
                rec.tags.append(Tag("region", region))
            ctype = str(row.get("Contact Type") or "").strip()
            if ctype:
                rec.tags.append(Tag("contact_type", ctype))
            rec.tags.append(Tag("source", "tips"))
        return rec


register(TipsLoader())
