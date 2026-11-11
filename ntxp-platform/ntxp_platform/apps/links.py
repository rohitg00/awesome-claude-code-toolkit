"""Cross-app links: functions that join data across views via shared concepts."""
from __future__ import annotations

from ..registry import AppSpec, FuncSpec
from . import contacts, contracts


def contract_contacts(contract_no: str):
    """Contract → the owner entity's people in Contacts (join: owner_entity ≈ org name)."""
    prof = contracts.get_contract(contract_no=contract_no)
    if not prof or prof.get("error"):
        return {"error": "contract not found", "contract_no": contract_no}
    owner = (prof.get("contract") or {}).get("owner_entity") or (prof.get("owner") or {}).get("name")
    return {"contract_no": contract_no, "owner": owner,
            "people": contacts.org_people(owner) if owner else []}


def org_contracts(org_name: str):
    """Organization → contracts it owns (join: org name ≈ owner_entity)."""
    from ..registry import norm
    want = norm(org_name)
    hits = [c for c in contracts.search_contracts("", 500) if norm(c.get("owner_entity") or "") == want]
    return {"org": org_name, "contracts": hits}


def entity_dossier(name: str):
    """Everything NTXP knows about an organization across all views (never secrets)."""
    return {"name": name, "contracts": org_contracts(name)["contracts"],
            "people": contacts.org_people(name)}


SPEC = AppSpec(
    "links", "Cross-app links", "(all views)", "ntxp_platform",
    "Joins across views on shared concepts (org name, email, phone, contract no).", [],
    [FuncSpec("contract_contacts", "People at a contract's owner entity", {"contract_no": "str"}, handler=contract_contacts),
     FuncSpec("org_contracts", "Contracts owned by an organization", {"org_name": "str"}, handler=org_contracts),
     FuncSpec("entity_dossier", "Org-wide dossier: contracts + people", {"name": "str"}, handler=entity_dossier)])
