"""Interlinking with NTXP Schedules / Master Contracts / Form Fill.

Uses real network peers: a local HTTP receiver that verifies our webhook signatures, and the
actual Master Contracts server from this repo (contracts-db) as the watched peer."""
import json
import os
import sys
import threading
import time
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.loaders.base import import_records
from ntxp_contacts.peers import load_peers, sign, verify, verify_service_token
from ntxp_contacts.peers import context as pctx
from ntxp_contacts.peers import contracts as pcontracts
from ntxp_contacts.peers import events, inbound
from ntxp_contacts.peers.runner import run_cycle
from ntxp_contacts.qualify import Grader
from ntxp_contacts.remote.auth import verify_token
from ntxp_contacts.remote.peer_api import handle_v1
from test_api import DATA, _Loader

PG_URL = os.environ.get("NTXP_TEST_PG_URL")
SECRET = "s" * 40


# ---------------------------------------------------------------- fixtures
class Receiver:
    """A peer's webhook endpoint: records every request; `status` is what it answers."""

    def __init__(self):
        self.got, self.status = [], 200
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                outer.got.append({"path": self.path, "body": body, "headers": {k.lower(): v for k, v in self.headers.items()}})
                self.send_response(outer.status)
                self.end_headers()

            def log_message(self, *a):
                pass
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()


@pytest.fixture(params=["sqlite"] + (["pg"] if PG_URL else []))
def conn(request, tmp_path):
    if request.param == "pg":
        c = connect(PG_URL)
        c.execute("DROP SCHEMA public CASCADE")
        c.execute("CREATE SCHEMA public")
        c.commit()
    else:
        c = connect(tmp_path / "t.db")
    migrate(c)
    import_records(c, _Loader(DATA), "x")
    yield c
    c.close()


@pytest.fixture
def recv():
    r = Receiver()
    yield r
    r.close()


@pytest.fixture
def peers_env(monkeypatch, recv):
    monkeypatch.setenv("NTXP_PEER_ALLOW_LOCAL", "1")
    cfg = {"schedules": {"url": recv.url, "secret": SECRET}, "formfill": {"url": recv.url, "secret": "f" * 40}}
    monkeypatch.setenv("NTXP_PEERS", json.dumps(cfg))
    return load_peers()[0]


def cid_of(conn, last):
    return conn.execute("SELECT contact_id FROM contacts WHERE last_name=?", (last,)).fetchone()["contact_id"]


def bump(conn, cid, origin="ui:someone"):
    from ntxp_contacts.db.repository import Repository
    Repository(conn).log_change("contact", cid, "update", origin, "title")
    conn.commit()


# ---------------------------------------------------------------- registry + signing
def test_registry_rejects_unsafe_peers(monkeypatch):
    monkeypatch.delenv("NTXP_PEER_ALLOW_LOCAL", raising=False)
    cfg = {"schedules": {"url": "https://schedules.ntxpllc.cloud", "secret": SECRET},
           "evil": {"url": "https://evil.example.com", "secret": SECRET},
           "plain": {"url": "http://schedules.ntxpllc.cloud", "secret": SECRET},
           "creds": {"url": "https://u:p@a.ntxpllc.cloud", "secret": SECRET},
           "short": {"url": "https://a.ntxpllc.cloud", "secret": "tiny"},
           "dot": {"url": "https://a.ntxpllc.cloud", "secret": "a." + "x" * 30},
           "local": {"url": "http://127.0.0.1:9", "secret": SECRET},
           "Bad Name": {"url": "https://a.ntxpllc.cloud", "secret": SECRET}}
    ok, err = load_peers(json.dumps(cfg))
    assert set(ok) == {"schedules"}
    assert set(err) == {"evil", "plain", "creds", "short", "dot", "local", "Bad Name"}
    assert load_peers("not json")[1]["_config"]
    assert load_peers("")[0] == {}


