"""Webhook signing + service tokens. HMAC-SHA256 over "<unix-ts>.<raw body>", Stripe-style
header ``X-NTXP-Signature: t=<ts>,v1=<hex>``; 5-minute replay window."""
from __future__ import annotations

import hashlib
import hmac
import time

TOLERANCE_S = 300
SIG_HEADER = "X-NTXP-Signature"


def sign(secret: str, body: bytes, ts: int | None = None) -> tuple[int, str]:
    ts = int(time.time()) if ts is None else int(ts)
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return ts, f"t={ts},v1={mac}"


def verify(secret: str, body: bytes, header: str | None, now: float | None = None) -> bool:
    if not header:
        return False
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        ts = int(parts["t"])
        given = parts["v1"]
    except (ValueError, KeyError):
        return False
    if abs((time.time() if now is None else now) - ts) > TOLERANCE_S:
        return False
    want = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, given)


def verify_service_token(token: str | None, peers: dict) -> dict | None:
    """Token format ``svc.<peer>.<secret>`` -> service principal, else None.
    Service principals may only call /api/v1 (see ApiApp); they never reach /mcp or /carddav."""
    if not token or not token.startswith("svc."):
        return None
    try:
        _, name, secret = token.split(".", 2)
    except ValueError:
        return None
    peer = peers.get(name)
    if peer is None or not hmac.compare_digest(peer.secret, secret):
        return None
    return {"email": f"{name}@service.invalid", "domain": "service", "service": name}
