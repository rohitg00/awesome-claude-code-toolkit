"""Fix 5 — an explicit path must never fall through to NTXP_DB_URL."""
from ntxp_contacts.config import backend, db_path, db_url


def test_explicit_path_forces_sqlite_over_db_url(monkeypatch, tmp_path):
    monkeypatch.setenv("NTXP_DB_URL", "postgresql://u@/cloud")
    p = str(tmp_path / "local.db")
    # explicit filesystem path -> SQLite, never the cloud URL
    assert db_url(p) is None
    assert backend(p) == "sqlite"
    assert str(db_path(p)) == p
    # explicit postgres URL override -> postgres
    assert backend("postgresql://u@/other") == "postgres"
    # no override -> env URL wins
    assert backend(None) == "postgres"
    assert db_url(None) == "postgresql://u@/cloud"