def test_signature_roundtrip_and_tamper():
    body = b'{"a":1}'
    ts, header = sign(SECRET, body)
    assert verify(SECRET, body, header)
    assert not verify(SECRET, b'{"a":2}', header)                 # tampered body
    assert not verify("o" * 40, body, header)                      # wrong secret
    assert not verify(SECRET, body, None) and not verify(SECRET, body, "garbage")
    _, old = sign(SECRET, body, ts=int(time.time()) - 1000)
    assert not verify(SECRET, body, old)                           # outside the replay window


def test_service_tokens_are_scoped(monkeypatch, peers_env):
    tok = f"svc.schedules.{SECRET}"
    assert verify_token(tok) is None                               # never on the human surface (/mcp, /carddav, /api)
    p = verify_token(tok, allow_service=True)
    assert p and p["service"] == "schedules"
    assert verify_token(f"svc.schedules.{'x' * 40}", allow_service=True) is None
    assert verify_token("svc.unknown." + SECRET, allow_service=True) is None
    assert verify_service_token("svc.schedules", peers_env) is None


# ---------------------------------------------------------------- outbound hooks
def test_events_are_signed_delivered_and_complete(conn, recv, peers_env):
    assert events.emit_changes(conn, peers_env)["schedules"]["queued"] == 0      # first run: only records the start
    cid = cid_of(conn, "Vaden")
    bump(conn, cid)
    s = events.emit_changes(conn, peers_env)
    assert s["schedules"]["queued"] == 1 and s["formfill"]["queued"] == 1
    assert events.emit_changes(conn, peers_env)["schedules"]["queued"] == 0       # idempotent
    out = events.deliver_due(conn, peers_env)
    assert out["delivered"] == 2 and out["dead"] == 0
    got = recv.got[0]
    # each delivery is signed with ITS peer's secret (one per peer, so one peer can't forge another's)
    used = {name for g in recv.got for name, p in peers_env.items()
            if verify(p.secret, g["body"], g["headers"]["x-ntxp-signature"])}
    assert used == {"schedules", "formfill"}
    assert all(sum(verify(p.secret, g["body"], g["headers"]["x-ntxp-signature"]) for p in peers_env.values()) == 1 for g in recv.got)
    ev = json.loads(got["body"])
    assert got["path"] == "/hooks/ntxp-contacts" and got["headers"]["x-ntxp-event"] == "contact.upserted"
    d = ev["data"]
    assert ev["type"] == "contact.upserted" and d["id"] == cid and d["email"] == "eric@vaden.com"
    assert d["company"] == "Vaden Drywall" and d["address"]["city"] == "Fort Worth" and d["address"]["state"] == "TX"
    assert d["labels"] == ["DBE", "RHCA", "Spruce HS"] and d["phones"] == ["+18178478822"]
    assert {"full_name", "phones", "emails", "address", "labels", "contracts", "href"} <= set(d)
    assert events.outbox_stats(conn) == {"delivered": 2}


def test_no_echo_back_to_the_peer_that_wrote(conn, recv, peers_env):
    events.emit_changes(conn, peers_env)
    cid = cid_of(conn, "Villalpando")
    bump(conn, cid, origin="peer:schedules")
    s = events.emit_changes(conn, peers_env)
    assert s["schedules"]["queued"] == 0 and s["formfill"]["queued"] == 1          # fans out to the OTHER app only


def test_held_back_contacts_are_removed_not_leaked(conn, recv, peers_env):
    events.emit_changes(conn, peers_env)
    cid = cid_of(conn, "Adair")
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()                                                              # -> not exposed
    bump(conn, cid)
    events.emit_changes(conn, peers_env)
    events.deliver_due(conn, peers_env)
    ev = json.loads(recv.got[0]["body"])
    assert ev["type"] == "contact.removed" and ev["data"] == {"id": cid, "merged_into": None}
    assert b"ladair@okc.gov" not in b"".join(g["body"] for g in recv.got)           # no PII for a held-back contact


