"""Layer B — tool-agnostic context hooks (blue hotlink injection)."""
import pytest

from ntxp_contacts.context import BLUE, HotlinkIndex, annotate
from ntxp_contacts.db import connect, migrate
from ntxp_contacts.sync.base import RemoteRecord
from ntxp_contacts.sync.reconcile import Reconciler


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    Reconciler(c, "jobtread").apply([RemoteRecord(external_id="JT1", payload={
        "firstName": "Eric", "lastName": "Vaden", "company": "Vaden Drywall",
        "email": "eric@vaden.com", "phone": "817-847-8822"})])
    return c


def _cid(conn):
    return conn.execute("SELECT contact_id FROM contacts WHERE is_deleted=0 LIMIT 1").fetchone()["contact_id"]


def test_annotate_wraps_email_phone_name_org(conn):
    text = "Call Eric Vaden at (817) 847-8822 or eric@vaden.com re: Vaden Drywall."
    out = annotate(conn, text)
    vias = {l["via"] for l in out["links"]}
    assert {"email", "phone", "name"} <= vias
    assert any(l["kind"] == "org" for l in out["links"])
    assert BLUE in out["html"]
    assert "focus=contact:" in out["html"] and "focus=org:" in out["html"]


def test_single_first_name_not_linked(conn):
    # a bare first name must not hotlink (conservative multi-word policy)
    out = annotate(conn, "Eric will call later.")
    assert out["links"] == []


def test_card_has_links_and_fields(conn):
    idx = HotlinkIndex(conn)
    cid = _cid(conn)
    d = idx.card(cid)
    assert d["name"] == "Eric Vaden" and d["org"] == "Vaden Drywall"
    assert d["email"] == "eric@vaden.com"
    assert d["href"].endswith(f"focus=contact:{cid}")
    html = idx.card_html(cid)
    assert "mailto:eric@vaden.com" in html and BLUE in html
