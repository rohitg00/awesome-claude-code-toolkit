import sqlite3

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.db.repository import Repository
from ntxp_contacts.loaders.base import import_records
from ntxp_contacts.model import CanonicalRecord, Email, Phone, Tag


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


class _FakeLoader:
    """In-memory loader emitting pre-built rows for deterministic tests."""
    source = "tips"

    def __init__(self, records):
        self._records = records

    def rows(self, path):
        yield from range(len(self._records))

    def to_canonical(self, i):
        return self._records[i]


def _person(name_norm, first, last, org, email=None, phone=None, source="tips", pk=None):
    rec = CanonicalRecord(source=source, source_pk=pk or name_norm)
    rec.org_name = org
    rec.org_name_norm = org.lower() if org else None
    rec.first_name, rec.last_name, rec.full_name = first, last, f"{first} {last}"
    rec.name_norm = name_norm
    if email:
        rec.emails.append(Email(email=email, email_norm=email, is_primary=True))
    if phone:
        rec.phones.append(Phone(phone_raw=phone, phone_e164=phone))
    rec.tags.append(Tag("source", source))
    return rec


def test_email_dedup_merges(conn):
    recs = [
        _person("john smith", "John", "Smith", "Acme", email="js@acme.com", pk="r1"),
        _person("j smith", "J", "Smith", "Acme", email="js@acme.com", pk="r2"),
    ]
    import_records(conn, _FakeLoader(recs), "x")
    repo = Repository(conn)
    assert repo.stats()["contacts"] == 1  # same email -> merged


def test_distinct_people_not_merged(conn):
    recs = [
        _person("john smith", "John", "Smith", "Acme", email="john@acme.com", pk="r1"),
        _person("jane doe", "Jane", "Doe", "Acme", email="jane@acme.com", pk="r2"),
    ]
    import_records(conn, _FakeLoader(recs), "x")
    assert Repository(conn).stats()["contacts"] == 2


def test_idempotent_reimport(conn):
    recs = [
        _person("john smith", "John", "Smith", "Acme", email="js@acme.com", pk="r1"),
        _person("jane doe", "Jane", "Doe", "Beta", email="jane@beta.com", pk="r2"),
    ]
    s1 = import_records(conn, _FakeLoader(recs), "x")
    before = Repository(conn).stats()
    s2 = import_records(conn, _FakeLoader(recs), "x")
    after = Repository(conn).stats()
    assert s2.skipped_unchanged == 2
    assert before["contacts"] == after["contacts"]
    assert before["source_records"] == after["source_records"]


def test_invalid_email_does_not_fuse(conn):
    r1 = _person("a one", "A", "One", "Org1", pk="r1")
    r1.emails.append(Email(email="junk@x.com", email_norm="junk@x.com", is_invalid=True))
    r2 = _person("b two", "B", "Two", "Org2", pk="r2")
    r2.emails.append(Email(email="junk@x.com", email_norm="junk@x.com", is_invalid=True))
    import_records(conn, _FakeLoader([r1, r2]), "x")
    assert Repository(conn).stats()["contacts"] == 2


def test_prune_by_state(conn):
    from ntxp_contacts.model import Address
    def org_in(name_norm, state, source, pk):
        r = _person(f"c {name_norm}", "C", name_norm, name_norm, source=source, pk=pk)
        a = Address(state=state, addr_norm=f"{name_norm} {state}".lower())
        r.org_addresses.append(a)
        return r
    tips = _FakeLoader([
        org_in("alpha", "TX", "tips", "t1"),
        org_in("bravo", "OK", "tips", "t2"),
        org_in("charlie", "CA", "tips", "t3"),
        org_in("delta", "NY", "tips", "t4"),
    ])
    # provenance comes from loader.source, so the non-tips record needs its own loader
    other = _FakeLoader([org_in("echo", "CA", "buildingconnectd", "b1")])
    other.source = "buildingconnectd"
    import_records(conn, tips, "x")
    import_records(conn, other, "x")
    repo = Repository(conn)
    before = repo.stats()["contacts"]
    summary = repo.prune_by_state("tips", ["TX", "OK"])
    conn.commit()
    assert summary["orgs_removed"] == 2          # charlie, delta
    assert summary["orgs_kept"] == 2             # alpha, bravo
    after = repo.stats()
    assert after["contacts"] == before - 2       # the 2 CA/NY tips contacts gone
    # the non-tips CA org/contact is untouched
    assert repo.search("echo")


def test_fts_search(conn):
    import_records(conn, _FakeLoader([
        _person("eric vaden", "Eric", "Vaden", "Vadens Drywall", email="e@v.com", pk="r1"),
    ]), "x")
    results = Repository(conn).search("Vaden")
    assert any("vaden" in (r.get("full_name") or "").lower() for r in results)
