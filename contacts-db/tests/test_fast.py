import csv

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.db.repository import Repository

duckdb = pytest.importorskip("duckdb")
from ntxp_contacts.fast import fast_import, auto_map  # noqa: E402


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def _csv(tmp_path, rows, header):
    p = tmp_path / "src.csv"
    with open(p, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return str(p)


def test_fast_import_tips(conn, tmp_path):
    header = ["MemberID", "Member", "Address1", "City", "State", "ZIP",
              "Membership Date", "Contact", "Contact_Title", "Phone", "Fax",
              "Region", "Contact Type"]
    rows = [
        ["696372.0", "Acme Inc", "1 Main", "Dallas", "TX", "7013", "", "John Smith", "Dir", "(214) 555-1212", "", "10a", "P"],
        ["696372.0", "Acme Inc", "1 Main", "Dallas", "TX", "7013", "", "Jane Doe", "VP", "(214) 555-3434", "", "10a", "A"],
        ["57820.0", "Beta LLC", "2 Oak", "Tulsa", "OK", "74101", "", "Bob Lee", "Mgr", "(918) 555-7777", "", "11b", "P"],
    ]
    path = _csv(tmp_path, rows, header)
    s = fast_import(conn, "tips", path)
    st = Repository(conn).stats()
    assert s.rows == 3
    assert st["organizations"] == 2          # Acme, Beta
    assert st["contacts"] == 3               # three distinct people
    # normalization: phone E.164, ZIP repaired
    row = conn.execute("SELECT phone_e164 FROM phones WHERE phone_e164 LIKE '+1214%' LIMIT 1").fetchone()
    assert row and row[0] == "+12145551212"
    z = conn.execute("SELECT zip FROM addresses WHERE zip='07013'").fetchone()
    assert z is not None                     # 7013 -> 07013


def test_fast_import_idempotent(conn, tmp_path):
    header = ["Company", "First Name", "Last Name", "Email", "Phone"]
    rows = [["Vaden Drywall", "Eric", "Vaden", "eric@vadens.com", "817-847-8822"]]
    path = _csv(tmp_path, rows, header)
    fast_import(conn, "buildingconnectd", path)
    before = Repository(conn).stats()
    s2 = fast_import(conn, "buildingconnectd", path)
    after = Repository(conn).stats()
    assert s2.skipped_unchanged == 1
    assert before["contacts"] == after["contacts"]
    assert before["source_records"] == after["source_records"]


def test_auto_map_unknown_source(conn, tmp_path):
    header = ["Organization Name", "Full Name", "Email Address", "Cell Phone", "State"]
    rows = [["Globex Corporation", "Hank Scorpio", "hank@globex.com", "(555) 010-2020", "NM"]]
    path = _csv(tmp_path, rows, header)
    m = auto_map("globex", header)
    assert m.org_name == "Organization Name"
    assert m.email == "Email Address"
    s = fast_import(conn, "globex", path, mapping=m)
    assert s.rows == 1
    assert Repository(conn).search("Scorpio")
