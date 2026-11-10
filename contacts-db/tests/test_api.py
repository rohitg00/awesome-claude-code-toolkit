"""Live-view REST API: filters, proximity, inline edit, labels, reports, CSV, auth."""
import asyncio
import json
import os

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.loaders.base import import_records
from ntxp_contacts.model import Address, CanonicalRecord, Email, Phone, Tag
from ntxp_contacts.qualify import Grader
from ntxp_contacts.remote.api import handle

PG_URL = os.environ.get("NTXP_TEST_PG_URL")


class _Loader:
    source = "tips"

    def __init__(self, recs):
        self.recs = recs

    def rows(self, path):
        yield from range(len(self.recs))

    def to_canonical(self, i):
        return self.recs[i]


def _p(first, last, org, email, city, state, role=None, trade=None, project=None, labels=(), phone=None):
    r = CanonicalRecord(source="tips", source_pk=email)
    r.first_name, r.last_name, r.full_name = first, last, f"{first} {last}"
    r.name_norm = f"{first} {last}".lower()
    r.org_name, r.org_name_norm = org, org.lower()
    r.emails.append(Email(email=email, email_norm=email, is_primary=True))
    if phone:
        r.phones.append(Phone(phone_raw=phone, phone_e164=phone))
    r.org_addresses.append(Address(city=city, state=state, addr_norm=f"{org}|{city}|{state}".lower()))
    r.tags.append(Tag("source", "tips"))
    if role:
        r.tags.append(Tag("role", role))
    if trade:
        r.tags.append(Tag("trade", trade))
    if project:
        r.tags.append(Tag("project", project))
    for l in labels:
        r.tags.append(Tag("label", l))
    return r


DATA = [
    _p("Eric", "Vaden", "Vaden Drywall", "eric@vaden.com", "Fort Worth", "TX", "Sub", "Drywall", "Spruce HS", ("DBE", "RHCA"), "+18178478822"),
    _p("Juan", "Villalpando", "JHL Painting", "juan@jhl.com", "Dallas", "TX", "Sub", "Painting", "Spruce HS", ("DBE",)),
    _p("Erik", "Erwin", "City of Frisco", "eerwin@friscotexas.gov", "Frisco", "TX", "Owner", None, "City Hall"),
    _p("Leon", "Adair", "Okc Fairgrounds", "ladair@okc.gov", "Oklahoma City", "OK", "Inspector"),
    _p("Greg", "Smith", "Jamail Smith", "greg@js.com", "Austin", "TX", "Contractor", "General", None, ("RHCA",)),
]


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


def call(conn, method, path, query=None, body=None, user="t@ntxpllc.com"):
    status, ctype, payload = handle(conn, user, method, path, query or {}, body or {})
    return status, (json.loads(payload) if ctype == "application/json" else payload.decode())


def names(res):
    return sorted(r["full_name"] for r in res["rows"])


def test_list_and_row_shape(conn):
    s, d = call(conn, "GET", "/api/contacts")
    assert s == 200 and d["total"] == 5
    eric = next(r for r in d["rows"] if r["last_name"] == "Vaden")
    assert eric["company"] == "Vaden Drywall" and eric["city"] == "Fort Worth" and eric["state"] == "TX"
    assert eric["role"] == "Sub" and eric["trade"] == "Drywall" and eric["project"] == "Spruce HS"
    assert eric["labels"] == ["DBE", "RHCA", "Spruce HS"]  # project is also a label and eric["domain"] == "vaden.com"


def test_filters(conn):
    assert names(call(conn, "GET", "/api/contacts", {"role": "sub"})[1]) == ["Eric Vaden", "Juan Villalpando"]
    assert names(call(conn, "GET", "/api/contacts", {"state": "OK"})[1]) == ["Leon Adair"]
    assert names(call(conn, "GET", "/api/contacts", {"label": "RHCA"})[1]) == ["Eric Vaden", "Greg Smith"]
    assert names(call(conn, "GET", "/api/contacts", {"label": "Vaden Drywall"})[1]) == ["Eric Vaden"]  # company auto-label
    assert names(call(conn, "GET", "/api/contacts", {"project": "Spruce HS", "trade": "Painting"})[1]) == ["Juan Villalpando"]
    assert names(call(conn, "GET", "/api/contacts", {"q": "friscotexas"})[1]) == ["Erik Erwin"]


