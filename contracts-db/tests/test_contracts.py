"""Tests for the NTXP Master Contracts core: idempotency, field-level saves,
optimistic-lock conflicts, jobs roll-up, importer, branding, contact files."""
import csv
import json
import os
from pathlib import Path

import pytest

from ntxp_contracts import branding, contactfile
from ntxp_contracts.db import connect, migrate
from ntxp_contracts.db.repository import ConflictError, Repository
from ntxp_contracts.importer import import_csv
from ntxp_contracts.jobs import sync_jobs
from ntxp_contracts.model import Contract, Job, OwnerEntity


@pytest.fixture()
def repo(tmp_path):
    db = tmp_path / "contracts.db"
    conn = connect(db)
    migrate(conn)
    return Repository(conn)


def test_migrate_and_stats(repo):
    s = repo.stats()
    assert s["contracts"] == 0 and s["unexecuted"] == 0


def test_upsert_is_idempotent_on_number(repo):
    c = Contract(contract_title="JOC A", contract_no="RFP-2024-001",
                 contract_type="Job Order Contract", owner_entity="City of Dallas")
    cid1, new1 = repo.upsert_contract(c)
    cid2, new2 = repo.upsert_contract(Contract(
        contract_title="JOC A", contract_no="rfp 2024 001"))  # same number, messy
    assert new1 is True and new2 is False and cid1 == cid2
    assert repo.stats()["contracts"] == 1


