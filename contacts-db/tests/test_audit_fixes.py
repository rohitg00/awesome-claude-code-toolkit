"""Regression tests for the audit round: each test fails on the pre-fix code."""
import asyncio
import io
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.qualify import Grader
from ntxp_contacts.remote import auth
from ntxp_contacts.remote.api import ApiError, _csv_cell, handle
from ntxp_contacts.sync.base import RemoteRecord
from ntxp_contacts.sync.reconcile import Reconciler


@pytest.fixture()
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    Reconciler(c, "jobtread").apply([RemoteRecord(external_id="JT1", payload={
        "firstName": "Eric", "lastName": "Vaden", "company": "Vaden Drywall",
        "email": "eric@vaden.com", "phone": "817-847-8822"})])
    return c


def _cid(conn):
    return conn.execute("SELECT contact_id FROM contacts WHERE is_deleted=0 LIMIT 1").fetchone()["contact_id"]


def _hold_back(conn, cid):
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()
    assert conn.execute("SELECT is_exposed FROM contact_grade WHERE contact_id=?", (cid,)).fetchone()[0] == 0


def call(conn, method, path, query=None, body=None):
    s, ctype, payload = handle(conn, "t@ntxpllc.com", method, path, query or {}, body)
    return s, (json.loads(payload) if ctype == "application/json" else payload.decode())


# ---- auth ------------------------------------------------------------------

