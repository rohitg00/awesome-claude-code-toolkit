"""Capability registry: every app's data fields and callable functions in one profile.

Apps are *views* of one codebase. Each app module (``apps/*.py``) contributes an
``AppSpec``; nothing here imports an app until its functions are called, so the
registry (and the combined profile) works even when only some apps are installed.
"""
from __future__ import annotations

import dataclasses
import importlib
from dataclasses import dataclass, field
from typing import Any, Callable

# Field names that must never leave their home app (secrets / credentials).
SECRET_FIELDS = {"api_key", "key_number", "login_user", "login_secret"}


@dataclass
class FieldSpec:
    name: str
    type: str = "text"
    entity: str = ""
    secret: bool = False
    joins: str = ""          # shared concept this field links on, e.g. "org_name"
    note: str = ""

    def qualified(self, app: str) -> str:
        return f"{app}.{self.entity}.{self.name}" if self.entity else f"{app}.{self.name}"


@dataclass
class FuncSpec:
    name: str
    summary: str
    params: dict[str, str] = field(default_factory=dict)   # name -> type (suffix ? = optional)
    read_only: bool = True
    sensitive: bool = False     # reveals secrets: never callable cross-app / via the hub
    handler: Callable[..., Any] | None = None
    app: str = ""

    @property
    def qualified(self) -> str:
        return f"{self.app}.{self.name}"


@dataclass
class AppSpec:
    name: str
    title: str
    host: str                              # default subdomain
    package: str                           # import name of the app's code base
    role: str                              # what this view is for (inputs/outputs)
    fields: list[FieldSpec] = field(default_factory=list)
    functions: list[FuncSpec] = field(default_factory=list)

    def installed(self) -> bool:
        try:
            return importlib.util.find_spec(self.package) is not None
        except (ImportError, ValueError):
            return False


def norm(s: str) -> str:
    """Shared join key for organization names (lowercase, alnum + single spaces)."""
    return " ".join("".join(ch if ch.isalnum() else " " for ch in (s or "").lower()).split())


def dataclass_fields(cls: type, entity: str, joins: dict[str, str] | None = None) -> list[FieldSpec]:
    """Derive FieldSpecs from an app's own dataclass so the profile cannot drift."""
    joins = joins or {}
    out = []
    for f in dataclasses.fields(cls):
        t = str(f.type).replace("typing.", "")
        out.append(FieldSpec(f.name, t, entity, secret=f.name in SECRET_FIELDS, joins=joins.get(f.name, "")))
    return out


class Registry:
    def __init__(self, apps: list[AppSpec]):
        self.apps = {a.name: a for a in apps}
        for a in apps:
            for fn in a.functions:
                fn.app = a.name

    def function(self, qualified: str) -> FuncSpec:
        app, _, name = qualified.partition(".")
        for fn in self.apps[app].functions:
            if fn.name == name:
                return fn
        raise KeyError(qualified)

    def profile(self, public: bool = True) -> dict:
        """The combined profile. ``public`` omits secret field *names' values* (names stay,
        flagged) and sensitive functions' handlers — the profile never carries data."""
        join_index: dict[str, list[str]] = {}
        apps = {}
        for a in self.apps.values():
            for f in a.fields:
                if f.joins:
                    join_index.setdefault(f.joins, []).append(f.qualified(a.name))
            apps[a.name] = {
                "title": a.title, "host": a.host, "role": a.role, "installed": a.installed(),
                "fields": [{"name": f.qualified(a.name), "type": f.type, "secret": f.secret,
                            "joins": f.joins} for f in a.fields],
                "functions": [{"name": fn.qualified, "summary": fn.summary, "params": fn.params,
                               "read_only": fn.read_only, "sensitive": fn.sensitive}
                              for fn in a.functions],
            }
        return {"apps": apps, "joins": join_index,
                "counts": {"fields": sum(len(a.fields) for a in self.apps.values()),
                           "functions": sum(len(a.functions) for a in self.apps.values())}}


def load_registry() -> Registry:
    from .apps import apilog, contacts, contracts, links
    return Registry([contacts.SPEC, contracts.SPEC, apilog.SPEC, links.SPEC])