def test_recipient_defaults_to_ntxp(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    assert repo.get_contract(cid)["recipient"] == "NTXP LLC"


def test_update_field_bumps_rev_and_logs(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X", contract_no="N1"))
    before = repo.get_contract(cid)["rev"]
    repo.update_field(cid, "coefficient_multiplier", "1.05")
    after = repo.get_contract(cid)
    assert after["coefficient_multiplier"] == 1.05
    assert after["rev"] == before + 1
    n = repo.conn.execute(
        "SELECT COUNT(*) n FROM change_log WHERE contract_id=? AND field='coefficient_multiplier'",
        (cid,)).fetchone()["n"]
    assert n == 1


def test_money_and_date_coercion(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    repo.update_field(cid, "estimated_budget", "$1,250,000")
    repo.update_field(cid, "expiration_date", "12/31/2026")
    c = repo.get_contract(cid)
    assert c["estimated_budget"] == 1_250_000.0
    assert c["expiration_date"] == "2026-12-31"


def test_executed_flag_toggle(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    assert repo.get_contract(cid)["is_executed"] is False
    repo.update_field(cid, "is_executed", True)
    assert repo.get_contract(cid)["is_executed"] is True


def test_rejects_non_editable_field(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    with pytest.raises(ValueError):
        repo.update_field(cid, "contract_id", 99)


def test_clearing_not_null_field_rejected_not_crashed(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    # recipient is NOT NULL — clearing it must raise ValueError (-> 400),
    # never an uncaught IntegrityError (-> 500).
    with pytest.raises(ValueError):
        repo.update_field(cid, "recipient", "")
    # the row is untouched
    assert repo.get_contract(cid)["recipient"] == "NTXP LLC"


def test_blank_nullable_field_coerced_to_none(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    repo.update_field(cid, "location", "Dallas")
    repo.update_field(cid, "location", "   ")   # whitespace-only clears it
    assert repo.get_contract(cid)["location"] is None


def test_yearless_date_not_misparsed():
    from ntxp_contracts import normalize as N
    # "12/31" must not silently become 1900-12-31
    assert N.normalize_date("12/31") is None
    assert N.normalize_date("12/31/2026") == "2026-12-31"


def test_jobs_attrs_excludes_mixed_case_aliases(repo):
    repo.upsert_contract(Contract(contract_title="J", contract_no="J-1"))
    repo.conn.commit()
    sync_jobs(repo, [{"Contract": "J-1", "Name": "Roof", "Sales": "1000",
                      "Region": "North"}])
    cid = repo.get_contract_by_no("J-1")["contract_id"]
    job = repo.list_jobs(cid)[0]
    assert job["name"] == "Roof"
    # capitalized consumed headers must not be duplicated into attrs
    assert "Name" not in job["attrs"] and "Sales" not in job["attrs"]
    assert job["attrs"].get("Region") == "North"   # genuine extra is kept


def test_optimistic_lock_conflict(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    rev = repo.get_contract(cid)["rev"]
    repo.update_field(cid, "notes", "first")            # rev advances
    with pytest.raises(ConflictError):
        repo.update_field(cid, "notes", "stale", expected_rev=rev)


def test_concurrent_different_fields_no_conflict(repo):
    cid, _ = repo.upsert_contract(Contract(contract_title="X"))
    rev = repo.get_contract(cid)["rev"]
    # Two editors hold the same starting rev but touch different fields.
    repo.update_field(cid, "location", "Dallas", expected_rev=rev)
    # second editor's rev is now stale for *that* field path, but field-level
    # editing means UIs send per-field PATCHes; without expected_rev it's LWW:
    repo.update_field(cid, "duration", "1 year")
    c = repo.get_contract(cid)
    assert c["location"] == "Dallas" and c["duration"] == "1 year"


def test_owner_entity_links_and_profile(repo):
    cid, _ = repo.upsert_contract(Contract(
        contract_title="JOC", contract_no="N5", owner_entity="TIPS USA"))
    repo.conn.commit()
    oid = repo.get_owner_by_name("TIPS USA")["owner_id"]
    repo.upsert_owner(OwnerEntity(name="TIPS USA", website="tips-usa.com",
                                  customer_service_phone="817-462-7872",
                                  accounting_phone="(817) 555-1212"))
    prof = repo.get_profile(cid)
    assert prof["owner"]["owner_id"] == oid
    assert prof["owner"]["website"] == "https://tips-usa.com"
    assert prof["owner"]["customer_service_phone"] == "+18174627872"


def test_jobs_sync_and_totals(repo):
    repo.upsert_contract(Contract(contract_title="JOC", contract_no="JOC-9"))
    repo.conn.commit()
    rows = [
        {"contract": "JOC-9", "name": "Gym reroof", "customer": "ISD",
         "sales_amount": "$120,000", "contract_value": "150000", "id": "j1"},
        {"contract": "JOC-9", "name": "HVAC", "sales": "80000", "id": "j2"},
    ]
    summary = sync_jobs(repo, rows)
    assert summary["upserted"] == 2
    cid = repo.get_contract_by_no("JOC-9")["contract_id"]
    prof = repo.get_profile(cid)
    assert prof["totals"]["job_count"] == 2
    assert prof["totals"]["total_sales"] == 200_000.0
    # re-sync is idempotent on external_id
    sync_jobs(repo, rows)
    assert repo.get_profile(cid)["totals"]["job_count"] == 2


def test_search(repo):
    repo.upsert_contract(Contract(contract_title="Electrical JOC", contract_no="E1",
                                  allowable_scope="Electrical, Trade Work"))
    repo.conn.commit()
    assert any("Electrical" in c["contract_title"] for c in repo.search("electric"))


def test_importer_idempotent(tmp_path, repo):
    p = tmp_path / "log.csv"
    with p.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Contract Title", "Contract / RFP #", "Type of Contract",
                    "Coefficient", "Cooperative Fee", "Expiration Date", "Executed"])
        w.writerow(["Job Order A", "RFP-1", "Job Order Contract", "1.10", "2%",
                    "12/31/2027", "yes"])
        w.writerow(["Co-op B", "COOP-2", "Cooperative Contract", "0.98", "1.5%",
                    "06/30/2026", "no"])
    s1 = import_csv(repo, p)
    s2 = import_csv(repo, p)
    assert s1["created"] == 2
    assert s2["created"] == 0 and s2["skipped"] == 2
    c = repo.get_contract_by_no("RFP-1")
    assert c["coefficient_multiplier"] == 1.10 and c["is_executed"] is True
    assert c["expiration_date"] == "2027-12-31"


def test_contactfile_vcard_and_ics():
    owner = {"name": "City of Dallas", "main_phone": "+12145551234",
             "customer_service_phone": "+12145555678", "website": "https://dallas.gov"}
    vc = contactfile.vcard(owner)
    assert "BEGIN:VCARD" in vc and "City of Dallas" in vc and "+12145551234" in vc
    ics = contactfile.ics_expiration({"contract_id": 1, "contract_title": "JOC",
                                      "contract_no": "N1", "expiration_date": "2026-12-31"})
    assert "BEGIN:VCALENDAR" in ics and "DTSTART;VALUE=DATE:20261231" in ics
    assert contactfile.ics_expiration({"expiration_date": None}) is None


def test_branding_fallback(monkeypatch, tmp_path):
    # Point all search roots at an empty dir => documented NTXP defaults.
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    b = branding.resolve_brand()
    assert b.colors["primary"] and b.fonts["heading"]


def test_branding_parses_skill(monkeypatch, tmp_path):
    sk = tmp_path / "skills" / "ntxp-brand"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        "---\nname: ntxp-brand\ndescription: NTXP brand colors\n---\n"
        "# NTXP Brand\n- Primary: `#123456` - brand navy\n"
        "- Accent: `#ABCDEF` - orange\n- Headings: Montserrat\n- Body text: Inter\n")
    monkeypatch.setenv("NTXP_BRANDING_PATH", str(tmp_path / "skills"))
    b = branding.resolve_brand()
    assert b.colors["primary"] == "#123456"
    assert b.colors["accent"] == "#ABCDEF"
    assert b.fonts["heading"].startswith("Montserrat")
    assert "ntxp-brand" in (b.skill_path or "")
