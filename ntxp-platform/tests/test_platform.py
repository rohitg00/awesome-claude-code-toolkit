import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ntxp_platform.hub import Denied, dispatch, make_handler, parse_upstreams
from ntxp_platform.registry import load_registry, norm


@pytest.fixture()
def world(tmp_path, monkeypatch):
    monkeypatch.setenv("NTXP_DB_PATH", str(tmp_path / "contacts.db"))
    monkeypatch.delenv("NTXP_DB_URL", raising=False)
    monkeypatch.setenv("NTXP_CONTRACTS_DB", str(tmp_path / "contracts.db"))
    monkeypatch.setenv("NTXP_APILOG_DB_PATH", str(tmp_path / "apilog.db"))
    from cryptography.fernet import Fernet
    monkeypatch.setenv("NTXP_APILOG_KEY", Fernet.generate_key().decode())

    from ntxp_contacts.collect import ingest
    from ntxp_contacts.db import connect, migrate
    from ntxp_contacts.model import CanonicalRecord, Email
    from ntxp_contacts.normalize import org_name_norm
    c = connect(None); migrate(c)
    ingest(c, [CanonicalRecord(source="t", source_pk="1", org_name="Dallas ISD",
                               org_name_norm=org_name_norm("Dallas ISD"), first_name="Ana", last_name="Ruiz",
                               full_name="Ana Ruiz", name_norm="ana ruiz", emails=[Email("ana@dallasisd.org", "ana@dallasisd.org")])])
    c.commit()

    from ntxp_contracts.db import connect as cc, migrate as cm
    from ntxp_contracts.db.repository import Repository
    from ntxp_contracts.model import Contract
    r = cc(None); cm(r)
    Repository(r).upsert_contract(Contract(contract_title="DISD JOC", contract_no="JOC-1",
                                           owner_entity="Dallas ISD", expiration_date="2099-01-01"))
    r.commit()
    from ntxp_apilog.db import connect as ac, migrate as am
    from ntxp_apilog.db.repository import Repository as AR
    from ntxp_apilog.crypto import Cipher
    from ntxp_apilog.model import ApiEntry
    a = ac(None); am(a)
    AR(a, cipher=Cipher()).upsert_api(ApiEntry(name="Acme", provider="Acme", api_key="sk-SECRET-VALUE-123"))
    a.commit()
    return load_registry()


def test_profile_combines_all_apps(world):
    p = world.profile()
    assert set(p["apps"]) == {"contacts", "contracts", "apilog", "links"}
    assert p["counts"]["fields"] > 40 and p["counts"]["functions"] >= 15
    assert "contracts.contract.owner_entity" in p["joins"]["org_name"]
    assert "contacts.org.name" in p["joins"]["org_name"]


def test_profile_flags_secret_fields_and_carries_no_data(world):
    p = json.dumps(world.profile())
    assert "sk-SECRET-VALUE-123" not in p
    secrets = [f["name"] for f in world.profile()["apps"]["apilog"]["fields"] if f["secret"]]
    assert "apilog.api.api_key" in secrets


def test_cross_app_links_join_on_org_name(world):
    r = dispatch(world, "links.contract_contacts", {"contract_no": "JOC-1"}, "contacts")
    assert r["owner"] == "Dallas ISD" and [x["full_name"] for x in r["people"]] == ["Ana Ruiz"]
    d = dispatch(world, "links.entity_dossier", {"name": "dallas  isd"}, "contracts")
    assert [c["contract_no"] for c in d["contracts"]] == ["JOC-1"]
    assert d["people"] and d["people"][0]["full_name"] == "Ana Ruiz"


def test_missing_contract_is_a_clean_error(world):
    assert "error" in dispatch(world, "links.contract_contacts", {"contract_no": "NOPE"}, "all")


def test_apilog_is_isolated_both_ways(world):
    with pytest.raises(Denied):                      # apilog view can't reach other apps
        dispatch(world, "contracts.stats", {}, "apilog")
    with pytest.raises(Denied):                      # contacts view can't reach apilog
        dispatch(world, "apilog.find_api", {"query": "acme"}, "contacts")
    with pytest.raises(Denied):                      # secrets never via dispatch, even in 'all'
        dispatch(world, "apilog.get_credentials", {"name_or_id": "Acme"}, "all")


