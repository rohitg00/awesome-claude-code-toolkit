"""DuckDB-accelerated bulk importer (the jevt engine pattern).

Reads a source file directly (CSV/TSV/gzip native, XLSX via the excel
extension), normalizes every field in one vectorized SQL pass, de-duplicates
within the file, then writes to the SQLite master in a handful of set-based
statements — instead of tens of thousands of per-row Python operations.

Scope: the deterministic path (exact email / org-name / native-id resolution),
which is the bulk of any import. Fuzzy near-duplicate review remains the job of
the careful `import` path. Idempotent: re-running skips unchanged rows via
`source_records.row_hash`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..db.repository import Repository
from .mapping import SourceMapping, get_mapping
from .sql import MAX_PHONES, build_normalize_sql

# fixed output column order fetched from DuckDB and staged into SQLite
_COLS = (
    "org_name org_name_norm website license_no first_name last_name full_name "
    "name_norm block_key title email_norm email_invalid line1 city state zip "
    "addr_norm region contact_type cert_raw "
    + " ".join(f"p{i}_raw p{i}_e164 p{i}_kind" for i in range(MAX_PHONES))
    + " source_pk row_hash ckey"
).split()


@dataclass
class FastStats:
    source: str
    rows: int = 0
    skipped_unchanged: int = 0
    new_orgs: int = 0
    new_contacts: int = 0
    emails: int = 0
    phones: int = 0
    engine: str = "duckdb"

    def as_dict(self) -> dict:
        return self.__dict__


def _open_relation(duck, path: str) -> str:
    """Return a DuckDB relation expression reading `path` as all-varchar."""
    p = str(path)
    low = p.lower()
    if low.endswith((".xlsx", ".xlsm")):
        duck.execute("INSTALL excel; LOAD excel;")
        return f"read_xlsx('{p}', all_varchar=true)"
    # CSV / TSV / TXT / gzip — auto-detect delimiter (jevt-style)
    return (f"read_csv('{p}', auto_detect=true, all_varchar=true, "
            f"ignore_errors=true, null_padding=true)")


def fast_import(conn, source: str, path: str | Path,
                mapping: SourceMapping | None = None) -> FastStats:
    import duckdb

    duck = duckdb.connect()
    rel = _open_relation(duck, str(path))
    cols = [c[0] for c in duck.execute(f"DESCRIBE SELECT * FROM {rel}").fetchall()]
    m = mapping or get_mapping(source, cols)
    m = m.restrict(cols)   # tolerate files missing some optional columns

    sql = build_normalize_sql(m, rel)
    norm = duck.execute(f"SELECT {', '.join(_COLS)} FROM ({sql})").fetchall()
    duck.close()

    stats = FastStats(source=source, rows=len(norm))
    if not norm:
        return stats

    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS _f")
    cur.execute("CREATE TEMP TABLE _f (" + ", ".join(f"{c} TEXT" for c in _COLS) + ")")
    cur.executemany(
        "INSERT INTO _f VALUES (" + ",".join("?" * len(_COLS)) + ")", norm)
    cur.execute("CREATE INDEX _f_ck ON _f(ckey)")

    # Idempotency: drop rows already recorded unchanged.
    stats.skipped_unchanged = cur.execute(
        "SELECT COUNT(*) FROM _f WHERE (source_pk, row_hash) IN "
        "(SELECT source_pk, row_hash FROM source_records WHERE source = ?)",
        (source,)).fetchone()[0]
    cur.execute(
        "DELETE FROM _f WHERE (source_pk, row_hash) IN "
        "(SELECT source_pk, row_hash FROM source_records WHERE source = ?)", (source,))

    orgs_before = cur.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
    contacts_before = cur.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]

    # 1) new organizations (one per normalized name not already present)
    cur.execute(
        "INSERT INTO organizations(name, name_norm, website, license_no, attrs) "
        "SELECT max(org_name), org_name_norm, max(website), max(license_no), '{}' "
        "FROM _f WHERE org_name_norm IS NOT NULL "
        "AND org_name_norm NOT IN (SELECT name_norm FROM organizations) "
        "GROUP BY org_name_norm")
    cur.execute("DROP TABLE IF EXISTS _om")
    cur.execute("CREATE TEMP TABLE _om AS SELECT org_id, name_norm FROM organizations")
    cur.execute("CREATE INDEX _om_nn ON _om(name_norm)")

    # 2) distinct contacts (by ckey), resolve existing, insert new
    cur.execute(
        "CREATE TEMP TABLE _ck AS SELECT ckey, "
        "max(first_name) first_name, max(last_name) last_name, max(full_name) full_name, "
        "max(name_norm) name_norm, max(block_key) block_key, max(title) title, "
        "max(org_name_norm) org_name_norm, max(email_norm) email_norm "
        "FROM _f WHERE name_norm IS NOT NULL GROUP BY ckey")
    cur.execute("ALTER TABLE _ck ADD COLUMN org_id INTEGER")
    cur.execute("ALTER TABLE _ck ADD COLUMN contact_id INTEGER")
    cur.execute("CREATE INDEX _ck_ck ON _ck(ckey)")
    cur.execute("UPDATE _ck SET org_id=(SELECT org_id FROM _om WHERE name_norm=_ck.org_name_norm)")
    cur.execute(
        "UPDATE _ck SET contact_id=(SELECT e.contact_id FROM emails e JOIN contacts c "
        "ON c.contact_id=e.contact_id WHERE e.email_norm=_ck.email_norm AND e.is_invalid=0 "
        "AND c.is_deleted=0 LIMIT 1) WHERE email_norm IS NOT NULL")
    cur.execute(
        "UPDATE _ck SET contact_id=(SELECT c.contact_id FROM contacts c "
        "WHERE c.name_norm=_ck.name_norm AND IFNULL(c.org_id,0)=IFNULL(_ck.org_id,0) "
        "AND c.is_deleted=0 LIMIT 1) WHERE contact_id IS NULL")
    cur.execute(
        "INSERT INTO contacts(org_id, first_name, last_name, full_name, name_norm, block_key, title, attrs) "
        "SELECT org_id, first_name, last_name, full_name, name_norm, block_key, title, '{}' "
        "FROM _ck WHERE contact_id IS NULL")
    cur.execute(
        "UPDATE _ck SET contact_id=(SELECT max(c.contact_id) FROM contacts c "
        "WHERE c.name_norm=_ck.name_norm AND IFNULL(c.org_id,0)=IFNULL(_ck.org_id,0)) "
        "WHERE contact_id IS NULL")

    # 3) comms attached to the resolved contact
    cur.execute(
        "INSERT OR IGNORE INTO emails(contact_id, email, email_norm, is_invalid, is_primary) "
        "SELECT k.contact_id, f.email_norm, f.email_norm, max(CAST(f.email_invalid AS INT)), 1 "
        "FROM _f f JOIN _ck k ON k.ckey=f.ckey "
        "WHERE f.email_norm IS NOT NULL AND k.contact_id IS NOT NULL "
        "GROUP BY k.contact_id, f.email_norm")
    for i in range(MAX_PHONES):
        cur.execute(
            f"INSERT OR IGNORE INTO phones(contact_id, phone_raw, phone_e164, kind) "
            f"SELECT DISTINCT k.contact_id, f.p{i}_raw, f.p{i}_e164, COALESCE(f.p{i}_kind,'main') "
            f"FROM _f f JOIN _ck k ON k.ckey=f.ckey "
            f"WHERE f.p{i}_raw IS NOT NULL AND trim(f.p{i}_raw) <> '' AND k.contact_id IS NOT NULL")
    cur.execute(
        "INSERT OR IGNORE INTO addresses(contact_id, line1, city, state, zip, addr_norm, kind) "
        "SELECT DISTINCT k.contact_id, f.line1, f.city, f.state, f.zip, f.addr_norm, 'main' "
        "FROM _f f JOIN _ck k ON k.ckey=f.ckey "
        "WHERE f.addr_norm IS NOT NULL AND f.addr_norm <> '' AND k.contact_id IS NOT NULL")

    # 4) tags (source / region / contact_type) + provenance
    cur.execute("INSERT OR IGNORE INTO tags(kind, value) VALUES ('source', ?)", (source,))
    for kind, col in (("region", "region"), ("contact_type", "contact_type")):
        cur.execute(
            f"INSERT OR IGNORE INTO tags(kind, value) SELECT DISTINCT '{kind}', {col} "
            f"FROM _f WHERE {col} IS NOT NULL")
    cur.execute(
        "INSERT OR IGNORE INTO entity_tags(tag_id, entity_type, entity_id) "
        "SELECT t.tag_id, 'contact', k.contact_id FROM _ck k, tags t "
        "WHERE t.kind='source' AND t.value=? AND k.contact_id IS NOT NULL", (source,))
    for kind, col in (("region", "region"), ("contact_type", "contact_type")):
        cur.execute(
            f"INSERT OR IGNORE INTO entity_tags(tag_id, entity_type, entity_id) "
            f"SELECT DISTINCT t.tag_id, 'contact', k.contact_id "
            f"FROM _f f JOIN _ck k ON k.ckey=f.ckey JOIN tags t "
            f"ON t.kind='{kind}' AND t.value=f.{col} "
            f"WHERE f.{col} IS NOT NULL AND k.contact_id IS NOT NULL")

    # 5) provenance (idempotency anchor) + change log for sync
    cur.execute(
        "INSERT OR IGNORE INTO source_records(source, source_pk, row_hash, raw, contact_id, org_id) "
        "SELECT ?, f.source_pk, f.row_hash, '{}', k.contact_id, k.org_id "
        "FROM _f f LEFT JOIN _ck k ON k.ckey=f.ckey", (source,))
    cur.execute(
        "INSERT INTO change_log(entity_type, entity_id, op, origin) "
        "SELECT 'contact', contact_id, 'upsert', 'fastimport' FROM _ck WHERE contact_id IS NOT NULL")

    stats.new_orgs = cur.execute("SELECT COUNT(*) FROM organizations").fetchone()[0] - orgs_before
    stats.new_contacts = cur.execute("SELECT COUNT(*) FROM contacts").fetchone()[0] - contacts_before
    stats.emails = cur.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
    stats.phones = cur.execute("SELECT COUNT(*) FROM phones").fetchone()[0]

    Repository(conn).rebuild_fts()
    for t in ("_f", "_om", "_ck"):
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
    return stats