def test_event_filters_per_peer(conn, recv, monkeypatch):
    monkeypatch.setenv("NTXP_PEER_ALLOW_LOCAL", "1")
    monkeypatch.setenv("NTXP_PEERS", json.dumps({"schedules": {"url": recv.url, "secret": SECRET, "events": ["contact.removed"]}}))
    peers = load_peers()[0]
    events.emit_changes(conn, peers)
    bump(conn, cid_of(conn, "Vaden"))
    assert events.emit_changes(conn, peers)["schedules"]["queued"] == 0             # upserted is filtered out


def test_retry_backoff_then_dead_letter(conn, recv, peers_env):
    events.emit_changes(conn, peers_env)
    bump(conn, cid_of(conn, "Vaden"))
    events.emit_changes(conn, peers_env)
    recv.status = 503                                                               # peer is down
    out = events.deliver_due(conn, peers_env)
    assert out["retried"] == 2 and out["delivered"] == 0
    row = conn.execute("SELECT status, attempts, last_error FROM peer_outbox WHERE peer='schedules'").fetchone()
    assert row["status"] == "pending" and row["attempts"] == 1 and "503" in row["last_error"]
    assert events.deliver_due(conn, peers_env)["retried"] == 0                      # not due yet (backoff)
    conn.execute("UPDATE peer_outbox SET next_attempt_at=?", (pctx.now_ts(conn, -5),))
    conn.commit()
    recv.status = 200                                                               # peer recovers
    assert events.deliver_due(conn, peers_env)["delivered"] == 2
    # a permanent rejection (4xx) is dead at once; the cap kills a never-recovering peer
    bump(conn, cid_of(conn, "Erwin"))
    events.emit_changes(conn, peers_env)
    recv.status = 400
    assert events.deliver_due(conn, peers_env)["dead"] == 2
    bump(conn, cid_of(conn, "Smith"))
    events.emit_changes(conn, peers_env)
    recv.status = 500
    conn.execute("UPDATE peer_outbox SET attempts=? WHERE status='pending'", (events.MAX_ATTEMPTS - 1,))
    conn.commit()
    assert events.deliver_due(conn, peers_env)["dead"] == 2


def test_backfill_sends_everything_exposed_once(conn, recv, peers_env):
    n = events.backfill(conn, peers_env["formfill"])
    assert n == 5
    assert events.deliver_due(conn, peers_env, limit=20)["delivered"] == 5
    assert all(json.loads(g["body"])["type"] == "contact.upserted" for g in recv.got)


# ---------------------------------------------------------------- inbound hooks
def _post(conn, peers, peer, event, secret=None, ts=None, raw=None):
    body = raw if raw is not None else json.dumps(event).encode()
    _, sig = sign(secret or (peers[peer].secret if peer in peers else SECRET), body, ts=ts)
    return inbound.handle(conn, peers, peer, body, {"x-ntxp-signature": sig})


def test_inbound_requires_valid_signature(conn, peers_env):
    ev = {"id": "e1", "type": "ping", "data": {}}
    assert _post(conn, peers_env, "schedules", ev)[0] == 200
    assert _post(conn, peers_env, "schedules", {**ev, "id": "e2"}, secret="w" * 40)[0] == 401
    assert _post(conn, peers_env, "schedules", {**ev, "id": "e3"}, ts=int(time.time()) - 3600)[0] == 401
    assert inbound.handle(conn, peers_env, "schedules", b"{}", {})[0] == 401
    assert _post(conn, peers_env, "nope", ev)[0] == 404
    assert _post(conn, peers_env, "schedules", None, raw=b"not json")[0] == 400
    assert _post(conn, peers_env, "schedules", {"type": "x"})[0] == 400


def test_inbound_is_applied_once(conn, peers_env):
    ev = {"id": "dup-1", "type": "assignment.upserted",
          "data": {"assignment_id": "A1", "project": "Spruce HS", "person": {"email": "eric@vaden.com"}}}
    assert _post(conn, peers_env, "schedules", ev)[1].get("matched") is True
    assert _post(conn, peers_env, "schedules", ev)[1] == {"duplicate": True}        # re-delivery is a no-op


