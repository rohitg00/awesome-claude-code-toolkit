"""Layer A — delta reconciliation + CRM adapters (offline; no live CRM I/O)."""
import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.sync.base import RemoteRecord, get_adapter
from ntxp_contacts.sync.engine import SyncEngine
from ntxp_contacts.sync.reconcile import Reconciler


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def _rr(ext, **payload):
    return RemoteRecord(external_id=ext, payload=payload)


# -- adapter field mappings --------------------------------------------------

def test_jobtread_mapping():
    a = get_adapter("jobtread")
    rec = a.to_canonical(_rr("JT1", firstName="Eric", lastName="Vaden",
                             company="Vaden Drywall", email="Eric@Vaden.com",
                             phone="817-847-8822"))
    assert rec.first_name == "Eric" and rec.last_name == "Vaden"
    assert rec.org_name == "Vaden Drywall"
    assert rec.emails[0].email_norm == "eric@vaden.com"
    assert rec.phones[0].phone_e164 == "+18178478822"
    assert any(t.kind == "source" and t.value == "jobtread" for t in rec.tags)


def test_quickbooks_nested_mapping():
    a = get_adapter("quickbooks")
    rec = a.to_canonical(_rr("QB1", GivenName="Juan", FamilyName="Villalpando",
                             CompanyName="JHL Painting",
                             PrimaryEmailAddr={"Address": "juan@jhl.com"},
                             PrimaryPhone={"FreeFormNumber": "(817) 703-6029"}))
    assert rec.full_name == "Juan Villalpando"
    assert rec.org_name == "JHL Painting"
    assert rec.emails[0].email_norm == "juan@jhl.com"
    assert rec.phones[0].phone_e164 == "+18177036029"


def test_buildingconnected_mapping():
    a = get_adapter("buildingconnected")
    rec = a.to_canonical(_rr("BC1", name="Sherri Snowden", company="Warden Construction",
                             email="sherri@warden.com"))
    assert rec.full_name == "Sherri Snowden"
    assert rec.org_name == "Warden Construction"


# -- delta plan transitions --------------------------------------------------

def test_plan_create_then_unchanged(conn):
    remotes = [_rr("JT1", firstName="Eric", lastName="Vaden",
                   company="Vaden Drywall", email="eric@vaden.com")]
    r = Reconciler(conn, "jobtread")
    plan1 = r.plan(remotes)
    assert plan1["summary"]["created"] == 1
    r.apply(remotes)
    plan2 = Reconciler(conn, "jobtread").plan(remotes)
    assert plan2["summary"]["unchanged"] == 1
    assert plan2["summary"]["created"] == 0


def test_link_by_email_across_systems(conn):
    # Lightfield (canonical) creates the contact first.
    lf = Reconciler(conn, "lightfield")
    lf.apply([_rr("LF1", first_name="Eric", last_name="Vaden",
                  company="Vaden Drywall", email="eric@vaden.com")])
    # JobTread sees the same person (same email) with no prior link -> 'link'.
    jt = Reconciler(conn, "jobtread")
    plan = jt.plan([_rr("JT1", firstName="Eric", lastName="Vaden",
                        company="Vaden Drywall", email="eric@vaden.com")])
    assert plan["summary"]["linked"] == 1
    assert plan["ops"][0]["op"] == "link"
    assert plan["ops"][0]["contact_id"] is not None


def test_conflict_flagged(conn):
    jt = Reconciler(conn, "jobtread")
    jt.apply([_rr("JT1", firstName="Eric", lastName="Vaden",
                  company="Vaden Drywall", email="eric@vaden.com", title="Owner")])
    # Same linked record, but the remote now reports a different title.
    plan = jt.plan([_rr("JT1", firstName="Eric", lastName="Vaden",
                        company="Vaden Drywall", email="eric@vaden.com",
                        title="President")])
    assert plan["ops"][0]["op"] == "conflict"
    assert "title" in plan["ops"][0]["conflicts"]


def test_apply_unchanged_linked_record_is_skipped(conn):
    rr = [_rr("JT1", firstName="Eric", lastName="Vaden",
              company="Vaden Drywall", email="eric@vaden.com")]
    jt = Reconciler(conn, "jobtread")
    jt.apply(rr)
    seq1 = conn.execute("SELECT COUNT(*) FROM change_log").fetchone()[0]
    out = jt.apply(rr)   # identical payload, already linked
    seq2 = conn.execute("SELECT COUNT(*) FROM change_log").fetchone()[0]
    assert out["unchanged"] == 1
    assert out["updated"] == 0
    assert seq2 == seq1   # no redundant change_log / fan-out churn


def test_no_echo_but_fans_out(conn):
    # Pull from JobTread and apply into canonical.
    jt = Reconciler(conn, "jobtread")
    jt.apply([_rr("JT1", firstName="Eric", lastName="Vaden",
                  company="Vaden Drywall", email="eric@vaden.com")])
    # The pulled change must NOT be pushed back to JobTread...
    assert SyncEngine(conn, "jobtread").plan("push") == []
    # ...but it should fan out to the other systems (e.g. QuickBooks).
    qb_plan = SyncEngine(conn, "quickbooks").plan("push")
    assert qb_plan and qb_plan[0]["op"] == "create"
