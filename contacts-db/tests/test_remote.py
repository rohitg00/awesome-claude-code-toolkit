"""F1 — stateless cloud MCP: maps links, OAuth-token gate, ASGI auth, hook."""
import asyncio
import io
import json

import pytest

from ntxp_contacts.remote.auth import verify_token
from ntxp_contacts.remote.http_server import AuthMiddleware
from ntxp_contacts.remote.maps import apple_maps_link, maps_link


# -- maps --------------------------------------------------------------------

def test_maps_links():
    g = maps_link({"line1": "411 Elm St", "city": "Dallas", "state": "TX"})
    assert g.startswith("https://www.google.com/maps/search/?api=1&query=")
    assert "Dallas" in g
    assert apple_maps_link("411 Elm St, Dallas TX").startswith("https://maps.apple.com/?q=")
    assert maps_link("") is None


# -- token verification ------------------------------------------------------

def test_verify_token_static(monkeypatch):
    monkeypatch.setenv("NTXP_MCP_AUTH", "static")
    monkeypatch.setenv("NTXP_MCP_TOKEN", "s3cret")
    assert verify_token("s3cret")["domain"] == "ntxpllc.com"
    assert verify_token("nope") is None
    assert verify_token(None) is None


def test_verify_token_none_bypass(monkeypatch):
    monkeypatch.setenv("NTXP_MCP_AUTH", "none")
    assert verify_token(None) is not None  # dev bypass


# -- ASGI auth middleware ----------------------------------------------------

class _Inner:
    def __init__(self):
        self.called = False

    async def __call__(self, scope, receive, send):
        self.called = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def _drive(app, scope):
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(m):
        sent.append(m)

    asyncio.run(app(scope, receive, send))
    return sent


def _scope(path, headers=None):
    return {"type": "http", "path": path, "headers": headers or []}


def test_auth_blocks_without_token(monkeypatch):
    monkeypatch.setenv("NTXP_MCP_AUTH", "static")
    monkeypatch.setenv("NTXP_MCP_TOKEN", "s3cret")
    inner = _Inner()
    sent = _drive(AuthMiddleware(inner), _scope("/mcp"))
    assert sent[0]["status"] == 401 and not inner.called


def test_auth_allows_valid_token(monkeypatch):
    monkeypatch.setenv("NTXP_MCP_AUTH", "static")
    monkeypatch.setenv("NTXP_MCP_TOKEN", "s3cret")
    inner = _Inner()
    sent = _drive(AuthMiddleware(inner),
                  _scope("/mcp", [(b"authorization", b"Bearer s3cret")]))
    assert inner.called and sent[0]["status"] == 200


def test_health_is_open(monkeypatch):
    monkeypatch.setenv("NTXP_MCP_AUTH", "static")
    inner = _Inner()
    sent = _drive(AuthMiddleware(inner), _scope("/health"))
    assert sent[0]["status"] == 200 and not inner.called


# -- hook --------------------------------------------------------------------

def test_hook_injects_contact_context(tmp_path, monkeypatch, capsys):
    db = tmp_path / "h.db"
    monkeypatch.setenv("NTXP_DB_PATH", str(db))
    monkeypatch.delenv("NTXP_DB_URL", raising=False)
    from ntxp_contacts.db import connect, migrate
    from ntxp_contacts.sync.base import RemoteRecord
    from ntxp_contacts.sync.reconcile import Reconciler
    c = connect(None)
    migrate(c)
    Reconciler(c, "jobtread").apply([RemoteRecord(external_id="JT1", payload={
        "firstName": "Eric", "lastName": "Vaden", "company": "Vaden Drywall",
        "email": "eric@vaden.com", "phone": "817-847-8822"})])
    c.close()

    monkeypatch.setattr("sys.stdin",
                        io.StringIO(json.dumps({"prompt": "Email Eric Vaden about the bid"})))
    from ntxp_contacts.hooks.contact_context import main
    assert main() == 0
    out = capsys.readouterr().out
    assert "Eric Vaden" in out and "additionalContext" in out