def test_apilog_find_is_masked(world):
    out = json.dumps(dispatch(world, "apilog.find_api", {"query": "acme"}, "apilog"), default=str)
    assert "sk-SECRET-VALUE-123" not in out and "Acme" in out


def test_writes_blocked_by_default(world):
    from ntxp_platform.registry import FuncSpec
    world.apps["contracts"].functions.append(FuncSpec("w", "x", read_only=False, handler=lambda: 1, app="contracts"))
    with pytest.raises(Denied):
        dispatch(world, "contracts.w", {}, "all")
    assert dispatch(world, "contracts.w", {}, "all", allow_write=True) == 1


def test_norm_and_upstreams():
    assert norm("Dallas, I.S.D.") == "dallas i s d"
    assert parse_upstreams("contacts=http://127.0.0.1:1/,bad,x=ftp://y") == {"contacts": "http://127.0.0.1:1"}


def _serve(handler):
    s = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_address[1]}"


def _req(url, host, method="GET", body=None, token=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    r.add_header("Host", host)
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_hub_http_routes_by_host_and_gates_calls(world):
    class Up(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            b = f"{self.server.name}:{self.path}:{self.headers.get('X-Forwarded-Host')}".encode()
            self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    a, au = _serve(Up); a.name = "contacts-app"
    b, bu = _serve(Up); b.name = "contracts-app"
    hub, hu = _serve(make_handler(world, token="tok", upstreams={"contacts": au, "contracts": bu}))
    try:
        assert _req(hu + "/x?y=1", "contacts.ntxpllc.cloud")[1].startswith("contacts-app:/x?y=1:contacts.ntxpllc.cloud")
        assert _req(hu + "/x", "contracts.ntxpllc.cloud")[1].startswith("contracts-app:")
        assert _req(hu + "/x", "evil.example.com")[0] == 404
        assert _req(hu + "/_ntxp/profile", "contacts.ntxpllc.cloud")[0] == 401
        assert _req(hu + "/_ntxp/profile", "contacts.ntxpllc.cloud", token="wrong")[0] == 401
        assert _req(hu + "/_ntxp/profile", "contacts.ntxpllc.cloud", token="tok")[0] == 200
        code, out = _req(hu + "/_ntxp/call", "contacts.ntxpllc.cloud", "POST",
                         {"function": "links.contract_contacts", "args": {"contract_no": "JOC-1"}}, "tok")
        assert code == 200 and "Ana Ruiz" in out
        # per-host view scoping: apilog host cannot reach contacts data; sensitive never
        assert _req(hu + "/_ntxp/call", "api.ntxpllc.cloud", "POST",
                    {"function": "contracts.stats"}, "tok")[0] == 403
        assert _req(hu + "/_ntxp/call", "api.ntxpllc.cloud", "POST",
                    {"function": "apilog.get_credentials", "args": {"name_or_id": "Acme"}}, "tok")[0] == 403
        assert _req(hu + "/_ntxp/call", "contacts.ntxpllc.cloud", "POST", {"function": "nope.x"}, "tok")[0] == 404
    finally:
        for s in (a, b, hub): s.shutdown()


def test_hub_without_token_refuses_all_calls(world):
    hub, hu = _serve(make_handler(world, token="", upstreams={}))
    try:
        assert _req(hu + "/_ntxp/profile", "contacts.ntxpllc.cloud")[0] == 401
        assert _req(hu + "/_ntxp/profile", "contacts.ntxpllc.cloud", token="")[0] == 401
    finally:
        hub.shutdown()


def test_sensitive_denied_even_with_handler(world):
    from ntxp_platform.registry import FuncSpec
    world.apps["apilog"].functions.append(
        FuncSpec("leak", "x", sensitive=True, handler=lambda: "sk-LEAK", app="apilog"))
    for view in ("all", "apilog"):
        with pytest.raises(Denied, match="secrets"):
            dispatch(world, "apilog.leak", {}, view, allow_write=True)
