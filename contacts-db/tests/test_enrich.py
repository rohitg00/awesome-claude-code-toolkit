"""Layers G/H/I — enrichment framework, photo resolver, LinkedIn cross-reference."""
import hashlib

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.enrich import (confirm, confirm_linkedin, detect_missing,
                                  generate, list_candidates)
from ntxp_contacts.enrich.base import Candidate, RESOLVERS
from ntxp_contacts.enrich.grade import grade_candidates
from ntxp_contacts.sync.base import RemoteRecord
from ntxp_contacts.sync.reconcile import Reconciler


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.db")
    migrate(c)
    return c


def _seed(conn, email="eric@vaden.com", company="Vaden Drywall"):
    Reconciler(conn, "lightfield").apply([RemoteRecord(
        external_id="LF1", payload={"first_name": "Eric", "last_name": "Vaden",
                                     "company": company, "email": email})])
    return conn.execute("SELECT contact_id FROM contacts WHERE is_deleted=0 LIMIT 1").fetchone()["contact_id"]


# -- resolvers + grading (no DB) --------------------------------------------

def test_gravatar_url_is_md5_of_email():
    c = {"emails": [{"email_norm": "eric@vaden.com"}]}
    cands = RESOLVERS["gravatar"].resolve(c)
    h = hashlib.md5(b"eric@vaden.com").hexdigest()
    assert cands[0].field == "photo" and h in cands[0].value


def test_company_website_and_public_directory():
    assert RESOLVERS["company_website"].resolve(
        {"emails": [{"email_norm": "a@vaden.com"}]})[0].value == "https://vaden.com"
    pub = RESOLVERS["public_directory"].resolve(
        {"emails": [{"email_norm": "jane@friscotexas.gov"}], "full_name": "Jane Roe"})
    assert pub and pub[0].source == "public_directory"


def test_linkedin_candidate_is_search_not_scrape():
    c = {"full_name": "Eric Vaden", "org_name": "Vaden Drywall"}
    cand = RESOLVERS["linkedin_candidate"].resolve(c)[0]
    assert cand.field == "linkedin" and "linkedin.com/in" in cand.evidence["query"]


def test_corroboration_boost():
    cands = [Candidate("photo", "X", "gravatar"), Candidate("photo", "X", "libravatar")]
    grade_candidates(cands)
    # same value from two sources -> both boosted above gravatar's base 0.60
    assert all(c.grade > 0.60 for c in cands)


# -- end to end --------------------------------------------------------------

def test_detect_generate_confirm(conn):
    cid = _seed(conn)
    missing = {m["contact_id"]: m["missing"] for m in detect_missing(conn)}
    assert "photo" in missing[cid] and "linkedin" in missing[cid] and "website" in missing[cid]

    summary = generate(conn)
    assert summary["candidates"] > 0
    assert summary["by_field"].get("photo", 0) >= 1

    photo_cands = list_candidates(conn, field="photo", contact_id=cid)
    assert photo_cands
    res = confirm(conn, photo_cands[0]["cand_id"])
    assert res["ok"]
    url = conn.execute("SELECT photo_url FROM contacts WHERE contact_id=?", (cid,)).fetchone()["photo_url"]
    assert url == photo_cands[0]["value"]


def test_confirm_linkedin_sets_field_and_photo(conn):
    cid = _seed(conn)
    out = confirm_linkedin(conn, cid, "https://linkedin.com/in/ericvaden",
                           photo_url="https://media.licdn.com/pic.jpg")
    assert out["ok"] and "linkedin" in out["changed"] and "photo" in out["changed"]
    row = conn.execute("SELECT linkedin_url, photo_url FROM contacts WHERE contact_id=?",
                       (cid,)).fetchone()
    assert row["linkedin_url"].endswith("ericvaden")
    assert row["photo_url"].endswith("pic.jpg")
    # no longer flagged missing linkedin/photo
    missing = {m["contact_id"]: m["missing"] for m in detect_missing(conn)}
    assert "linkedin" not in missing.get(cid, []) and "photo" not in missing.get(cid, [])
