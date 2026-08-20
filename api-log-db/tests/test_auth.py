"""Tests for Google OAuth login: config/allowlist, sessions, and the HTTP gate.

The full Google round-trip isn't exercised (no live IdP); we test everything up
to and around the code exchange: allowlist logic, session lifecycle, the
authorize URL, and that the server actually blocks unauthenticated requests
when OAuth is enabled and stays open when it isn't.
"""
from __future__ import annotations

import http.client
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import pytest

from ntxp_apilog import auth as oauth


# --- config / allowlist ------------------------------------------------------
def test_disabled_without_client_creds(monkeypatch):
    for k in ("NTXP_APILOG_GOOGLE_CLIENT_ID", "NTXP_APILOG_GOOGLE_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    assert oauth.OAuthConfig.from_env("127.0.0.1", 8787).enabled is False


def test_default_redirect_uri(monkeypatch):
    monkeypatch.delenv("NTXP_APILOG_OAUTH_REDIRECT", raising=False)
    cfg = oauth.OAuthConfig.from_env("apilog.ntxp.com", 9000)
    assert cfg.redirect_uri == "http://apilog.ntxp.com:9000/auth/callback"


def test_allowlist_email_and_domain():
    cfg = oauth.OAuthConfig(client_id="x", client_secret="y",
                            allowed_emails={"alex@ntxp.com"}, allowed_domain="ntxp.com")
    assert cfg.is_allowed("alex@ntxp.com")
    assert cfg.is_allowed("BOB@NTXP.COM")        # case-insensitive + domain
    assert not cfg.is_allowed("mallory@evil.com")
    assert not cfg.is_allowed(None)


def test_open_when_no_allowlist():
    cfg = oauth.OAuthConfig(client_id="x", client_secret="y")
    assert cfg.is_allowed("anyone@anywhere.com") is True


# --- session store -----------------------------------------------------------
def test_session_lifecycle():
    store = oauth.SessionStore()
    sid = store.create("alex@ntxp.com", "Alex")
    assert store.get(sid)["email"] == "alex@ntxp.com"
    store.destroy(sid)
    assert store.get(sid) is None
    assert store.get(None) is None


def test_state_is_single_use():
    store = oauth.SessionStore()
    state = store.new_state()
    assert store.consume_state(state) is True
    assert store.consume_state(state) is False     # replay rejected
    assert store.consume_state("never-issued") is False


def test_authorize_url_has_params():
    cfg = oauth.OAuthConfig(client_id="cid", client_secret="sec",
                            redirect_uri="http://h/auth/callback")
    url = oauth.authorize_url(cfg, "st8")
    assert url.startswith(oauth.AUTHORIZE_URL)
    for token in ("client_id=cid", "state=st8", "auth%2Fcallback", "scope=openid"):
        assert token in url


# --- live HTTP gate ----------------------------------------------------------
@pytest.fixture()
def server(tmp_path, monkeypatch, request):
    """Start the dashboard server on an ephemeral port with the given env."""
    monkeypatch.setenv("NTXP_APILOG_DB_PATH", str(tmp_path / "apilog.db"))
    monkeypatch.setenv("NTXP_APILOG_KEY_PATH", str(tmp_path / "apilog.key"))
    for k, v in getattr(request, "param", {}).items():
        monkeypatch.setenv(k, v)

    from ntxp_apilog.server import _make_handler
    handler = _make_handler(str(tmp_path / "apilog.db"), "127.0.0.1", 0)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(url, **kw):
    req = urllib.request.Request(url, **kw)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def test_gate_open_when_oauth_disabled(server):
    status, body = _get(server + "/api/meta")
    assert status == 200 and "categories" in body


@pytest.mark.parametrize("server", [{
    "NTXP_APILOG_GOOGLE_CLIENT_ID": "cid", "NTXP_APILOG_GOOGLE_CLIENT_SECRET": "sec",
    "NTXP_APILOG_ALLOWED_DOMAIN": "ntxp.com",
}], indirect=True)
def test_gate_blocks_when_oauth_enabled(server):
    # API calls are rejected with 401 + a login pointer.
    status, body = _get(server + "/api/apis")
    assert status == 401 and "/auth/login" in body
    # The dashboard page becomes the branded sign-in interstitial.
    status, body = _get(server + "/")
    assert status == 200 and "Sign in with Google" in body
    # /auth/me reports enabled-but-anonymous so the SPA can react.
    status, body = _get(server + "/auth/me")
    assert status == 200 and '"enabled": true' in body and '"authenticated": false' in body
    # /auth/login issues a 302 to Google's authorize endpoint (don't follow it).
    u = urlparse(server)
    conn = http.client.HTTPConnection(u.hostname, u.port)
    conn.request("GET", "/auth/login")
    resp = conn.getresponse()
    assert resp.status == 302
    assert resp.getheader("Location", "").startswith(oauth.AUTHORIZE_URL)
    conn.close()
