"""Generate downloadable contact / calendar files for the profile screen.

- ``vcard`` — a vCard 3.0 (.vcf) for the owner entity so a tap saves the
  customer-service / accounting / main lines straight into a phone's contacts.
- ``ics_expiration`` — an iCalendar (.ics) all-day event on the contract's
  expiration date so renewal lands on a calendar with a reminder.

Both are tiny, dependency-free string builders; the web layer serves them with
the right Content-Type and a download filename.
"""
from __future__ import annotations


import re
from datetime import datetime, timezone

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _esc_vcard(v) -> str:
    """Text value: CR/LF become a literal \\n (never a new content line), other control chars are dropped."""
    v = _CTRL.sub("", str(v)).replace("\r\n", "\n").replace("\r", "\n")
    return v.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def _line(v) -> str:
    """Unstructured value (phone, email, URL): a single physical line only."""
    return _CTRL.sub("", re.sub(r"[\r\n]+", " ", str(v))).strip()


def vcard(owner: dict) -> str:
    name = owner.get("name") or "Owner Entity"
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{_esc_vcard(name)}",
             f"ORG:{_esc_vcard(name)}"]
    if owner.get("main_phone"):
        lines.append(f"TEL;TYPE=WORK,VOICE:{_line(owner['main_phone'])}")
    if owner.get("customer_service_phone"):
        lines.append(f"TEL;TYPE=WORK,VOICE;X-LABEL=Customer Service:"
                     f"{_line(owner['customer_service_phone'])}")
    if owner.get("accounting_phone"):
        lines.append(f"TEL;TYPE=WORK,VOICE;X-LABEL=Accounting:"
                     f"{_line(owner['accounting_phone'])}")
    if owner.get("email"):
        lines.append(f"EMAIL;TYPE=WORK:{_line(owner['email'])}")
    if owner.get("website"):
        lines.append(f"URL:{_line(owner['website'])}")
    if owner.get("address"):
        lines.append(f"ADR;TYPE=WORK:;;{_esc_vcard(owner['address'])};;;;")
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def ics_expiration(contract: dict) -> str | None:
    exp = contract.get("expiration_date")
    if not exp:
        return None
    dt = re.sub(r"[^0-9]", "", str(exp))[:8]
    title = _esc_vcard(contract.get("contract_title") or "Contract")
    no = _esc_vcard(contract.get("contract_no") or "")
    uid = f"ntxp-contract-{contract.get('contract_id','x')}@ntxp"
    summary = f"Contract expires: {title}" + (f" ({no})" if no else "")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//NTXP//Contracts//EN",
        "CALSCALE:GREGORIAN", "BEGIN:VEVENT", f"UID:{uid}",
        "DTSTAMP:" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        f"DTSTART;VALUE=DATE:{dt}", f"SUMMARY:{summary}",
        "BEGIN:VALARM", "TRIGGER:-P30D", "ACTION:DISPLAY",
        "DESCRIPTION:Contract expires in 30 days", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"
