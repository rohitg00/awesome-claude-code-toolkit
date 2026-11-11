"""Postgres-backend parity tests.

Skipped unless NTXP_TEST_PG_URL points at a reachable Postgres (and psycopg is
installed). Exercises the same loader/resolver/sync path as the SQLite suite to
prove the dual-target backend behaves identically.

    NTXP_TEST_PG_URL=postgresql://user@/db?host=/sock python -m pytest tests/test_postgres.py
"""
import os

import pytest

PG_URL = os.environ.get("NTXP_TEST_PG_URL")
pytestmark = pytest.mark.skipif(not PG_URL, reason="NTXP_TEST_PG_URL not set")

psycopg = pytest.importorskip("psycopg")

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.db.repository import Repository
from ntxp_contacts.loaders.base import import_records
from ntxp_contacts.model import CanonicalRecord, Address, Email, Phone, Tag
from ntxp_contacts.sync.base import RemoteRecord
from ntxp_contacts.sync.engine import SyncEngine
from ntxp_contacts.sync.reconcile import Reconciler


class _FakeLoader:
    source = "tips"

    def __init__(self, records):
        self._records = records

    def rows(self, path):
        yield from range(len(self._records))

    def to_canonical(self, i):
        return self._records[i]


def _person(name_norm, first, last, org, email=None, phone=None, state=None,
            source="tips", pk=None):
    rec = CanonicalRecord(source=source, source_pk=pk or name_norm)
    rec.org_name = org
    rec.org_name_norm = org.lower() if org else None
    rec.first_name, rec.last_name, rec.full_name = first, last, f"{first} {last}"
    rec.name_norm = name_norm
    if email:
        rec.emails.append(Email(email=email, email_norm=email, is_primary=True))
    if phone:
        rec.phones.append(Phone(phone_raw=phone, phone_e164=phone))
    if state:
        rec.org_addresses.append(Address(state=state, addr_norm=f"{org}|{state}".lower()))
    rec.tags.append(Tag("source", source))
    return rec


@pytest.fixture
def conn():
    c = connect(PG_URL)
    # Clean slate each test.
    c.execute("DROP SCHEMA public CASCADE")
    c.execute("CREATE SCHEMA public")
    c.commit()
    migrate(c)
    assert getattr(c, "backend", "sqlite") == "postgres"
    yield c
    c.close()


def test_email_dedup_merges(conn):
    recs = [
        _person("john smith", "John", "Smith", "Acme", email="js@acme.com", pk="r1"),
        _person("j smith", "J", "Smith", "Acme", email="js@acme.com", pk="r2"),
    ]
    import_records(conn, _FakeLoader(recs), "x")
    assert Repository(conn).stats()["contacts"] == 1


def test_distinct_people_not_merged(conn):
    recs = [
        _person("john smith", "John", "Smith", "Acme", email="john@acme.com", pk="r1"),
        _person("jane doe", "Jane", "Doe", "Acme", email="jane@acme.com", pk="r2"),
    ]
    import_records(conn, _FakeLoader(recs), "x")
    assert Repository(conn).stats()["contacts"] == 2


def test_idempotent_reimport(conn):
    recs = [_person("john smith", "John", "Smith", "Acme", email="js@acme.com", pk="r1")]
    import_records(conn, _FakeLoader(recs), "x")
    import_records(conn, _FakeLoader(recs), "x")  # second pass is a no-op
    s = Repository(conn).stats()
    assert s["contacts"] == 1
    assert s["source_records"] == 1


def test_fts_search(conn):
    recs = [_person("eric vaden", "Eric", "Vaden", "Vaden Drywall",
                    email="e@vaden.com", pk="r1")]
    import_records(conn, _FakeLoader(recs), "x")
    repo = Repository(conn)
    hits = repo.search("vaden dry")
    assert any("Vaden" in (h.get("full_name") or h.get("name") or "") for h in hits)


def test_prune_by_state(conn):
    recs = [
        _person("a tx", "A", "Tx", "TX Co", email="a@tx.com", state="TX", pk="r1"),
        _person("b ca", "B", "Ca", "CA Co", email="b@ca.com", state="CA", pk="r2"),
    ]
    import_records(conn, _FakeLoader(recs), "x")
    repo = Repository(conn)
    summary = repo.prune_by_state("tips", ["TX", "OK"])
    conn.commit()
    assert summary["orgs_removed"] == 1
    assert repo.stats()["contacts"] == 1  # CA tombstoned


def test_sync_high_water(conn):
    recs = [_person("john smith", "John", "Smith", "Acme", email="js@acme.com", pk="r1")]
    import_records(conn, _FakeLoader(recs), "x")
    eng = SyncEngine(conn, "jobtread")
    plan = eng.plan("push")
    assert plan and plan[0]["op"] == "create"
    cid = plan[0]["entity_id"]
    eng.record_result(cid, "JT-123", plan[0]["payload_hash"])
    assert eng.plan("push") == []  # nothing pending after recording


def test_reconcile_delta_on_pg(conn):
    rr = RemoteRecord(external_id="JT1", payload={
        "firstName": "Eric", "lastName": "Vaden",
        "company": "Vaden Drywall", "email": "eric@vaden.com"})
    jt = Reconciler(conn, "jobtread")
    assert jt.plan([rr])["summary"]["created"] == 1
    jt.apply([rr])
    assert Reconciler(conn, "jobtread").plan([rr])["summary"]["unchanged"] == 1
    # echo guard + fan-out hold on Postgres too
    assert SyncEngine(conn, "jobtread").plan("push") == []
    assert SyncEngine(conn, "quickbooks").plan("push")[0]["op"] == "create"


def test_grade_on_pg(conn):
    from ntxp_contacts.qualify import Grader
    Reconciler(conn, "lightfield").apply([RemoteRecord(
        external_id="LF1",
        payload={"first_name": "Eric", "last_name": "Vaden",
                 "company": "Vaden Drywall", "email": "eric@vaden.com"})])
    cid = conn.execute(
        "SELECT contact_id FROM contacts WHERE is_deleted=0 LIMIT 1").fetchone()["contact_id"]
    assert Grader(conn).run()["graded"] == 1
    g = Grader(conn).get_grade(cid)
    assert g["is_exposed"] == 1 and g["sources"] == 1
    # outdated gate on Postgres (timestamptz freshest_at)
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00+00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()
    assert Grader(conn).get_grade(cid)["is_exposed"] == 0
