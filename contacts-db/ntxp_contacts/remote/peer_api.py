"""/api/v1 — the surface other NTXP apps (Schedules, Master Contracts, Form Fill) call.

Auth: Bearer ``svc.<peer>.<secret>`` (service) or a Google Workspace token (human).
Everything is exposure-gated like the UI: held-back / deleted contacts are invisible.

  GET /api/v1/ping
  GET /api/v1/people/resolve?email=|phone=|q=&limit=     find who someone is
  GET /api/v1/people/<id>                                 the autofill bag (+ contracts, assignments)
  GET /api/v1/context?id=|q=                              the card text to inject into a UI/prompt
"""
from __future__ import annotations

import json

from .. import normalize as N
from ..context import HotlinkIndex
from ..peers.context import assignments_for_contact
from ..peers.events import contact_bag
from .api import ApiError, _json, _q1, _rows

CONTRACT = "ntxp-contacts-peer/1"


def _lite(r: dict) -> dict:
    return {k: r.get(k) for k in ("id", "full_name", "title", "company", "email", "phone",
                                  "city", "state", "role", "trade", "project", "labels")}


def handle_v1(conn, principal: dict, method: str, path: str, query: dict):
    """-> (status, content_type, bytes); errors come back as JSON, never as exceptions."""
    try:
        return _handle_v1(conn, principal, method, path, query)
    except ApiError as e:
        return _json(e.status, {"error": e.msg})
    except (ValueError, TypeError) as e:
        return _json(400, {"error": str(e)})


def _handle_v1(conn, principal: dict, method: str, path: str, query: dict):
    p = path.rstrip("/")
    if method != "GET":
        return _json(405, {"error": "read-only"})
    if p == "/api/v1/ping":
        return _json(200, {"ok": True, "contract": CONTRACT, "as": principal.get("service") or principal.get("email")})
    if p == "/api/v1/people/resolve":
        limit = min(int(_q1(query, "limit", "10") or 10), 25)
        email, phone, q = N.normalize_email(_q1(query, "email")), N.normalize_phone(_q1(query, "phone")), _q1(query, "q")
        if not (email or phone or q):
            raise ApiError(400, "give email, phone or q")
        if email:
            ids = [r["contact_id"] for r in conn.execute(
                "SELECT DISTINCT contact_id FROM emails WHERE email_norm=? AND contact_id IS NOT NULL", (email,)).fetchall()]
        elif phone:
            ids = [r["contact_id"] for r in conn.execute(
                "SELECT DISTINCT contact_id FROM phones WHERE phone_e164=? AND contact_id IS NOT NULL", (phone,)).fetchall()]
        else:
            ids = [r["id"] for r in _rows(conn, {"q": q}, limit)[1]]
        out = []
        for cid in ids[:limit]:
            bag = contact_bag(conn, cid)                 # None unless exposed
            if bag:
                out.append(_lite(bag) | {"id": cid})
        return _json(200, {"matches": out})
    if p.startswith("/api/v1/people/"):
        try:
            cid = int(p.rsplit("/", 1)[1])
        except ValueError:
            raise ApiError(404, "not found")
        bag = contact_bag(conn, cid)
        if bag is None:
            raise ApiError(404, "not found")
        bag["assignments"] = assignments_for_contact(conn, cid)
        return _json(200, bag)
    if p == "/api/v1/context":
        idx = HotlinkIndex(conn)
        cid = _q1(query, "id")
        if not cid:
            q = _q1(query, "q")
            if not q:
                raise ApiError(400, "give id or q")
            from ..db.repository import Repository
            hit = Repository(conn).search(q, 1)
            cid = (hit[0].get("contact_id") if hit else None)
        card = idx.card(int(cid)) if cid else None
        if not card or contact_bag(conn, int(cid)) is None:
            return _json(200, {"card": None})
        from ..hooks.contact_context import card_text
        return _json(200, {"card": card, "text": card_text(card)})
    raise ApiError(404, "not found")