def test_schedules_assignment_lifecycle_and_card(conn, peers_env):
    cid = cid_of(conn, "Vaden")
    end = (date.today() + timedelta(days=20)).isoformat()
    ev = lambda i, t, **d: {"id": i, "type": t, "data": d}
    st, res = _post(conn, peers_env, "schedules", ev("a1", "assignment.upserted", assignment_id="A1", project="Natatorium",
                    role="Sub", start=date.today().isoformat(), end=end, status="active", person={"email": "ERIC@vaden.com"}))
    assert st == 200 and res == {"matched": True, "contact_id": cid}
    from ntxp_contacts.context import HotlinkIndex
    from ntxp_contacts.hooks.contact_context import card_text
    card = HotlinkIndex(conn).card(cid)
    assert card["assignments"][0]["project"] == "Natatorium" and card["assignments"][0]["end"] == end
    assert "🗓 active: Natatorium" in card_text(card)
    # their project is now a filterable label in the live app
    from ntxp_contacts.remote.api import handle
    s, _, b = handle(conn, "t@ntxpllc.com", "GET", "/api/contacts", {"project": "Natatorium"}, {})
    assert [r["id"] for r in json.loads(b)["rows"]] == [cid]
    # an ended / cancelled assignment disappears from the card
    _post(conn, peers_env, "schedules", ev("a2", "assignment.upserted", assignment_id="A1", project="Natatorium", status="cancelled",
                                           person={"email": "eric@vaden.com"}))
    assert HotlinkIndex(conn).card(cid)["assignments"] == []
    assert _post(conn, peers_env, "schedules", ev("a3", "assignment.removed", assignment_id="A1"))[1] == {"removed": 1}


def test_schedules_never_fuzzy_matches(conn, peers_env):
    ev = {"id": "u1", "type": "assignment.upserted",
          "data": {"assignment_id": "A9", "project": "P", "person": {"name": "Eric Vaden", "email": "nobody@nowhere.com"}}}
    assert _post(conn, peers_env, "schedules", ev)[1] == {"matched": False}
    bad = {"id": "u2", "type": "assignment.upserted", "data": {"assignment_id": "A9", "status": "bogus", "person": {"email": "eric@vaden.com"}}}
    assert "error" in _post(conn, peers_env, "schedules", bad)[1]
    assert _post(conn, peers_env, "schedules", {"id": "u3", "type": "future.event", "data": {}})[1] == {"ignored": "future.event"}


def test_formfill_people_seen_ingests_and_dedups(conn, peers_env):
    people = [{"name": "Dana Okafor", "email": "dana@okaforbuilders.com", "phone": "214-555-0188", "company": "Okafor Builders",
               "title": "Estimator", "address": {"line1": "9 Elm St", "city": "Plano", "state": "TX", "zip": "75024"}},
              {"name": "Eric Vaden", "email": "eric@vaden.com"}]               # already known -> merged, not duplicated
    ev = {"id": "f1", "type": "people.seen", "data": {"form": "W-9", "people": people}}
    st, res = _post(conn, peers_env, "formfill", ev)
    assert st == 200 and res["people"] == 2 and res["new"] == 1
    n = conn.execute("SELECT COUNT(*) FROM contacts WHERE is_deleted=0").fetchone()[0]
    assert n == 6
    from ntxp_contacts.remote.api import handle
    s, _, b = handle(conn, "t@ntxpllc.com", "GET", "/api/contacts", {"q": "okafor"}, {})
    row = json.loads(b)["rows"][0]
    assert row["company"] == "Okafor Builders" and row["city"] == "Plano" and "Form: W-9" in row["labels"]
    assert _post(conn, peers_env, "formfill", {"id": "f2", "type": "people.seen", "data": {"people": "x"}})[1].get("error")
    big = {"id": "f3", "type": "people.seen", "data": {"people": [{"name": f"P{i} Q", "email": f"p{i}@x.com"} for i in range(201)]}}
    assert "error" in _post(conn, peers_env, "formfill", big)[1]