def test_proximity_miles(conn):
    near = call(conn, "GET", "/api/contacts", {"near": "Dallas,TX", "miles": "40"})[1]
    assert names(near) == ["Eric Vaden", "Erik Erwin", "Juan Villalpando"]  # FW ~31mi, Frisco ~26mi
    assert all("miles" in r for r in near["rows"])
    far = call(conn, "GET", "/api/contacts", {"near": "Dallas,TX", "miles": "5"})[1]
    assert names(far) == ["Juan Villalpando"]
    assert call(conn, "GET", "/api/contacts", {"near": "Atlantis", "miles": "5"})[0] == 400


def test_sort_and_paging(conn):
    d = call(conn, "GET", "/api/contacts", {"sort": "company", "dir": "desc", "limit": "2"})[1]
    assert d["total"] == 5 and len(d["rows"]) == 2
    assert d["rows"][0]["company"] == "Vaden Drywall"


def test_inline_edit_persists_and_logs(conn):
    cid = call(conn, "GET", "/api/contacts", {"q": "vaden"})[1]["rows"][0]["id"]
    s, d = call(conn, "PATCH", f"/api/contacts/{cid}",
                body={"title": "Owner", "city": "Dallas", "role": "Owner", "email": "eric.v@vaden.com",
                      "last_name": "Vaden Jr"}, user="ed@ntxpllc.com")
    assert s == 200 and d["contact"]["title"] == "Owner" and d["contact"]["city"] == "Dallas"
    assert d["contact"]["role"] == "Owner" and d["contact"]["email"] == "eric.v@vaden.com"
    assert d["contact"]["full_name"] == "Eric Vaden Jr"
    origins = {r["origin"] for r in conn.execute("SELECT origin FROM change_log WHERE entity_id=?", (cid,))}
    assert "ui:ed@ntxpllc.com" in origins     # edit is attributed + feeds sync fan-out


def test_edit_validation(conn):
    cid = call(conn, "GET", "/api/contacts")[1]["rows"][0]["id"]
    assert call(conn, "PATCH", f"/api/contacts/{cid}", body={"email": "nope"})[0] == 400
    assert call(conn, "PATCH", f"/api/contacts/{cid}", body={"is_deleted": 1})[0] == 400
    assert call(conn, "PATCH", f"/api/contacts/{cid}", body={"state": "Narnia"})[0] == 400
    assert call(conn, "PATCH", "/api/contacts/99999", body={"title": "x"})[0] == 404


def test_labels_add_remove(conn):
    cid = call(conn, "GET", "/api/contacts", {"q": "erwin"})[1]["rows"][0]["id"]
    call(conn, "POST", f"/api/contacts/{cid}/labels", body={"add": ["Dallas ISD", "Social"]})
    row = call(conn, "GET", "/api/contacts", {"label": "Dallas ISD"})[1]["rows"][0]
    assert "Social" in row["labels"]
    call(conn, "POST", f"/api/contacts/{cid}/labels", body={"remove": ["Social"]})
    assert "Social" not in call(conn, "GET", "/api/contacts", {"label": "Dallas ISD"})[1]["rows"][0]["labels"]


def test_facets(conn):
    d = call(conn, "GET", "/api/facets")[1]
    assert "Sub" in d["role"] and "TX" in d["state"] and d["total"] == 5
    assert any(l["value"] == "DBE" and l["count"] == 2 for l in d["labels"])
    c = call(conn, "GET", "/api/facets", {"field": "company", "q": "va"})[1]
    assert [v["value"] for v in c["values"]] == ["Vaden Drywall"]


