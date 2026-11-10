"""F2a — one-way iOS sync: vCard rendering + read-only CardDAV."""
import xml.etree.ElementTree as ET

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.db.repository import Repository
from ntxp_contacts.qualify import Grader
from ntxp_contacts.remote import carddav
from ntxp_contacts.remote.vcard import (contact_vcard, exposed_contact_ids,
                                        export_vcards, render_one)
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


# -- vCard -------------------------------------------------------------------

def test_vcard_fields(conn):
    vc = render_one(conn, _cid(conn))
    assert "BEGIN:VCARD" in vc and "VERSION:3.0" in vc
    assert "FN:Eric Vaden" in vc
    assert "ORG:Vaden Drywall" in vc
    assert "EMAIL;TYPE=INTERNET,PREF:eric@vaden.com" in vc
    assert "TEL;TYPE=WORK:+18178478822" in vc


def test_export_excludes_held_back(conn):
    cid = _cid(conn)
    assert cid in exposed_contact_ids(conn)
    # age it out -> not exposed -> dropped from the feed
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()
    assert cid not in exposed_contact_ids(conn)
    assert "BEGIN:VCARD" not in export_vcards(conn)


# -- CardDAV handlers --------------------------------------------------------

def test_options_advertises_addressbook(conn):
    status, headers, _ = carddav.handle(conn, "OPTIONS", "/carddav/", "", "0")
    assert status == 200
    assert any(k == b"dav" and b"addressbook" in v for k, v in headers)


def test_propfind_principal_and_collection(conn):
    s, _, body = carddav.handle(conn, "PROPFIND", "/carddav/", "", "0")
    assert s == 207 and b"current-user-principal" in body
    ET.fromstring(body)  # well-formed

    cid = _cid(conn)
    s, _, body = carddav.handle(conn, "PROPFIND", carddav.COLLECTION, "", "1")
    assert s == 207
    ET.fromstring(body)
    assert f"ntxp-{cid}.vcf".encode() in body
    assert b"addressbook" in body


def test_report_returns_vcards(conn):
    s, _, body = carddav.handle(conn, "REPORT", carddav.COLLECTION, "", "1")
    assert s == 207
    ET.fromstring(body)
    assert b"address-data" in body and b"Eric Vaden" in body


def test_get_item_returns_vcard(conn):
    cid = _cid(conn)
    s, headers, body = carddav.handle(conn, "GET", f"{carddav.COLLECTION}ntxp-{cid}.vcf", "", "0")
    assert s == 200
    assert any(k == b"content-type" and b"text/vcard" in v for k, v in headers)
    assert body.startswith(b"BEGIN:VCARD")


def test_cid_from_path():
    assert carddav._cid_from_path("/carddav/addressbooks/ntxp/ntxp-42.vcf") == 42
    assert carddav._cid_from_path("/carddav/addressbooks/ntxp/") is None


def test_held_back_contact_not_served_directly(conn):
    cid = _cid(conn)
    conn.execute("UPDATE source_records SET last_seen_at='2016-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    Grader(conn).run()  # -> not exposed
    # direct GET of the guessed .vcf must 404
    s, _, _ = carddav.handle(conn, "GET", f"{carddav.COLLECTION}ntxp-{cid}.vcf", "", "0")
    assert s == 404
    # multiget with an explicit href must not return the held-back vCard
    body = f"<multiget><d:href>{carddav.COLLECTION}ntxp-{cid}.vcf</d:href></multiget>"
    s, _, rbody = carddav.handle(conn, "REPORT", carddav.COLLECTION, body, "1")
    assert b"address-data" not in rbody


def test_validators_change_on_edit(conn):
    import re
    from ntxp_contacts.model import Email
    cid = _cid(conn)
    conn.execute("UPDATE contacts SET updated_at='2020-01-01 00:00:00' WHERE contact_id=?", (cid,))
    conn.commit()
    _, _, b1 = carddav.handle(conn, "PROPFIND", carddav.COLLECTION, "", "1")
    ctag1 = re.search(rb"getctag[^>]*>([^<]+)<", b1).group(1)
    etag1 = re.search(rb"getetag>([^<]+)<", b1).group(1)
    # an edit (new email) must advance both validators
    Repository(conn).add_email(Email(email="eric2@vaden.com", email_norm="eric2@vaden.com"), cid, None)
    conn.commit()
    _, _, b2 = carddav.handle(conn, "PROPFIND", carddav.COLLECTION, "", "1")
    ctag2 = re.search(rb"getctag[^>]*>([^<]+)<", b2).group(1)
    etag2 = re.search(rb"getetag>([^<]+)<", b2).group(1)
    assert ctag1 != ctag2 and etag1 != etag2