# ---------------------------------------------------------------- /api/v1 for peers
def test_v1_resolve_autofill_and_context(conn, peers_env):
    principal = verify_token(f"svc.formfill.{'f' * 40}", allow_service=True)
    call = lambda path, **q: json.loads(handle_v1(conn, principal, "GET", path, q)[2])
    assert call("/api/v1/ping")["as"] == "formfill"
    m = call("/api/v1/people/resolve", email="ERIC@vaden.com")["matches"]
    assert [x["full_name"] for x in m] == ["Eric Vaden"]
    assert call("/api/v1/people/resolve", phone="(817) 847-8822")["matches"][0]["id"] == m[0]["id"]
    assert call("/api/v1/people/resolve", q="vaden")["matches"]
    bag = call(f"/api/v1/people/{m[0]['id']}")
    assert bag["email"] == "eric@vaden.com" and bag["company"] == "Vaden Drywall" and "assignments" in bag
    ctx = call("/api/v1/context", q="Eric Vaden")
    assert "Eric Vaden" in ctx["text"] and ctx["card"]["contact_id"] == m[0]["id"]
    assert handle_v1(conn, principal, "POST", "/api/v1/ping", {})[0] == 405                 # read-only
    assert handle_v1(conn, principal, "GET", "/api/v1/people/resolve", {})[0] == 400
    assert handle_v1(conn, principal, "GET", "/api/v1/people/99999", {})[0] == 404


def test_v1_never_serves_held_back_people(conn, peers_env):
    principal = verify_token(f"svc.formfill.{'f' * 40}", allow_service=True)
    cid = cid_of(conn, "Adair")
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()
    assert json.loads(handle_v1(conn, principal, "GET", "/api/v1/people/resolve", {"email": "ladair@okc.gov"})[2])["matches"] == []
    assert handle_v1(conn, principal, "GET", f"/api/v1/people/{cid}", {})[0] == 404
    assert json.loads(handle_v1(conn, principal, "GET", "/api/v1/context", {"id": str(cid)})[2])["card"] is None


# ---------------------------------------------------------------- Master Contracts (the REAL server)
@pytest.fixture
def contracts_server(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "contracts-db"))
    try:
        from ntxp_contracts.db import connect as cconnect, migrate as cmigrate
        from ntxp_contracts.db.repository import Repository as CRepo
        from ntxp_contracts.model import Contract
        from ntxp_contracts.web.server import make_handler, _ensure_migrated
    except ImportError:
        pytest.skip("contracts-db not importable")
    db = str(tmp_path / "contracts.db")
    _ensure_migrated(db)
    cc = cconnect(db)
    repo = CRepo(cc)
    soon = (date.today() + timedelta(days=30)).isoformat()
    for t, no, owner, exp, ex, coef in [
            ("Statewide JOC", "RFP-2024-77", "Vaden Drywall", soon, True, 1.12),
            ("Coop Painting", "COOP-9", "City of Frisco", (date.today() + timedelta(days=900)).isoformat(), False, 0.95),
            ("Unmatched Owner Deal", "X-1", "Nobody Co", None, True, 1.0)]:
        repo.upsert_contract(Contract(contract_title=t, contract_no=no, contract_type="Job Order Contract", owner_entity=owner,
                                      expiration_date=exp, is_executed=ex, coefficient_multiplier=coef, cooperative_fee="2%"))
    cc.commit()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(db))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", db, repo, cc
    srv.shutdown()


