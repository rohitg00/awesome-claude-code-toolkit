"""Layer E — Google Workspace sweep collectors."""
import pytest

from ntxp_contacts.collect import (extract_calendar_event, extract_drive_doc,
                                    extract_gmail, extract_google_contact, sweep)
from ntxp_contacts.db import connect, migrate
from ntxp_contacts.db.repository import Repository
from ntxp_contacts.qualify import Grader


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


# -- extractors --------------------------------------------------------------

def test_gmail_signature_and_recipients():
    recs = extract_gmail({
        "from": "Eric Vaden <Eric@Vaden.com>",
        "to": ["juan@jhl.com", "Greg Smith <greg@jamailsmith.com>"],
        "date": "2026-02-01",
        "signature": {"name": "Eric Vaden", "phone": "817-847-8822",
                      "title": "Owner", "company": "Vaden Drywall"},
    })
    sender = [r for r in recs if r.source == "gmail_signature"][0]
    assert sender.emails[0].email_norm == "eric@vaden.com"
    assert sender.phones[0].phone_e164 == "+18178478822"
    assert sender.title == "Owner" and sender.org_name == "Vaden Drywall"
    # company-domain auto-group tag
    assert any(t.kind == "domain" and t.value == "vaden.com" for t in sender.tags)
    tos = [r for r in recs if r.source == "gmail_to"]
    assert len(tos) == 2


def test_freemail_not_domain_grouped():
    recs = extract_gmail({"from": "Jane Doe <jane@gmail.com>"})
    assert not any(t.kind == "domain" for t in recs[0].tags)


def test_google_contact_and_calendar_and_drive():
    gc = extract_google_contact({
        "names": [{"displayName": "Sherri Snowden", "givenName": "Sherri", "familyName": "Snowden"}],
        "emailAddresses": [{"value": "sherri@warden.com"}],
        "phoneNumbers": [{"value": "(817) 555-0125"}],
        "organizations": [{"name": "Warden Construction", "title": "PM"}]})[0]
    assert gc.source == "gcontacts" and gc.org_name == "Warden Construction"
    assert gc.phones[0].phone_e164 == "+18175550125"

    ev = extract_calendar_event({
        "organizer": {"email": "owner@friscotexas.gov", "displayName": "Erik Erwin"},
        "attendees": [{"email": "sub@vaden.com", "displayName": "Eric Vaden"},
                      {"resource": True, "email": "room@x.com"}],
        "start": {"dateTime": "2026-03-04T10:00:00Z"}})
    assert {r.source for r in ev} == {"calendar_organizer", "calendar_attendee"}

    dv = extract_drive_doc({
        "name": "Spec.pdf", "modifiedTime": "2026-01-01T00:00:00Z",
        "owners": [{"displayName": "Dana Owner", "emailAddress": "dana@ntxpllc.com"}],
        "lastModifyingUser": {"displayName": "Dana Owner", "emailAddress": "dana@ntxpllc.com"}})
    assert len(dv) == 1 and dv[0].source == "drive_author"  # deduped


# -- end to end --------------------------------------------------------------

def test_sweep_ingest_dedup(conn):
    bundle = {"gcontacts": [{
        "names": [{"displayName": "Eric Vaden"}],
        "emailAddresses": [{"value": "eric@vaden.com"}],
        "organizations": [{"name": "Vaden Drywall"}]}]}
    r1 = sweep(conn, bundle)
    assert r1["new"] == 1
    r2 = sweep(conn, bundle)          # idempotent
    assert r2["skipped"] == 1 and r2["new"] == 0
    assert Repository(conn).stats()["contacts"] == 1


def test_resweep_preserves_data_point_age(conn):
    # An old event, swept twice, must stay held back — the re-sweep's touch must
    # not refresh last_seen to now.
    bundle = {"calendar": [{
        "organizer": {"email": "old@acme.com", "displayName": "Old Contact"},
        "start": {"dateTime": "2017-05-05T10:00:00Z"}}]}
    sweep(conn, bundle)
    Grader(conn).run()
    cid = conn.execute("SELECT contact_id FROM contacts WHERE is_deleted=0 LIMIT 1").fetchone()["contact_id"]
    assert Grader(conn).get_grade(cid)["is_exposed"] == 0
    r = sweep(conn, bundle)              # re-sweep hits the idempotent skip path
    assert r["skipped"] == 1
    Grader(conn).run()
    assert Grader(conn).get_grade(cid)["is_exposed"] == 0   # still aged out


def test_data_point_age_gates_exposure(conn):
    # A years-old calendar event must grade as outdated, not fresh-because-swept.
    sweep(conn, {"calendar": [{
        "organizer": {"email": "old@acme.com", "displayName": "Old Contact"},
        "start": {"dateTime": "2017-05-05T10:00:00Z"}}]})
    Grader(conn).run()
    cid = conn.execute("SELECT contact_id FROM contacts WHERE is_deleted=0 LIMIT 1").fetchone()["contact_id"]
    g = Grader(conn).get_grade(cid)
    assert g["is_exposed"] == 0  # aged out by its own event date
