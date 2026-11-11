"""Flexible field mapping — the jevt concept: map any source column to a
canonical field, so a new source needs a mapping, not a bespoke loader.

A `SourceMapping` says which raw column feeds each canonical field. `auto_map`
guesses a mapping from column-name heuristics when none is supplied (jevt's
"automatic detection"). The DuckDB engine turns a mapping into one vectorized
normalization query.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SourceMapping:
    source: str
    # organization
    org_name: str | None = None
    website: str | None = None
    license_no: str | None = None
    # contact — either a single combined name column, or split first/last
    contact_full: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    # comms
    email: str | None = None
    email_invalid: str | None = None          # a column that flags invalid email
    phones: list[tuple[str, str]] = field(default_factory=list)   # (column, kind)
    # address
    line1: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    # classification
    region: str | None = None
    contact_type: str | None = None
    cert_columns: list[str] = field(default_factory=list)   # comma lists -> certification tags
    # provenance: columns (already-mapped canonical names) composing the stable source_pk
    source_pk_parts: list[str] = field(default_factory=lambda: ["org_name_norm", "name_norm"])
    owner: str = "contact"    # 'contact' or 'org' — who owns address/phones when no person

    def restrict(self, columns: list[str]) -> "SourceMapping":
        """Return a copy with any column not present in `columns` nulled out, so
        a mapping can be applied to a file that lacks some optional columns."""
        present = set(columns)
        import dataclasses
        named = ("org_name", "website", "license_no", "contact_full", "first_name",
                 "last_name", "title", "email", "email_invalid", "line1", "city",
                 "state", "zip", "region", "contact_type")
        changes = {f: (getattr(self, f) if getattr(self, f) in present else None) for f in named}
        changes["phones"] = [(c, k) for (c, k) in self.phones if c in present]
        changes["cert_columns"] = [c for c in self.cert_columns if c in present]
        return dataclasses.replace(self, **changes)


# Built-in mappings for the five known sources (mirror the hand-written loaders).
MAPPINGS: dict[str, SourceMapping] = {
    "tips": SourceMapping(
        "tips", org_name="Member", contact_full="Contact", title="Contact_Title",
        phones=[("Phone", "main"), ("Fax", "fax")],
        line1="Address1", city="City", state="State", zip="ZIP",
        region="Region", contact_type="Contact Type",
        source_pk_parts=["MemberID", "name_norm"], owner="org"),
    "buildingconnectd": SourceMapping(
        "buildingconnectd", org_name="Company", first_name="First Name", last_name="Last Name",
        email="Email", email_invalid="Invalid Email",
        phones=[("Phone", "main"), ("Office Phone", "office"), ("Cell", "cell")],
        line1="Street", city="City", state="State", zip="Zip",
        cert_columns=["Enterprise Type", "DBE Certificates"],
        source_pk_parts=["org_name_norm", "name_norm", "email_norm"]),
    "approved_subs": SourceMapping(
        "approved_subs", org_name="Name", website="Web_Page", license_no="License_No",
        contact_full="Contact_Name", email="E_Mail",
        phones=[("Telephone", "main"), ("Fax_Number", "fax"), ("Contact_No", "main")],
        line1="Address1", city="City", state="State", zip="ZIP",
        cert_columns=["CC_Description"],
        source_pk_parts=["Vendor"], owner="org"),
    "luncheon": SourceMapping(
        "luncheon", org_name="Organization", first_name="First name", last_name="Last name",
        title="Position", source_pk_parts=["org_name_norm", "name_norm"]),
}


def auto_map(source: str, columns: list[str]) -> SourceMapping:
    """Heuristic mapping from column names (jevt-style auto-detection)."""
    low = {c.lower().strip(): c for c in columns}

    def find(*needles):
        for n in needles:
            for lc, orig in low.items():
                if n in lc:
                    return orig
        return None

    m = SourceMapping(source)
    m.org_name = find("company", "organization", "member", "vendor name", "account", "name")
    m.contact_full = find("contact name", "full name", "contact")
    m.first_name = find("first name", "first")
    m.last_name = find("last name", "last")
    if m.contact_full and (m.first_name or m.last_name):
        m.contact_full = None  # prefer split
    m.title = find("title", "position")
    m.email = find("e_mail", "e-mail", "email")
    m.line1 = find("address1", "address", "street")
    m.city = find("city")
    m.state = find("state", "st")
    m.zip = find("zip", "postal")
    m.region = find("region")
    m.contact_type = find("contact type", "type")
    for col, kind in (("cell", "cell"), ("mobile", "cell"), ("office", "office"),
                      ("fax", "fax"), ("phone", "main"), ("telephone", "main")):
        hit = find(col)
        if hit and (hit, kind) not in m.phones and not any(hit == p[0] for p in m.phones):
            m.phones.append((hit, kind))
    return m


def get_mapping(source: str, columns: list[str] | None = None) -> SourceMapping:
    if source in MAPPINGS:
        return MAPPINGS[source]
    if columns is None:
        raise KeyError(f"no built-in mapping for '{source}'; pass columns for auto-mapping")
    return auto_map(source, columns)