class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture()
def google(monkeypatch):
    monkeypatch.setenv("NTXP_MCP_AUTH", "google")
    monkeypatch.delenv("NTXP_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("NTXP_GOOGLE_ALLOWED_CLIENT_IDS", raising=False)
    auth._CACHE.clear()
    calls = []
    state = {"userinfo": {"hd": "ntxpllc.com", "email": "a@ntxpllc.com", "email_verified": True},
             "tokeninfo": {"aud": "mine.apps.googleusercontent.com"}}

    def fake(req, timeout=0):
        url = req.full_url if hasattr(req, "full_url") else req
        calls.append(url)
        key = "tokeninfo" if "tokeninfo" in url else "userinfo"
        v = state[key]
        if isinstance(v, Exception):
            raise v
        return _Resp(json.dumps(v).encode())
    monkeypatch.setattr(auth.urllib.request, "urlopen", fake)
    return state, calls


def test_google_mode_domain_and_verified(google):
    state, _ = google
    assert auth.verify_token("t1")["email"] == "a@ntxpllc.com"
    state["userinfo"] = {"hd": "evil.com", "email": "a@evil.com", "email_verified": True}
    assert auth.verify_token("t2") is None
    state["userinfo"] = {"email": "a@gmail.com", "email_verified": True}          # no hd at all
    assert auth.verify_token("t3") is None
    state["userinfo"] = {"hd": "ntxpllc.com", "email": "a@ntxpllc.com", "email_verified": False}
    assert auth.verify_token("t4") is None
    state["userinfo"] = urllib.error.URLError("down")
    assert auth.verify_token("t5") is None


def test_token_audience_enforced_when_client_id_configured(google, monkeypatch):
    state, _ = google
    monkeypatch.setenv("NTXP_GOOGLE_CLIENT_ID", "mine.apps.googleusercontent.com")
    assert auth.verify_token("good") is not None
    state["tokeninfo"] = {"aud": "someone-elses-app", "azp": "someone-elses-app"}   # token minted for another app
    assert auth.verify_token("other-app") is None
    monkeypatch.setenv("NTXP_GOOGLE_ALLOWED_CLIENT_IDS", "someone-elses-app")       # explicitly allow-listed client
    auth._CACHE.clear()
    assert auth.verify_token("other-app") is not None


def test_token_checks_are_cached_including_bad_verdicts(google):
    state, calls = google
    for _ in range(5):
        auth.verify_token("same")
    assert len(calls) == 1
    state["userinfo"] = {"hd": "evil.com", "email": "a@evil.com", "email_verified": True}
    for _ in range(5):
        assert auth.verify_token("bogus") is None
    assert len(calls) == 2                       # one upstream call for the bogus token, not five


def test_transient_upstream_errors_are_not_cached(google):
    state, calls = google
    state["userinfo"] = urllib.error.URLError("timeout")
    assert auth.verify_token("blip") is None
    state["userinfo"] = {"hd": "ntxpllc.com", "email": "a@ntxpllc.com", "email_verified": True}
    assert auth.verify_token("blip") is not None          # recovered immediately: the outage was not remembered
    state["userinfo"] = urllib.error.HTTPError("u", 503, "x", {}, None)
    assert auth.verify_token("five-oh-three") is None
    state["userinfo"] = {"hd": "ntxpllc.com", "email": "a@ntxpllc.com", "email_verified": True}
    assert auth.verify_token("five-oh-three") is not None


def test_missing_email_verified_fails_closed(google):
    state, _ = google
    state["userinfo"] = {"hd": "ntxpllc.com", "email": "a@ntxpllc.com"}
    assert auth.verify_token("no-claim") is None


def test_azp_must_also_be_ours_and_cache_never_outlives_the_token(google, monkeypatch):
    state, calls = google
    monkeypatch.setenv("NTXP_GOOGLE_CLIENT_ID", "mine.apps.googleusercontent.com")
    state["tokeninfo"] = {"aud": "mine.apps.googleusercontent.com", "azp": "attacker-client"}
    assert auth.verify_token("mixed") is None
    state["tokeninfo"] = {"aud": "mine.apps.googleusercontent.com", "azp": "mine.apps.googleusercontent.com", "expires_in": "0"}
    assert auth.verify_token("expired-now") is None
    state["tokeninfo"] = {"aud": "mine.apps.googleusercontent.com", "azp": "mine.apps.googleusercontent.com", "expires_in": "2"}
    assert auth.verify_token("short-lived") is not None
    key = auth.hashlib.sha256(b"short-lived").hexdigest()
    assert auth._CACHE[key][0] - time.monotonic() <= 2.5


def test_same_token_concurrently_costs_one_upstream_call(google, monkeypatch):
    state, calls = google
    orig = auth.urllib.request.urlopen

    def slow(req, timeout=0):
        time.sleep(0.2)
        return orig(req, timeout)
    monkeypatch.setattr(auth.urllib.request, "urlopen", slow)
    ts = [threading.Thread(target=auth.verify_token, args=("burst",)) for _ in range(12)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(calls) == 1


def test_slow_token_check_does_not_stall_the_event_loop(google, monkeypatch):
    def slow(req, timeout=0):
        time.sleep(0.6)
        return _Resp(json.dumps({"hd": "ntxpllc.com", "email": "a@ntxpllc.com", "email_verified": True}).encode())
    monkeypatch.setattr(auth.urllib.request, "urlopen", slow)

    async def main():
        ticks = []

        async def ticker():
            for _ in range(5):
                ticks.append(time.monotonic())
                await asyncio.sleep(0.05)
        t = asyncio.create_task(ticker())
        r = await auth.verify_token_async("slow-token")
        await t
        return r, ticks
    r, ticks = asyncio.run(main())
    assert r is not None
    assert max(b - a for a, b in zip(ticks, ticks[1:])) < 0.3     # loop kept running while Google was "slow"


def test_static_token_constant_time_and_non_ascii(monkeypatch):
    monkeypatch.setenv("NTXP_MCP_AUTH", "static")
    monkeypatch.setenv("NTXP_MCP_TOKEN", "s3cret")
    assert auth.verify_token("s3cret") and auth.verify_token("s3cré") is None


# ---- signing: non-ASCII header values must be a clean "no", not a 500 ------

def test_signature_and_service_token_with_non_ascii_are_rejected_not_crashing():
    from ntxp_contacts.peers import signing
    now = int(time.time())
    assert signing.verify("secret", b"{}", f"t={now},v1=é", now=now) is False
    class P:  # noqa: E301
        secret = "abc"
    assert signing.verify_service_token("svc.schedules.é", {"schedules": P()}) is None


# ---- API -------------------------------------------------------------------

def test_csv_cells_neutralise_spreadsheet_formulas():
    for evil in ('=HYPERLINK("http://x","y")', "+1+1", "-2", "@SUM(A1)", "\tcmd", "\rcmd", " =1+1", "\n=1+1", "  \t@x"):
        assert _csv_cell(evil).startswith("'")
    assert _csv_cell("Eric") == "Eric" and _csv_cell(5) == 5


def test_csv_export_escapes_formula_names(conn):
    cid = _cid(conn)
    assert call(conn, "PATCH", f"/api/contacts/{cid}", body={"first_name": "=1+1"})[0] == 200
    s, body = call(conn, "GET", "/api/export.csv")
    assert s == 200 and "'=1+1" in body and ",=1+1," not in body


def test_negative_or_zero_limit_cannot_remove_the_page_cap(conn):
    for lim in ("-1", "0"):
        s, d = call(conn, "GET", "/api/contacts", {"limit": lim})
        assert s == 200 and d["limit"] == 1 and len(d["rows"]) == 1


def test_held_back_contacts_cannot_be_edited_or_relabelled(conn):
    cid = _cid(conn)
    _hold_back(conn, cid)
    assert call(conn, "PATCH", f"/api/contacts/{cid}", body={"city": "Waco"})[0] == 404
    assert call(conn, "POST", f"/api/contacts/{cid}/labels", body={"add": ["x"]})[0] == 404


@pytest.mark.parametrize("bad", [[1], "x", 5, None])
def test_non_object_bodies_are_400_not_500(conn, bad):
    cid = _cid(conn)
    for path, m in ((f"/api/contacts/{cid}", "PATCH"), (f"/api/contacts/{cid}/labels", "POST")):
        s, _ = call(conn, m, path, body=bad)
        assert s in (200, 400)            # None/{} are "no-op" bodies; lists/strings/ints must not crash
        if bad not in (None,):
            assert s == 400


def test_label_pipe_is_not_stored_and_add_list_is_capped(conn):
    cid = _cid(conn)
    call(conn, "POST", f"/api/contacts/{cid}/labels", body={"add": ["a|b"] + [f"l{i}" for i in range(200)]})
    vals = [r["value"] for r in conn.execute("SELECT value FROM tags WHERE kind='label'")]
    assert "a|b" not in vals and "a b" in vals and len(vals) <= 50


# ---- MCP exposure gate -----------------------------------------------------

def test_mcp_tools_respect_the_exposure_gate(tmp_path):
    pytest.importorskip("mcp")
    from ntxp_contacts.mcp_server import build_server
    db = tmp_path / "m.db"
    c = connect(db)
    migrate(c)
    Reconciler(c, "jobtread").apply([RemoteRecord(external_id="JT1", payload={
        "firstName": "Eric", "lastName": "Vaden", "company": "Vaden Drywall", "email": "eric@vaden.com"})])
    cid = _cid(c)
    srv = build_server(str(db))

    def tool(name, args):
        res = asyncio.run(srv.call_tool(name, args))
        content = res[0] if isinstance(res, tuple) else res
        return json.loads(content[0].text)
    assert tool("get_contact", {"contact_id": cid})["contact_id"] == cid
    assert any(r.get("contact_id") == cid for r in tool("search_contacts", {"query": "Vaden"}))
    _hold_back(c, cid)
    assert tool("get_contact", {"contact_id": cid}) is None
    assert not any(r.get("contact_id") == cid for r in tool("search_contacts", {"query": "Vaden"}))
    assert tool("export_contacts", {"limit": 10}) == []


# ---- CardDAV ---------------------------------------------------------------

def _asgi(app, method, path, headers, body=b""):
    out = []

    async def recv():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(m):
        out.append(m)
    asyncio.run(app({"type": "http", "method": method, "path": path, "headers": headers}, recv, send))
    return out[0]["status"]


def test_carddav_rejects_oversized_bodies_and_closes_connections(tmp_path, monkeypatch):
    from ntxp_contacts.remote.carddav import CardDAVApp
    monkeypatch.setenv("NTXP_MCP_AUTH", "none")
    app = CardDAVApp(str(tmp_path / "c.db"))
    assert _asgi(app, "OPTIONS", "/carddav/", []) == 200
    assert _asgi(app, "PROPFIND", "/carddav/", [], b"x" * 2_000_000) == 413


# ---- peers never follow redirects -----------------------------------------

def test_peer_http_refuses_redirects():
    from ntxp_contacts.peers import contracts as pc, events as pe

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/steal")
            self.end_headers()
        do_POST = do_GET
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        class Peer:
            url = base
            secret = "s"
        with pytest.raises(urllib.error.HTTPError) as e:
            pc._get(Peer, "/api/changes")
        assert e.value.code == 302
        code, msg = pe._post(base + "/hook", b"{}", {})
        assert code == 302
    finally:
        srv.shutdown()


# ---- performance / robustness ---------------------------------------------

def test_address_join_is_indexed(conn):
    names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")]
    assert "ix_addr_contact" in names
    plan = " ".join(str(tuple(r)) for r in conn.execute(
        "EXPLAIN QUERY PLAN SELECT 1 FROM addresses a WHERE a.contact_id=1"))
    assert "ix_addr_contact" in plan or "USING INDEX" in plan.upper()


def test_sqlite_waits_for_writers(conn):
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] >= 30000


def test_grading_that_flips_exposure_is_announced(conn):
    cid = _cid(conn)
    Grader(conn).run()                                              # fresh data: exposed
    before = conn.execute("SELECT COUNT(*) FROM change_log WHERE field='exposure'").fetchone()[0]
    _hold_back(conn, cid)                                           # re-grade after the data ages out
    after = conn.execute("SELECT COUNT(*) FROM change_log WHERE field='exposure' AND entity_id=?", (cid,)).fetchone()[0]
    assert before == 0 and after == 1


def test_contracts_pull_survives_bad_peer_answers(conn):
    from ntxp_contacts.peers import contracts as pc

    class Peer:
        name, url, secret = "contracts", "https://c.ntxpllc.cloud", "s"
    good = {"contracts": [{"contract_id": 1, "contract_no": "JOC-1", "contract_title": "J", "owner_entity": "Vaden Drywall"}]}
    seq = {"latest_seq": 5, "changed": True}

    def getter(body):
        return lambda peer, path, timeout=0: seq if "changes" in path else body
    assert pc.pull(conn, Peer, force=True, get=getter(good))["contracts"] == 1
    n = conn.execute("SELECT COUNT(*) FROM peer_context WHERE kind='contract'").fetchone()[0]
    assert n == 1
    for bad in ({"error": "x"}, "<html>502</html>", {"contracts": None}):
        assert "skipped" in pc.pull(conn, Peer, get=getter(bad))
        assert conn.execute("SELECT COUNT(*) FROM peer_context WHERE kind='contract'").fetchone()[0] == n
    # an empty list is believed only when confirmed on two consecutive polls
    assert "skipped" in pc.pull(conn, Peer, get=getter({"contracts": []}))
    assert conn.execute("SELECT COUNT(*) FROM peer_context WHERE kind='contract'").fetchone()[0] == n
    out = pc.pull(conn, Peer, get=getter({"contracts": []}))
    assert out.get("removed") == 1 and conn.execute("SELECT COUNT(*) FROM peer_context WHERE kind='contract'").fetchone()[0] == 0
