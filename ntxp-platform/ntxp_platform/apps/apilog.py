"""API Log view: credentials vault. Deliberately isolated — secrets never cross apps."""
from __future__ import annotations

from ..registry import AppSpec, FuncSpec, dataclass_fields


def _fields():
    try:
        from ntxp_apilog.model import ApiEntry, UsageEvent
    except ImportError:
        return []
    return dataclass_fields(ApiEntry, "api", {"provider": "org_name", "base_url": "website"}) \
        + dataclass_fields(UsageEvent, "usage")


def _repo():
    from ntxp_apilog.crypto import Cipher
    from ntxp_apilog.db import connect, migrate
    from ntxp_apilog.db.repository import Repository
    c = connect(None)
    migrate(c)
    return Repository(c, cipher=Cipher())


def find_api(query: str, limit: int = 10):
    """Non-secret metadata only (the repository masks keys unless reveal=True)."""
    return _repo().search(query, limit=int(limit))


def list_apis(status: str = "", category: str = ""):
    return _repo().list_apis(status=status or None, category=category or None)


def stats():
    return _repo().stats()


SPEC = AppSpec(
    "apilog", "NTXP API Log", "api.ntxpllc.cloud", "ntxp_apilog",
    "In: API registrations, usage/cost events. Out: encrypted credential reveals (audited), cost "
    "dashboard. Secrets stay in this view.", _fields(),
    [FuncSpec("find_api", "Find a registered API (masked)", {"query": "str", "limit": "int?"}, handler=find_api),
     FuncSpec("list_apis", "List registered APIs (masked)", {"status": "str?", "category": "str?"}, handler=list_apis),
     FuncSpec("stats", "Spend and registry totals", {}, handler=stats),
     FuncSpec("get_credentials", "Reveal secrets (audited) — apilog view only", {"name_or_id": "str"}, sensitive=True)])
