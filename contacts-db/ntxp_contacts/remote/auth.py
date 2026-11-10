"""OAuth-token gate for the cloud MCP — verification only (not a full AS).

The cloud MCP is stateless: each request carries a Bearer token. v1 verifies a
Google Workspace OAuth access token and requires the ntxpllc.com hosted domain,
so access ends up being "zero setup except OAuth". Modes (env ``NTXP_MCP_AUTH``):

* ``google`` (default) — validate the access token at Google's userinfo endpoint
  and require ``hd == NTXP_MCP_ALLOWED_DOMAIN``.
* ``static`` — accept a single shared token (``NTXP_MCP_TOKEN``); for a private
  deployment behind the agent proxy / an internal gateway.
* ``none``   — dev bypass (no auth). Never use in production.
"""
from __future__ import annotations

import json
import os
import urllib.request

ALLOWED_DOMAIN = os.environ.get("NTXP_MCP_ALLOWED_DOMAIN", "ntxpllc.com")
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def verify_token(token: str | None, allow_service: bool = False) -> dict | None:
    """Return {'email','domain'} for a valid token, else None.

    Peer service tokens (``svc.<peer>.<secret>``) are accepted only when the caller opts in
    (``allow_service=True``, used for /api/v1 alone): a peer key must never open /mcp,
    /carddav or the human /api surface."""
    if token and token.startswith("svc."):
        if not allow_service:
            return None
        from ..peers import load_peers, verify_service_token
        return verify_service_token(token, load_peers()[0])
    mode = os.environ.get("NTXP_MCP_AUTH", "google").lower()
    if mode == "none":
        return {"email": "anonymous@" + ALLOWED_DOMAIN, "domain": ALLOWED_DOMAIN}
    if not token:
        return None
    if mode == "static":
        want = os.environ.get("NTXP_MCP_TOKEN")
        if want and token == want:
            return {"email": "service@" + ALLOWED_DOMAIN, "domain": ALLOWED_DOMAIN}
        return None
    # mode == "google"
    try:
        req = urllib.request.Request(USERINFO_URL,
                                     headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            info = json.load(resp)
    except Exception:
        return None
    if info.get("hd") != ALLOWED_DOMAIN:
        return None
    return {"email": info.get("email"), "domain": info.get("hd")}
