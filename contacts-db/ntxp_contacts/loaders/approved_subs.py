"""Approved subcontractors (legacy .xls). Org-centric with one contact."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .. import normalize as N
from ..model import Address, CanonicalRecord, Email, Phone, Tag
from ._excel import read_xls
from .base import register


class ApprovedSubsLoader:
    source = "approved_subs"

    def rows(self, path: str | Path) -> Iterator[dict]:
        yield from read_xls(path)

    def to_canonical(self, row: dict) -> CanonicalRecord | None:
        vendor = N.strip_float_id(row.get("Vendor"))
        org_name = str(row.get("Name") or "").strip()
        if not org_name:
            return None

        rec = CanonicalRecord(source=self.source, raw=dict(row))
        rec.source_pk = vendor or N.org_name_norm(org_name)
        rec.org_name = org_name
        rec.org_name_norm = N.org_name_norm(org_name)
        rec.website = str(row.get("Web_Page") or "").strip() or None
        rec.license_no = str(row.get("License_No") or "").strip() or None
        if vendor:
            rec.org_attrs["vendor_no"] = vendor
        lic = str(row.get("License") or "").strip()
        if lic and set(lic) != {"-"}:
            rec.org_attrs["license"] = lic
        for col in ("EMR 2009", "EMR2010", "EMR2011"):
            val = str(row.get(col) or "").strip()
            if val:
                rec.org_attrs[col.replace(" ", "").lower()] = val

        trade = str(row.get("CC_Description") or "").strip()
        if trade and trade.lower() not in ("need cost code",):
            rec.org_tags.append(Tag("trade", trade))
        rec.org_tags.append(Tag("source", "approved_subs"))
        rec.org_tags.append(Tag("contact_type", "approved_subcontractor"))

        addr = Address(
            line1=str(row.get("Address1") or "").strip() or None,
            city=str(row.get("City") or "").strip() or None,
            state=N.normalize_state(row.get("State")),
            zip=N.normalize_zip(row.get("ZIP")),
        )
        addr.addr_norm = N.addr_norm(addr.line1, addr.city, addr.state, addr.zip)
        if addr.addr_norm:
            rec.org_addresses.append(addr)

        for col, kind in (("Telephone", "main"), ("Fax_Number", "fax")):
            raw = str(row.get(col) or "").strip()
            if raw:
                rec.org_phones.append(Phone(phone_raw=raw, phone_e164=N.normalize_phone(raw), kind=kind))
        org_email = N.normalize_email(row.get("E_Mail"))

        contact_name = str(row.get("Contact_Name") or "").strip()
        if contact_name:
            first, last = N.parse_name(contact_name)
            rec.first_name, rec.last_name = first, last
            rec.full_name = contact_name
            rec.name_norm = N.name_norm(first, last, contact_name)
            if org_email:
                rec.emails.append(Email(email=org_email, email_norm=org_email, is_primary=True))
            cno = str(row.get("Contact_No") or "").strip()
            if cno:
                rec.phones.append(Phone(phone_raw=cno, phone_e164=N.normalize_phone(cno), kind="main"))
            rec.tags.append(Tag("source", "approved_subs"))
        elif org_email:
            rec.org_emails.append(Email(email=org_email, email_norm=org_email))
        return rec


register(ApprovedSubsLoader())
