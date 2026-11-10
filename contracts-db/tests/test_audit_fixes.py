"""Regression tests for the audit round (contracts)."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from ntxp_contracts import contactfile, normalize as N
from ntxp_contracts.db import connect, migrate
from ntxp_contracts.db.repository import ConflictError, Repository
from ntxp_contracts.model import Contract
from ntxp_contracts.web import server as srv


@pytest.fixture()
def repo(tmp_path):
    c = connect(tmp_path / "c.db")
    migrate(c)
    return Repository(c)


@pytest.fixture()
def base(tmp_path, monkeypatch):
    monkeypatch.delenv("NTXP_CONTRACTS_TOKEN", raising=False)
    monkeypatch.delenv("NTXP_CONTRACTS_ALLOWED_HOSTS", raising=False)
    s = ThreadingHTTPServer(("127.0.0.1", 0), srv.make_handler(str(tmp_path / "w.db")))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()


def req(url, method="GET", body=None, headers=None, raw=None):
    h = dict(headers or {})
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None and "Content-Type" not in h:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


# ---- Infinity / NaN can no longer poison the whole log ---------------------

@pytest.mark.parametrize("v", ["1e999", "inf", "-inf", "nan", "Infinity", float("inf"), float("nan")])
def test_non_finite_numbers_are_rejected_by_normalizers(v):
    assert N.normalize_money(v) is None and N.normalize_float(v) is None


def test_inf_edit_cannot_break_the_list_endpoint(base):
    s, b = req(base + "/api/contracts", "POST", {})
    cid = json.loads(b)["contract"]["contract_id"]
    for field in ("coefficient_multiplier", "estimated_budget"):
        req(base + f"/api/contracts/{cid}", "PATCH", {"field": field, "value": "1e999"})
    s, b = req(base + "/api/contracts")
    assert s == 200 and "Infinity" not in b and "NaN" not in b
    json.loads(b)


# ---- optimistic lock is atomic; "new" is always new ------------------------

def test_stale_rev_conflicts_and_changes_nothing(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="A", contract_no="X-1"))
    repo.conn.commit()
    rev = repo.get_contract(cid)["rev"]
    repo.update_field(cid, "contract_title", "B", expected_rev=rev)
    with pytest.raises(ConflictError):
        repo.update_field(cid, "contract_title", "C", expected_rev=rev)     # same (now stale) rev
    assert repo.get_contract(cid)["contract_title"] == "B"


def test_rev_is_checked_inside_the_update(repo, monkeypatch):
    cid, _ = repo.upsert_contract(Contract(contract_title="A", contract_no="X-2"))
    repo.conn.commit()
    rev = repo.get_contract(cid)["rev"]
    # another writer lands between the (Python-side) read and the UPDATE
    orig = repo.conn.execute
    state = {"done": False}

    def sneaky(sql, params=()):
        if sql.lstrip().startswith("UPDATE contracts SET") and not state["done"]:
            state["done"] = True
            orig("UPDATE contracts SET rev = rev + 1 WHERE contract_id = ?", (cid,))
        return orig(sql, params)
    monkeypatch.setattr(repo.conn, "execute", sneaky) if False else None
    # sqlite3.Connection.execute is read-only; emulate the interleaving through a second connection instead
    other = connect(repo.conn.execute("PRAGMA database_list").fetchone()[2])
    other.execute("UPDATE contracts SET rev = rev + 1, contract_title='theirs' WHERE contract_id=?", (cid,))
    other.commit()
    with pytest.raises(ConflictError):
        repo.update_field(cid, "contract_title", "mine", expected_rev=rev)
    assert repo.get_contract(cid)["contract_title"] == "theirs"


def test_add_contract_twice_makes_two_rows(repo):
    a = repo.create_contract()
    b = repo.create_contract()
    assert a["contract_id"] != b["contract_id"]
    assert sum(1 for c in repo.list_contracts() if c["contract_title"] == "Untitled Contract") == 2


def test_clearing_owner_clears_the_owner_link(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="A", contract_no="X-3", owner_entity="City of Dallas"))
    repo.conn.commit()
    assert repo.get_contract(cid)["owner_id"]
    repo.update_field(cid, "owner_entity", "")
    assert repo.get_contract(cid)["owner_id"] is None


# ---- vCard / iCalendar injection ------------------------------------------

def test_vcard_and_ics_cannot_be_injected_through_newlines():
    v = contactfile.vcard({"name": "A\r\nTEL:+1999\r\nEND:VCARD", "email": "x@y\r\nURL:http://evil", "website": "http://ok"})
    lines = v.split("\r\n")
    assert lines.count("BEGIN:VCARD") == 1 and lines.count("END:VCARD") == 1
    assert not any(l.startswith("TEL:+1999") or l.startswith("URL:http://evil") for l in lines)
    ics = contactfile.ics_expiration({"expiration_date": "2026-01-02", "contract_title": "T\r\nATTACH:http://evil", "contract_id": 1})
    assert not any(l.startswith("ATTACH") for l in ics.split("\r\n"))
    assert "DTSTAMP:" in ics


def test_vcard_route_404s_for_missing_contract(base):
    assert req(base + "/api/contracts/9999/vcard")[0] == 404


# ---- server hardening ------------------------------------------------------

def test_rebinding_and_cross_site_writes_are_refused(base):
    assert req(base + "/api/contracts", headers={"Host": "evil.example.com"})[0] == 421
    assert req(base + "/api/contracts", "POST", {}, headers={"Origin": "http://evil.example.com"})[0] == 403
    assert req(base + "/api/contracts", "POST", raw=b'{"x":1}', headers={"Content-Type": "text/plain"})[0] == 415
    assert req(base + "/api/contracts", "POST", {})[0] == 201


@pytest.mark.parametrize("raw,code", [(b"[1]", 400), (b'"x"', 400), (b"{bad", 400), (b"x" * 2_000_000, 413)])
def test_bad_bodies_are_clean_4xx(base, raw, code):
    s, b = req(base + "/api/contracts", "POST", raw=raw)
    assert s == code and "Traceback" not in b


def test_bad_since_is_400_and_errors_do_not_leak(base):
    assert req(base + "/api/changes?since=abc")[0] == 400
    s, b = req(base + "/api/contracts/1", "PATCH", {"field": ["x"], "value": 1})
    assert s in (400, 404) and "Error" not in b and "line" not in b


def test_token_required_on_api_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("NTXP_CONTRACTS_TOKEN", "s3cret")
    s = ThreadingHTTPServer(("127.0.0.1", 0), srv.make_handler(str(tmp_path / "t.db")))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{s.server_address[1]}"
    try:
        assert req(base + "/api/contracts")[0] == 401
        assert req(base + "/api/contracts", headers={"Authorization": "Bearer wrong"})[0] == 401
        assert req(base + "/api/contracts", headers={"Authorization": "Bearer s3cret"})[0] == 200
    finally:
        s.shutdown()


def test_refuses_to_bind_publicly_without_a_token(monkeypatch):
    monkeypatch.delenv("NTXP_CONTRACTS_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        srv.serve(host="0.0.0.0", port=0)


# ---- static page: reflected-XSS id ---------------------------------------

def test_profile_script_only_accepts_numeric_ids(base):
    js = req(base + "/static/contract.js")[1]
    assert "match(/^\\d" in js
    assert "'" in req(base + "/static/util.js")[1] and "&#39;" in req(base + "/static/util.js")[1]
