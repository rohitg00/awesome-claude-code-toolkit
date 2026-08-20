"""BuildingConnected bid-invitation export. One contact per row, rich comms."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .. import normalize as N
from ..model import Address, CanonicalRecord, Email, Phone, Tag
from ._excel import read_xlsx
from .base import register


class BuildingConnectedLoader:
    source = "buildingconnectd"

    def rows(self, path: str | Path) -> Iterator[dict]:
        yield from read_xlsx(path)

    def to_canonical(self, row: dict) -> CanonicalRecord | None:
        company = str(row.get("Company") or "").strip()
        first = str(row.get("First Name") or "").strip()
        last = str(row.get("Last Name") or "").strip()
        email = N.normalize_email(row.get("Email"))
        if not company and not first and not last and not email:
            return None

        rec = CanonicalRecord(source=self.source, raw=dict(row))
        rec.source_pk = "|".join([N.org_name_norm(company), N.name_norm(first, last), email or ""])

        rec.org_name = company or None
        rec.org_name_norm = N.org_name_norm(company) or None
        if rec.org_name:
            rec.org_tags.append(Tag("source", "buildingconnected"))

        # Enterprise / DBE classification tags (split comma lists)
        for col in ("Enterprise Type", "DBE Certificates", "Tags"):
            val = str(row.get(col) or "").strip()
            for piece in _split(val):
                rec.org_tags.append(Tag("certification", piece))
        labor = str(row.get("Labor Type") or "").strip()
        if labor and labor.lower() != "none":
            rec.org_tags.append(Tag("labor_type", labor))

        if first or last:
            rec.first_name = first or None
            rec.last_name = last or None
            rec.full_name = " ".join(p for p in (first, last) if p) or None
            rec.name_norm = N.name_norm(first, last)
            if email:
                invalid = str(row.get("Invalid Email") or "").strip().lower() in ("yes", "true", "1")
                rec.emails.append(Email(email=email, email_norm=email, is_invalid=invalid, is_primary=True))
            for col, kind in (("Phone", "main"), ("Office Phone", "office"), ("Cell", "cell")):
                raw = str(row.get(col) or "").strip()
                if raw:
                    rec.phones.append(Phone(phone_raw=raw, phone_e164=N.normalize_phone(raw), kind=kind))
            addr = Address(
                line1=str(row.get("Street") or "").strip() or None,
                city=str(row.get("City") or "").strip() or None,
                state=N.normalize_state(row.get("State")),
                zip=N.normalize_zip(row.get("Zip")),
            )
            addr.addr_norm = N.addr_norm(addr.line1, addr.city, addr.state, addr.zip)
            if addr.addr_norm:
                rec.addresses.append(addr)
            rec.tags.append(Tag("source", "buildingconnected"))
        return rec


def _split(value: str) -> list[str]:
    if not value or value.lower() == "none":
        return []
    return [p.strip() for p in value.replace(";", ",").split(",") if p.strip()]


register(BuildingConnectedLoader())