def test_master_contracts_are_watched_linked_and_injected(conn, contracts_server, monkeypatch):
    url, db, repo, cc = contracts_server
    monkeypatch.setenv("NTXP_PEER_ALLOW_LOCAL", "1")
    monkeypatch.setenv("NTXP_PEERS", json.dumps({"contracts": {"url": url, "secret": SECRET}}))
    peer = load_peers()[0]["contracts"]
    assert peer.pulls and not peer.receives_events
    r = pcontracts.pull(conn, peer)
    assert r["contracts"] == 3 and r["linked_to_orgs"] == 2                         # 'Nobody Co' has no matching org
    assert pcontracts.pull(conn, peer)["skipped"] == "no changes"                   # cheap /api/changes probe
    # the card for anyone at Vaden Drywall now carries the contract, with live flags
    from ntxp_contacts.context import HotlinkIndex
    from ntxp_contacts.hooks.contact_context import card_text
    card = HotlinkIndex(conn).card(cid_of(conn, "Vaden"))
    c = card["contracts"][0]
    assert c["number"] == "RFP-2024-77" and c["coefficient"] == 1.12 and c["flags"] == ["expiring"]
    txt = card_text(card)
    assert "📄 contract: RFP-2024-77 — Statewide JOC" in txt and "coef 1.12" in txt and "[expiring]" in txt
    assert HotlinkIndex(conn).card(cid_of(conn, "Erwin"))["contracts"][0]["flags"] == ["unexecuted"]
    # filterable in the live app by contract
    from ntxp_contacts.remote.api import handle
    s, _, b = handle(conn, "t@ntxpllc.com", "GET", "/api/contacts", {"label": "Contract RFP-2024-77"}, {})
    assert [x["full_name"] for x in json.loads(b)["rows"]] == ["Eric Vaden"]
    # an edit in Master Contracts flows through on the next cycle; a deletion removes the label + context
    repo.update_field(repo.get_contract_by_no("COOP-9")["contract_id"], "coefficient_multiplier", 1.5, actor="t")
    cc.commit()
    assert pcontracts.pull(conn, peer)["contracts"] == 3
    assert HotlinkIndex(conn).card(cid_of(conn, "Erwin"))["contracts"][0]["coefficient"] == 1.5
    repo.soft_delete(repo.get_contract_by_no("RFP-2024-77")["contract_id"], actor="t")
    cc.commit()
    pcontracts.pull(conn, peer)
    assert HotlinkIndex(conn).card(cid_of(conn, "Vaden"))["contracts"] == []
    s, _, b = handle(conn, "t@ntxpllc.com", "GET", "/api/contacts", {"label": "Contract RFP-2024-77"}, {})
    assert json.loads(b)["total"] == 0


def test_a_down_peer_does_not_break_the_cycle(conn, recv, monkeypatch):
    monkeypatch.setenv("NTXP_PEER_ALLOW_LOCAL", "1")
    monkeypatch.setenv("NTXP_PEERS", json.dumps({"contracts": {"url": "http://127.0.0.1:9", "secret": SECRET},
                                                  "schedules": {"url": recv.url, "secret": SECRET}}))
    out = run_cycle(conn)
    assert "error" in out["pull"]["contracts"] and out["emit"]["schedules"]["queued"] == 0
    bump(conn, cid_of(conn, "Vaden"))
    out = run_cycle(conn)
    assert out["deliver"]["delivered"] == 1 and recv.got


def test_cycle_is_a_noop_without_peers(conn, monkeypatch):
    monkeypatch.delenv("NTXP_PEERS", raising=False)
    out = run_cycle(conn)
    assert out["emit"] == {} and out["deliver"] == {"delivered": 0, "retried": 0, "dead": 0}


