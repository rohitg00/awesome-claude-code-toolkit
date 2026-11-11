"""Layer F — JEV qualification / grading."""
import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.qualify import Grader, band, score
from ntxp_contacts.sync.base import RemoteRecord
from ntxp_contacts.sync.reconcile import Reconciler


# -- pure policy (no DB) -----------------------------------------------------

def test_score_monotonic_in_each_axis():
    base = score(60, 30, 1, 1)
    assert score(100, 30, 1, 1) > base          # better source
    assert score(60, 30, 1, 1) > score(60, 900, 1, 1)   # fresher beats older
    assert score(60, 30, 3, 1) > base           # more corroboration
    assert score(60, 30, 1, 0) > base           # nearer the person
    assert 0.0 <= base <= 1.0


def test_bands():
    assert band(0.85) == "A"
    assert band(0.65) == "B"
    assert band(0.45) == "C"
    assert band(0.20) == "D"


# -- end to end --------------------------------------------------------------

@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def _seed(conn):
    Reconciler(conn, "lightfield").apply([RemoteRecord(
        external_id="LF1",
        payload={"first_name": "Eric", "last_name": "Vaden",
                 "company": "Vaden Drywall", "email": "eric@vaden.com"})])
    return conn.execute(
        "SELECT contact_id FROM contacts WHERE is_deleted=0 LIMIT 1").fetchone()["contact_id"]


def test_fresh_contact_is_graded_and_exposed(conn):
    cid = _seed(conn)
    summary = Grader(conn).run()
    assert summary["graded"] == 1
    g = Grader(conn).get_grade(cid)
    assert g is not None
    assert 0.0 <= g["grade"] <= 1.0
    assert g["is_exposed"] == 1 and g["is_synced"] == 1
    assert g["sources"] == 1


def test_outdated_contact_held_back(conn):
    cid = _seed(conn)
    # Age the only observation well past the exposure cutoff.
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' "
                 "WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()
    g = Grader(conn).get_grade(cid)
    assert g["is_exposed"] == 0 and g["is_synced"] == 0
    assert "OUTDATED" in g["reason"]


def test_plan_does_not_write(conn):
    _seed(conn)
    Grader(conn).run(apply=False)
    assert conn.execute("SELECT COUNT(*) FROM contact_grade").fetchone()[0] == 0


def test_held_back_contact_excluded_from_push(conn):
    from ntxp_contacts.sync.engine import SyncEngine
    cid = _seed(conn)
    # Fresh + graded: eligible to fan out to QuickBooks.
    Grader(conn).run()
    assert SyncEngine(conn, "quickbooks").plan("push"), "fresh contact should be pushable"
    # Age it out -> not-synced -> excluded from the push plan.
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()
    assert SyncEngine(conn, "quickbooks").plan("push") == []
