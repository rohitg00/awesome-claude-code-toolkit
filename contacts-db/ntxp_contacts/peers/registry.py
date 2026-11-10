"""Peer registry: NTXP Schedules, NTXP Master Contracts, NTXP Form Fill.

Configured by NTXP_PEERS (JSON), e.g.::

  {"schedules": {"url": "https://schedules.ntxpllc.cloud", "secret": "<32+ chars>",
                 "hook_path": "/hooks/ntxp-contacts", "events": ["contact.*"]},
   "contracts": {"url": "https://contracts.ntxpllc.cloud", "secret": "<...>"},
   "formfill":  {"url": "https://formfill.ntxpllc.cloud",  "secret": "<...>",
                 "hook_path": "/hooks/ntxp-contacts"}}

The URLs are *your* hostnames; nothing is guessed. Safety rules enforced at load:
  * https only, host must end with NTXP_PEER_HOST_SUFFIX (default ".ntxpllc.cloud"),
    no credentials in the URL — outbound calls can only ever reach NTXP hosts;
  * the shared secret must be >= 24 chars (it signs our webhooks, verifies theirs,
    and authenticates their calls into /api/v1);
  * NTXP_PEER_ALLOW_LOCAL=1 additionally permits http://127.0.0.1 / localhost (tests, dev).
A misconfigured peer is reported by `ntxp peers status` and skipped — it never crashes the app.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

KNOWN = ("schedules", "contracts", "formfill")
_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,24}$")
MIN_SECRET = 24
DEFAULT_HOOK_PATH = "/hooks/ntxp-contacts"


@dataclass
class Peer:
    name: str
    url: str
    secret: str = field(repr=False)
    hook_path: str = DEFAULT_HOOK_PATH
    events: tuple[str, ...] = ("contact.*",)
    receives_events: bool = True      # contracts is pulled from, not pushed to, unless it opts in
    pulls: bool = False               # we poll this peer (Master Contracts)

    @property
    def hook_url(self) -> str:
        return self.url.rstrip("/") + self.hook_path


def _allowed_suffix() -> str:
    return os.environ.get("NTXP_PEER_HOST_SUFFIX", ".ntxpllc.cloud").lower()


def _allow_local() -> bool:
    return os.environ.get("NTXP_PEER_ALLOW_LOCAL", "").lower() in ("1", "true", "yes")


def validate_url(url: str) -> str:
    u = urlparse(url or "")
    host = (u.hostname or "").lower()
    if u.username or u.password:
        raise ValueError("peer url must not contain credentials")
    local = host in ("127.0.0.1", "localhost", "::1")
    if local:
        if not _allow_local():
            raise ValueError("local peer urls need NTXP_PEER_ALLOW_LOCAL=1")
        if u.scheme not in ("http", "https"):
            raise ValueError("peer url must be http(s)")
        return url.rstrip("/")
    if u.scheme != "https":
        raise ValueError("peer url must be https")
    if not host.endswith(_allowed_suffix()) or host == _allowed_suffix().lstrip("."):
        raise ValueError(f"peer host must end with {_allowed_suffix()}")
    return url.rstrip("/")


def load_peers(raw: str | None = None) -> tuple[dict[str, Peer], dict[str, str]]:
    """-> (valid peers, {name: error}). Never raises on bad config."""
    raw = raw if raw is not None else os.environ.get("NTXP_PEERS", "")
    peers: dict[str, Peer] = {}
    errors: dict[str, str] = {}
    if not raw.strip():
        return peers, errors
    try:
        cfg = json.loads(raw)
        if not isinstance(cfg, dict):
            raise ValueError("NTXP_PEERS must be a JSON object")
    except ValueError as exc:
        return peers, {"_config": f"NTXP_PEERS is not valid JSON: {exc}"}
    for name, c in cfg.items():
        try:
            if not _NAME_RE.match(name):
                raise ValueError("bad peer name")
            if not isinstance(c, dict):
                raise ValueError("peer config must be an object")
            secret = str(c.get("secret") or "")
            if len(secret) < MIN_SECRET:
                raise ValueError(f"secret must be at least {MIN_SECRET} characters")
            if "." in secret:
                raise ValueError("secret must not contain '.' (use `ntxp peers keygen`)")
            hook_path = str(c.get("hook_path") or DEFAULT_HOOK_PATH)
            if not hook_path.startswith("/"):
                raise ValueError("hook_path must start with /")
            events = tuple(str(e) for e in (c.get("events") or ["contact.*"]))
            peers[name] = Peer(
                name=name, url=validate_url(str(c.get("url") or "")), secret=secret,
                hook_path=hook_path, events=events,
                receives_events=bool(c.get("receive_events", name != "contracts")),
                pulls=bool(c.get("pull", name == "contracts")))
        except ValueError as exc:
            errors[name] = str(exc)
    return peers, errors
