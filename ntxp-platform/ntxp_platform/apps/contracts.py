"""Contracts view: contract log in, reference lookups/profiles/expiry out."""
from __future__ import annotations

import dataclasses

from ..registry import AppSpec, FieldSpec, FuncSpec, dataclass_fields

_JOINS = {"owner_entity": "org_name", "contract_no": "contract_no", "location": "address"}


def _fields():
    try:
        from ntxp_contracts.model import Contract, Job, OwnerEntity
    except ImportError:   # app not installed: keep the profile honest but minimal
        return []
    owner_joins = {"name": "org_name", "website": "website", "email": "email",
                   "main_phone": "phone", "address": "address"}
    return (dataclass_fields(Contract, "contract", _JOINS)
            + dataclass_fields(OwnerEntity, "owner", owner_joins)
            + dataclass_fields(Job, "job"))


def _repo():
    from ntxp_contracts.db import connect, migrate
    from ntxp_contracts.db.repository import Repository
    c = connect(None)
    migrate(c)
    return Repository(c)


def search_contracts(query: str = "", limit: int = 50):
    return _repo().search(query, limit=int(limit))


def get_contract(contract_no: str = "", contract_id: int = 0):
    r = _repo()
    if not contract_id:
        c = r.get_contract_by_no(contract_no)
        if not c:
            return {"error": "not found"}
        contract_id = c["contract_id"]
    return r.get_profile(int(contract_id))


def list_expiring(within_days: int = 90):
    import datetime as dt
    cutoff = (dt.date.today() + dt.timedelta(days=int(within_days))).isoformat()
    return [c for c in _repo().list_contracts()
            if c.get("expiration_date") and c["expiration_date"] <= cutoff]


def stats():
    return _repo().stats()


SPEC = AppSpec(
    "contracts", "NTXP Master Contracts", "contracts.ntxpllc.cloud", "ntxp_contracts",
    "In: contract log import, inline edits, job sync. Out: reference lookups (coefficient, fee, "
    "expiry), per-contract profile, vCard/ICS, change feed.", _fields(),
    [FuncSpec("search_contracts", "Search contract log", {"query": "str?", "limit": "int?"}, handler=search_contracts),
     FuncSpec("get_contract", "Contract profile (terms, owner, jobs, totals)", {"contract_no": "str?", "contract_id": "int?"}, handler=get_contract),
     FuncSpec("list_expiring", "Contracts expiring within N days", {"within_days": "int?"}, handler=list_expiring),
     FuncSpec("stats", "Contract log totals", {}, handler=stats)])
