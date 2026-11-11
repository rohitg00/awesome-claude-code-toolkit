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

import asyncio
import concurrent.futures
import hashlib
import hmac
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ALLOWED_DOMAIN = os.environ.get("NTXP_MCP_ALLOWED_DOMAIN", "ntxpllc.com")
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

# Google answers userinfo for ANY access token with an email scope, so without an audience check a
# token minted for a third-party app by an ntxpllc.com user would be accepted. When
# NTXP_GOOGLE_CLIENT_ID is set we also require the token's aud/azp to be that client (or one listed in
# NTXP_GOOGLE_ALLOWED_CLIENT_IDS, comma separated, for MCP clients that use their own OAuth client).
_CACHE: dict[str, tuple[float, dict | None]] = {}
_CACHE_LOCK = threading.Lock()
_OK_TTL, _BAD_TTL, _CACHE_MAX = 60.0, 15.0, 2048
_AUTH_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="ntxp-auth")
_KEY_LOCKS: dict[str, threading.Lock] = {}
_HTTP_TIMEOUT = 4


class _Transient(Exception):
    """Upstream (Google/network) trouble: say "try again", and never cache it as a verdict on the token."""


def _allowed_clients() -> set[str]:
    ids = {os.environ.get("NTXP_GOOGLE_CLIENT_ID", "").strip()}
    ids |= {x.strip() for x in os.environ.get("NTXP_GOOGLE_ALLOWED_CLIENT_IDS", "").split(",")}
    return {i for i in ids if i}


def _fetch(req) -> dict | None:
    """JSON body, None when Google says the token is bad (4xx), _Transient on 5xx/timeouts/DNS."""
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if 400 <= e.code < 500:
            return None
        raise _Transient() from e
    except Exception as e:
        raise _Transient() from e


def _google_check(token: str) -> tuple[dict | None, float]:
    """(principal or None, seconds the verdict may be cached)."""
    info = _fetch(urllib.request.Request(USERINFO_URL, headers={"Authorization": f"Bearer {token}"}))
    ttl = _OK_TTL
    if not isinstance(info, dict) or info.get("hd") != ALLOWED_DOMAIN or not info.get("email"):
        return None, _BAD_TTL
    if info.get("email_verified") not in (True, "true"):          # fail closed when the claim is missing
        return None, _BAD_TTL
    clients = _allowed_clients()
    if clients:
        ti = _fetch(urllib.request.Request(
            TOKENINFO_URL + "?" + urllib.parse.urlencode({"access_token": token})))
        if not isinstance(ti, dict):
            return None, _BAD_TTL
        aud, azp = ti.get("aud"), ti.get("azp")
        if aud not in clients or (azp and azp not in clients):     # issued to one of OUR clients only
            return None, _BAD_TTL
        try:
            ttl = min(ttl, float(ti.get("expires_in")))            # never outlive the token itself
        except (TypeError, ValueError):
            pass
        if ttl <= 0:
            return None, _BAD_TTL
    return {"email": info.get("email"), "domain": info.get("hd")}, ttl


def _cached_google(token: str) -> dict | None:
    key = hashlib.sha256(token.encode("utf-8", "replace")).hexdigest()
    now = time.monotonic()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and hit[0] > now:
            return hit[1]
    with _CACHE_LOCK:
        lock = _KEY_LOCKS.setdefault(key, threading.Lock())
    with lock:                                                     # single-flight: same token = one upstream call
        with _CACHE_LOCK:
            hit = _CACHE.get(key)
            if hit and hit[0] > time.monotonic():
                return hit[1]
        try:
            result, ttl = _google_check(token)
        except _Transient:
            return None                                            # fail closed, but do NOT cache an outage
        finally:
            with _CACHE_LOCK:
                _KEY_LOCKS.pop(key, None)
        with _CACHE_LOCK:
            if len(_CACHE) >= _CACHE_MAX:
                t = time.monotonic()
                dead = [k for k, v in _CACHE.items() if v[0] <= t]
                for k in dead or [k for k, v in _CACHE.items() if v[1] is None][: _CACHE_MAX // 2] or list(_CACHE)[: _CACHE_MAX // 2]:
                    _CACHE.pop(k, None)                            # evict expired, then failures, before good entries
            _CACHE[key] = (time.monotonic() + ttl, result)
        return result


async def verify_token_async(token: str | None, allow_service: bool = False) -> dict | None:
    """verify_token without blocking the event loop (the Google call can take seconds)."""
    return await asyncio.get_running_loop().run_in_executor(_AUTH_POOL, verify_token, token, allow_service)


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
        if want and hmac.compare_digest(token.encode("utf-8", "replace"), want.encode("utf-8", "replace")):
            return {"email": "service@" + ALLOWED_DOMAIN, "domain": ALLOWED_DOMAIN}
        return None
    # mode == "google"
    return _cached_google(token)
