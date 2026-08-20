"""End-to-end tests for the NTXP API Log core: crypto, repository, MCP tools."""
from __future__ import annotations

import json

import pytest

from ntxp_apilog.crypto import Cipher, is_encrypted, mask
from ntxp_apilog.db import connect, migrate
from ntxp_apilog.db.repository import Repository
from ntxp_apilog.model import ApiEntry, UsageEvent


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    # Isolate DB and encryption key per test.
    monkeypatch.setenv("NTXP_APILOG_KEY_PATH", str(tmp_path / "apilog.key"))
    monkeypatch.delenv("NTXP_APILOG_KEY", raising=False)
    conn = connect(str(tmp_path / "apilog.db"))
    migrate(conn)
    return Repository(conn)


def _openai() -> ApiEntry:
    return ApiEntry(
        name="OpenAI", provider="OpenAI, Inc.", category="llm",
        base_url="https://api.openai.com/v1", auth_type="bearer",
        api_key="sk-secret-123456", key_number="proj_abc",
        login_user="ops@ntxp.com", login_secret="hunter2",
        cost_model="$0.01 / 1K tokens", monthly_budget=200.0, tags=["prod", "llm"],
        purpose="LLM completions",
    )


def test_crypto_roundtrip_and_mask():
    c = Cipher()
    token = c.encrypt("sk-secret-123456")
    assert is_encrypted(token)
    assert "secret" not in token  # not stored in cleartext
    assert c.decrypt(token) == "sk-secret-123456"
    assert c.decrypt("legacy-plaintext") == "legacy-plaintext"  # back-compat
    assert mask("sk-secret-123456").endswith("3456")
    assert mask("sk-secret-123456").count("•") > 0


def test_upsert_get_and_secret_encryption(repo):
    api_id, is_new = repo.upsert_api(_openai())
    assert is_new and api_id > 0

    # Ciphertext on disk, never plaintext.
    raw = repo.conn.execute(
        "SELECT api_key_enc, login_secret_enc FROM apis WHERE api_id=?", (api_id,)
    ).fetchone()
    assert is_encrypted(raw["api_key_enc"])
    assert "sk-secret-123456" not in raw["api_key_enc"]

    masked = repo.get_api(api_id, reveal=False)
    assert masked["has_api_key"] is True
    assert masked["api_key_masked"].endswith("3456")
    assert "api_key" not in masked            # not revealed
    assert masked["spend_total"] == 0

    revealed = repo.get_api(api_id, reveal=True)
    assert revealed["api_key"] == "sk-secret-123456"
    assert revealed["login_secret"] == "hunter2"


def test_upsert_is_idempotent_and_preserves_secret(repo):
    api_id, _ = repo.upsert_api(_openai())
    # Metadata-only update (no api_key) must not wipe the stored secret.
    again_id, is_new = repo.upsert_api(
        ApiEntry(name="OpenAI", category="llm", status="active", purpose="updated"))
    assert again_id == api_id and is_new is False
    revealed = repo.get_api(api_id, reveal=True)
    assert revealed["api_key"] == "sk-secret-123456"
    assert revealed["purpose"] == "updated"


def test_search_finds_by_purpose_and_tag(repo):
    repo.upsert_api(_openai())
    repo.upsert_api(ApiEntry(name="Stripe", category="payments",
                             purpose="charge invoices", api_key="rk_live_x"))
    assert {r["name"] for r in repo.search("llm")} == {"OpenAI"}
    assert {r["name"] for r in repo.search("invoices")} == {"Stripe"}
    assert {r["name"] for r in repo.search("OpenAI")} == {"OpenAI"}


def test_resolve_by_name_or_id(repo):
    api_id, _ = repo.upsert_api(_openai())
    assert repo.resolve("OpenAI")["api_id"] == api_id
    assert repo.resolve("openai")["api_id"] == api_id      # norm
    assert repo.resolve(api_id)["api_id"] == api_id
    assert repo.resolve("nope") is None


def test_usage_and_stats(repo):
    api_id, _ = repo.upsert_api(_openai())
    repo.log_usage(UsageEvent(api_id=api_id, cost=1.25, units=125000, unit_kind="tokens"))
    repo.log_usage(UsageEvent(api_id=api_id, cost=0.75))
    s = repo.stats()
    assert s["total_apis"] == 1
    assert s["total_spend"] == 2.0
    assert s["spend_by_api"][0] == {"name": "OpenAI", "spend": 2.0}
    assert repo.list_apis()[0]["spend_total"] == 2.0


def test_soft_delete_hides_from_views(repo):
    api_id, _ = repo.upsert_api(_openai())
    repo.delete_api(api_id)
    assert repo.get_api(api_id) is None
    assert repo.list_apis() == []
    assert repo.search("OpenAI") == []
    # Name freed for re-registration after soft delete.
    new_id, is_new = repo.upsert_api(ApiEntry(name="OpenAI"))
    assert is_new and new_id != api_id


def test_access_log_records_reveal(repo):
    api_id, _ = repo.upsert_api(_openai())
    repo.log_access(api_id, action="reveal", accessor="user:alex@ntxp.com",
                    purpose="debug", origin="cli")
    row = repo.conn.execute(
        "SELECT action, accessor FROM access_log WHERE api_id=?", (api_id,)).fetchone()
    assert row["action"] == "reveal" and row["accessor"] == "user:alex@ntxp.com"


def test_mcp_server_builds(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    monkeypatch.setenv("NTXP_APILOG_KEY_PATH", str(tmp_path / "apilog.key"))
    from ntxp_apilog.mcp_server import build_server
    assert build_server(db_override=str(tmp_path / "apilog.db")) is not None
