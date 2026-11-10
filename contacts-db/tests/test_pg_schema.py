"""Shared-Supabase safety: a dedicated schema keeps this app's migrations and RLS
lockdown away from other apps' tables, and works behind a transaction pooler."""
import os

import pytest

PG_URL = os.environ.get("NTXP_TEST_PG_URL")
pytestmark = pytest.mark.skipif(not PG_URL, reason="NTXP_TEST_PG_URL not set")
psycopg = pytest.importorskip("psycopg")

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.db.pg import pg_schema


@pytest.fixture
def shared_db(monkeypatch):
    """A 'shared' database: another app's table lives in public with grants to anon."""
    with psycopg.connect(PG_URL, autocommit=True) as c:
        c.execute("DROP SCHEMA IF EXISTS ntxp_t CASCADE")
        c.execute("DROP SCHEMA public CASCADE")
        c.execute("CREATE SCHEMA public")
        c.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') "
                  "THEN CREATE ROLE anon NOLOGIN; END IF; END $$")
        c.execute("GRANT USAGE ON SCHEMA public TO anon")
        c.execute("CREATE TABLE public.other_app_data (id int, v text)")
        c.execute("GRANT SELECT ON public.other_app_data TO anon")
    monkeypatch.setenv("NTXP_PG_SCHEMA", "ntxp_t")
    yield
    with psycopg.connect(PG_URL, autocommit=True) as c:
        c.execute("DROP SCHEMA IF EXISTS ntxp_t CASCADE")


def test_migrations_and_lockdown_stay_in_their_schema(shared_db):
    c = connect(PG_URL)
    migrate(c)
    mine = {r[0] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='ntxp_t'").fetchall()}
    assert {"contacts", "organizations", "council_answers", "schema_version"} <= mine
    # nothing of ours leaked into public...
    pub = {r[0] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()}
    assert pub == {"other_app_data"}
    # ...our tables are locked down...
    rls = {r[0]: r[1] for r in c.execute(
        "SELECT relname, relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='ntxp_t' AND relkind='r'").fetchall()}
    assert rls and all(rls.values())
    # ...and the OTHER app's table is untouched: RLS still off, anon's grant intact.
    other = c.execute("SELECT relrowsecurity FROM pg_class WHERE relname='other_app_data'").fetchone()[0]
    assert other is False
    priv = c.execute("SELECT has_table_privilege('anon','public.other_app_data','SELECT')").fetchone()[0]
    assert priv is True
    anon_mine = c.execute("SELECT has_table_privilege('anon','ntxp_t.contacts','SELECT')").fetchone()[0]
    assert anon_mine is False
    c.close()


def test_search_path_is_primed_every_transaction(shared_db):
    """Behind a transaction-mode pooler session SET is lost between transactions; the
    facade must re-prime each transaction (SET LOCAL)."""
    c = connect(PG_URL)
    migrate(c)
    assert c.execute("SELECT current_schema()").fetchone()[0] == "ntxp_t"
    c.commit()
    # a raw statement after commit shows the un-primed session default...
    assert c._raw.execute("SELECT current_schema()").fetchone()[0] == "public"
    c._raw.rollback()
    c._fresh = True
    # ...while the facade primes the new transaction again
    assert c.execute("SELECT current_schema()").fetchone()[0] == "ntxp_t"
    c.commit()
    c.close()


def test_schema_name_is_validated(monkeypatch):
    monkeypatch.setenv("NTXP_PG_SCHEMA", 'x"; DROP SCHEMA public; --')
    with pytest.raises(ValueError):
        pg_schema()
    monkeypatch.setenv("NTXP_PG_SCHEMA", "NTXP_Contacts")
    assert pg_schema() == "ntxp_contacts"
    monkeypatch.delenv("NTXP_PG_SCHEMA")
    assert pg_schema() is None