def test_report_specs_and_csv(conn):
    s, d = call(conn, "GET", "/api/report", {"type": "trade"})
    assert s == 200 and {x["title"] for x in d["spec"]["sections"]} >= {"Drywall", "Painting"}
    d = call(conn, "GET", "/api/report", {"type": "directory", "project": "Spruce HS"})[1]["spec"]
    assert d["doc_title"] == "Project Directory" and d["project_title"] == "Spruce HS"
    assert [x["title"] for x in d["sections"]] == ["Summary", "Owner / Inspectors", "Design Team", "NTXP LLC", "Subcontractors"]
    subs = d["sections"][-1]["rows"]
    assert len(subs) == 2 and subs[0][-1].endswith(".com") and subs[0][-2] == "817-847-8822"
    assert d["orientation"] == "portrait" and "Title" not in d["sections"][-1]["columns"]
    land = call(conn, "GET", "/api/report", {"type": "full", "orientation": "landscape"})[1]["spec"]
    assert "Title" in land["sections"][1]["columns"]
    assert call(conn, "GET", "/api/report", {"type": "bogus"})[0] == 400
    s, csv_text = call(conn, "GET", "/api/export.csv", {"state": "TX"})
    assert s == 200 and csv_text.splitlines()[0].startswith("ID,First,Last") and len(csv_text.splitlines()) == 5


def test_held_back_contacts_never_served(conn):
    cid = call(conn, "GET", "/api/contacts", {"q": "adair"})[1]["rows"][0]["id"]
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()
    assert call(conn, "GET", "/api/contacts", {"q": "adair"})[1]["total"] == 0
    assert "Leon Adair" not in call(conn, "GET", "/api/export.csv")[1]


def test_unknown_route(conn):
    assert call(conn, "GET", "/api/nope")[0] == 404


# -- ASGI shell: auth + routing + static page ----------------------------------

def _asgi(app, method, path, headers=None, body=b"", qs=b""):
    sent = []

    async def recv():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(m):
        sent.append(m)

    asyncio.run(app({"type": "http", "method": method, "path": path, "query_string": qs,
                     "headers": headers or []}, recv, send))
    return sent[0]["status"], dict(sent[0]["headers"]), sent[1]["body"]


def test_asgi_auth_and_static(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    monkeypatch.setenv("NTXP_MCP_AUTH", "static")
    monkeypatch.setenv("NTXP_MCP_TOKEN", "tok")
    monkeypatch.setenv("NTXP_GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    from ntxp_contacts.remote.http_server import build_http_app
    app = build_http_app(str(tmp_path / "a.db"))
    s, h, b = _asgi(app, "GET", "/api/contacts")
    assert s == 401
    s, h, b = _asgi(app, "GET", "/api/contacts", [(b"authorization", b"Bearer tok")])
    assert s == 200 and json.loads(b)["total"] == 0
    s, h, b = _asgi(app, "GET", "/config.js")
    assert s == 200 and b"abc.apps.googleusercontent.com" in b
    s, h, b = _asgi(app, "GET", "/")
    assert s == 200 and b"content-security-policy" in h and b"NTXP" in b


def test_project_filter_matches_any_of_a_contacts_projects(conn):
    from ntxp_contacts.db.repository import Repository
    from ntxp_contacts.model import Tag
    cid = call(conn, "GET", "/api/contacts", {"q": "vaden"})[1]["rows"][0]["id"]   # already on "Spruce HS"
    Repository(conn).add_tag(Tag("project", "Natatorium"), "contact", cid)
    conn.commit()
    for proj in ("Spruce HS", "Natatorium"):                                        # both work, not just the first
        assert [r["id"] for r in call(conn, "GET", "/api/contacts", {"project": proj})[1]["rows"] if r["id"] == cid] == [cid]
    vals = [v["value"] for v in call(conn, "GET", "/api/facets", {"field": "project"})[1]["values"]]
    assert "Natatorium" in vals and "Spruce HS" in vals
    assert "Natatorium" in call(conn, "GET", "/api/facets")[1]["project"]