# ---------------------------------------------------------------- the HTTP edge (needs mcp; runs in the venv)
def test_http_edge_scopes_peer_keys(tmp_path, monkeypatch, recv):
    pytest.importorskip("mcp")
    import asyncio
    monkeypatch.setenv("NTXP_MCP_AUTH", "static")
    monkeypatch.setenv("NTXP_MCP_TOKEN", "human")
    monkeypatch.setenv("NTXP_PEER_ALLOW_LOCAL", "1")
    monkeypatch.setenv("NTXP_PEERS_AUTORUN", "0")
    monkeypatch.setenv("NTXP_PEERS", json.dumps({"formfill": {"url": recv.url, "secret": "f" * 40}}))
    from ntxp_contacts.remote.http_server import build_http_app
    db = str(tmp_path / "e.db")
    c = connect(db)
    migrate(c)
    import_records(c, _Loader(DATA), "x")
    c.close()
    app = build_http_app(db)

    def call(method, path, headers=(), body=b"", qs=b""):
        sent = []

        async def r():
            return {"type": "http.request", "body": body, "more_body": False}

        async def s(m):
            sent.append(m)
        asyncio.run(app({"type": "http", "method": method, "path": path, "query_string": qs, "headers": list(headers)}, r, s))
        return sent[0]["status"], json.loads(sent[1]["body"] or b"null") if sent[0]["status"] != 204 else None

    svc = (b"authorization", b"Bearer svc.formfill." + b"f" * 40)
    assert call("GET", "/api/v1/ping", [svc])[0] == 200
    assert call("GET", "/api/v1/people/resolve", [svc], qs=b"email=eric@vaden.com")[1]["matches"][0]["full_name"] == "Eric Vaden"
    assert call("GET", "/api/contacts", [svc])[0] == 401                              # peer key can't use the human API
    assert call("PATCH", "/api/contacts/1", [svc], body=b'{"title":"x"}')[0] == 401   # ...or edit anything
    assert call("GET", "/carddav/", [svc])[0] == 401                                  # ...or pull the iOS feed
    assert call("POST", "/mcp", [svc], body=b"{}")[0] == 401                          # ...or call the MCP tools
    assert call("GET", "/api/v1/ping")[0] == 401
    assert call("GET", "/api/v1/ping", [(b"authorization", b"Bearer human")])[0] == 200   # humans may read v1
    # the signed inbound hook needs no bearer, only a valid signature
    body = json.dumps({"id": "h1", "type": "ping", "data": {}}).encode()
    _, good = sign("f" * 40, body)
    assert call("POST", "/api/v1/hooks/in/formfill", [(b"x-ntxp-signature", good.encode())], body=body)[0] == 200
    assert call("POST", "/api/v1/hooks/in/formfill", [(b"x-ntxp-signature", b"t=1,v1=00")], body=body)[0] == 401
    assert call("GET", "/api/v1/hooks/in/formfill")[0] == 405


# ---------------------------------------------------------------- the published reference verifier (docs/examples)
def test_node_reference_verifier_agrees_with_our_signer(tmp_path):
    """Schedules / Form Fill will copy docs/examples/verify_webhook.js; it must verify what we send
    and produce what we accept — checked against the real signer in both directions."""
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    js = Path(__file__).resolve().parents[1] / "docs" / "examples" / "verify_webhook.js"
    body = '{"id":"x","type":"contact.upserted","data":{"name":"Zoë O\'Brien — 日本"}}'.encode()     # non-ASCII on purpose
    _, header = sign(SECRET, body)
    script = f"""
      const {{verify, sign}} = require({json.dumps(str(js))});
      const body = Buffer.from({json.dumps(body.decode())}, 'utf8');
      const out = {{ok: verify({json.dumps(SECRET)}, body, {json.dumps(header)}),
                   tamper: verify({json.dumps(SECRET)}, Buffer.from('{{}}'), {json.dumps(header)}),
                   wrong: verify('w'.repeat(40), body, {json.dumps(header)}),
                   stale: verify({json.dumps(SECRET)}, body, sign({json.dumps(SECRET)}, body, 1000)),
                   header: sign({json.dumps(SECRET)}, body)}};
      console.log(JSON.stringify(out));"""
    res = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
    assert res["ok"] is True and res["tamper"] is False and res["wrong"] is False and res["stale"] is False
    assert verify(SECRET, body, res["header"])                                       # what Node signs, we accept


def test_background_runner_only_starts_when_configured(monkeypatch, tmp_path):
    from ntxp_contacts.peers.runner import start_background
    monkeypatch.delenv("NTXP_PEERS", raising=False)
    assert start_background(str(tmp_path / "x.db")) is None                             # no peers -> no thread
    monkeypatch.setenv("NTXP_PEER_ALLOW_LOCAL", "1")
    monkeypatch.setenv("NTXP_PEERS", json.dumps({"schedules": {"url": "http://127.0.0.1:9", "secret": SECRET}}))
    monkeypatch.setenv("NTXP_PEERS_AUTORUN", "0")
    assert start_background(str(tmp_path / "x.db")) is None                             # explicitly disabled (cron mode)
