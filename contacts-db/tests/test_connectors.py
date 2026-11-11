"""F2c — whitelisted connector middle-layer."""
import pytest

from ntxp_contacts.connectors import ingest_contacts, is_allowed, map_contact
from ntxp_contacts.db import connect, migrate
from ntxp_contacts.db.repository import Repository


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def test_map_contact_aliases():
    rec = map_contact("hubspot", {
        "DisplayName": "Eric Vaden", "emailAddress": "eric@vaden.com",
        "organization": "Vaden Drywall", "jobTitle": "Owner", "mobile": "817-847-8822"})
    assert rec.first_name == "Eric" and rec.last_name == "Vaden"
    assert rec.org_name == "Vaden Drywall" and rec.title == "Owner"
    assert rec.emails[0].email_norm == "eric@vaden.com"
    assert rec.phones[0].phone_e164 == "+18178478822"
    assert rec.source == "connector:hubspot"


def test_allowlist():
    assert is_allowed("google") and is_allowed("HubSpot")
    assert not is_allowed("evilcorp")


def test_ingest_allowed(conn):
    out = ingest_contacts(conn, "google", [
        {"name": "Eric Vaden", "email": "eric@vaden.com", "company": "Vaden Drywall"},
        {"name": "Juan Villalpando", "email": "juan@jhl.com", "company": "JHL Painting"}])
    assert out["service"] == "google" and out["new"] == 2
    assert Repository(conn).stats()["contacts"] == 2


def test_ingest_disallowed_raises(conn):
    with pytest.raises(PermissionError):
        ingest_contacts(conn, "evilcorp", [{"email": "x@y.com", "name": "X Y"}])


def test_allowlist_env_override(monkeypatch):
    monkeypatch.setenv("NTXP_CONNECTOR_ALLOWLIST", "foo,bar")
    assert is_allowed("foo") and not is_allowed("google")
