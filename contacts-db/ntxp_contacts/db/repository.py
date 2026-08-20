"""Thin typed persistence layer over sqlite3.

Holds all SQL. Loaders and the resolver call these methods; they never touch
SQL directly. Upserts use natural unique indexes so surrogate keys are stable
across re-imports (the basis of idempotency).
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable

from ..model import Address, CanonicalRecord, Email, Phone, Tag


class Repository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.defer_fts = False   # when True, skip per-row FTS; call rebuild_fts() once

    # -- low level ----------------------------------------------------------
    def _now_touch(self, table: str, pk_col: str, pk: int) -> None:
        self.conn.execute(
            f"UPDATE {table} SET updated_at = datetime('now') WHERE {pk_col} = ?", (pk,)
        )

    def log_change(self, entity_type: str, entity_id: int, op: str,
                   origin: str, field: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO change_log(entity_type, entity_id, field, op, origin) "
            "VALUES (?,?,?,?,?)",
            (entity_type, entity_id, field, op, origin),
        )

    # -- organizations ------------------------------------------------------
    def find_org_by_norm(self, name_norm: str) -> int | None:
        row = self.conn.execute(
            "SELECT org_id FROM organizations WHERE name_norm = ? AND is_deleted = 0 "
            "ORDER BY org_id LIMIT 1",
            (name_norm,),
        ).fetchone()
        return row["org_id"] if row else None

    def create_org(self, rec: CanonicalRecord, origin: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO organizations(name, name_norm, website, license_no, attrs) "
            "VALUES (?,?,?,?,?)",
            (rec.org_name, rec.org_name_norm, rec.website, rec.license_no,
             json.dumps(rec.org_attrs, sort_keys=True)),
        )
        org_id = int(cur.lastrowid)
        self.log_change("org", org_id, "insert", origin)
        self._reindex_org(org_id)
        return org_id

    def update_org(self, org_id: int, rec: CanonicalRecord, origin: str) -> None:
        """Fill blanks / merge attrs without clobbering existing non-null fields."""
        row = self.conn.execute(
            "SELECT website, license_no, attrs FROM organizations WHERE org_id = ?",
            (org_id,),
        ).fetchone()
        attrs = json.loads(row["attrs"] or "{}")
        attrs.update({k: v for k, v in rec.org_attrs.items() if v not in (None, "")})
        self.conn.execute(
            "UPDATE organizations SET website = COALESCE(website, ?), "
            "license_no = COALESCE(license_no, ?), attrs = ?, "
            "updated_at = datetime('now') WHERE org_id = ?",
            (rec.website, rec.license_no, json.dumps(attrs, sort_keys=True), org_id),
        )
        self.log_change("org", org_id, "update", origin)
        # FTS row for an org depends only on its name, which this update never
        # changes — so no reindex needed here.

    # -- contacts -----------------------------------------------------------
    def find_contact_by_email(self, email_norm: str) -> int | None:
        row = self.conn.execute(
            "SELECT e.contact_id FROM emails e "
            "JOIN contacts c ON c.contact_id = e.contact_id "
            "WHERE e.email_norm = ? AND e.is_invalid = 0 AND c.is_deleted = 0 "
            "ORDER BY e.contact_id LIMIT 1",
            (email_norm,),
        ).fetchone()
        return row["contact_id"] if row else None

    def contact_candidates(self, block_key: str | None, org_id: int | None) -> list[sqlite3.Row]:
        """Cheap indexed blocking with everything scoring needs in one query.

        Returns contact_id, name_norm, the org's normalized name + state, and a
        comma-joined set of E.164 phones — so the resolver scores candidates
        without any per-candidate follow-up queries (the prior O(candidates)
        round-trips were the import bottleneck)."""
        if not block_key and not org_id:
            return []
        # Use a UNION of single-column equality predicates so EACH arm is driven
        # by its own index (ix_contact_block / ix_contact_org). A combined
        # `block_key=? OR org_id=?` defeats SQLite's index use and full-scans the
        # contacts table on every row -> O(n^2) imports.
        arms, params = [], []
        if block_key:
            arms.append("SELECT contact_id, name_norm, org_id FROM contacts "
                        "WHERE is_deleted = 0 AND block_key = ?")
            params.append(block_key)
        if org_id:
            arms.append("SELECT contact_id, name_norm, org_id FROM contacts "
                        "WHERE is_deleted = 0 AND org_id = ?")
            params.append(org_id)
        inner = " UNION ".join(arms)
        # Compute scoring sub-selects only for the bounded candidate set.
        q = (
            "WITH cand AS (" + inner + " LIMIT 100) "
            "SELECT c.contact_id, c.name_norm, o.name_norm AS org_norm, c.org_id, "
            "  (SELECT a.state FROM addresses a WHERE a.org_id = c.org_id AND a.state IS NOT NULL LIMIT 1) AS org_state, "
            "  (SELECT GROUP_CONCAT(p.phone_e164) FROM phones p WHERE p.contact_id = c.contact_id AND p.phone_e164 IS NOT NULL) AS phones "
            "FROM cand c LEFT JOIN organizations o ON o.org_id = c.org_id"
        )
        return self.conn.execute(q, params).fetchall()

    def create_contact(self, rec: CanonicalRecord, org_id: int | None, origin: str) -> int:
        from ..normalize import block_key
        cur = self.conn.execute(
            "INSERT INTO contacts(org_id, first_name, last_name, full_name, "
            "name_norm, block_key, title, attrs) VALUES (?,?,?,?,?,?,?,?)",
            (org_id, rec.first_name, rec.last_name, rec.full_name, rec.name_norm,
             block_key(rec.first_name, rec.last_name, rec.name_norm),
             rec.title, json.dumps(rec.contact_attrs, sort_keys=True)),
        )
        contact_id = int(cur.lastrowid)
        self.log_change("contact", contact_id, "insert", origin)
        self._reindex_contact(contact_id)
        return contact_id

    def update_contact(self, contact_id: int, rec: CanonicalRecord,
                       org_id: int | None, origin: str) -> None:
        row = self.conn.execute(
            "SELECT title, attrs FROM contacts WHERE contact_id = ?", (contact_id,)
        ).fetchone()
        attrs = json.loads(row["attrs"] or "{}")
        attrs.update({k: v for k, v in rec.contact_attrs.items() if v not in (None, "")})
        self.conn.execute(
            "UPDATE contacts SET org_id = COALESCE(org_id, ?), "
            "first_name = COALESCE(first_name, ?), last_name = COALESCE(last_name, ?), "
            "full_name = COALESCE(full_name, ?), title = COALESCE(title, ?), "
            "attrs = ?, updated_at = datetime('now') WHERE contact_id = ?",
            (org_id, rec.first_name, rec.last_name, rec.full_name, rec.title,
             json.dumps(attrs, sort_keys=True), contact_id),
        )
        self.log_change("contact", contact_id, "update", origin)
        self._reindex_contact(contact_id)

    # -- comms / tags -------------------------------------------------------
    def add_email(self, e: Email, contact_id: int | None, org_id: int | None) -> None:
        self.conn.execute(
            "INSERT INTO emails(contact_id, org_id, email, email_norm, is_invalid, is_primary) "
            "VALUES (?,?,?,?,?,?) ON CONFLICT DO NOTHING",
            (contact_id, org_id, e.email, e.email_norm, int(e.is_invalid), int(e.is_primary)),
        )

    def add_phone(self, p: Phone, contact_id: int | None, org_id: int | None) -> None:
        self.conn.execute(
            "INSERT INTO phones(contact_id, org_id, phone_raw, phone_e164, kind) "
            "VALUES (?,?,?,?,?) ON CONFLICT DO NOTHING",
            (contact_id, org_id, p.phone_raw, p.phone_e164, p.kind),
        )

    def add_address(self, a: Address, contact_id: int | None, org_id: int | None) -> None:
        if not a.addr_norm:
            return
        self.conn.execute(
            "INSERT INTO addresses(contact_id, org_id, line1, city, state, zip, addr_norm, kind) "
            "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
            (contact_id, org_id, a.line1, a.city, a.state, a.zip, a.addr_norm, a.kind),
        )

    def add_tag(self, t: Tag, entity_type: str, entity_id: int) -> None:
        cur = self.conn.execute(
            "INSERT INTO tags(kind, value) VALUES (?,?) "
            "ON CONFLICT(kind, value) DO UPDATE SET kind = kind RETURNING tag_id",
            (t.kind, t.value),
        )
        tag_id = cur.fetchone()["tag_id"]
        self.conn.execute(
            "INSERT INTO entity_tags(tag_id, entity_type, entity_id) VALUES (?,?,?) "
            "ON CONFLICT DO NOTHING",
            (tag_id, entity_type, entity_id),
        )

    # -- source records (idempotency) --------------------------------------
    def find_source_record(self, source: str, source_pk: str | None,
                           row_hash: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM source_records WHERE source = ? AND "
            "IFNULL(source_pk,'') = IFNULL(?,'') AND row_hash = ?",
            (source, source_pk, row_hash),
        ).fetchone()

    def find_source_by_pk(self, source: str, source_pk: str | None) -> sqlite3.Row | None:
        if source_pk is None:
            return None
        return self.conn.execute(
            "SELECT * FROM source_records WHERE source = ? AND source_pk = ? "
            "ORDER BY source_record_id DESC LIMIT 1",
            (source, source_pk),
        ).fetchone()

    def touch_source_record(self, source_record_id: int) -> None:
        self.conn.execute(
            "UPDATE source_records SET last_seen_at = datetime('now') "
            "WHERE source_record_id = ?",
            (source_record_id,),
        )

    def record_source(self, source: str, source_pk: str | None, row_hash: str,
                      raw: dict, contact_id: int | None, org_id: int | None) -> None:
        self.conn.execute(
            "INSERT INTO source_records(source, source_pk, row_hash, raw, contact_id, org_id) "
            "VALUES (?,?,?,?,?,?) ON CONFLICT(source, source_pk, row_hash) DO UPDATE SET "
            "last_seen_at = datetime('now')",
            (source, source_pk, row_hash, json.dumps(raw, default=str),
             contact_id, org_id),
        )

    # -- staging (OCR quarantine) ------------------------------------------
    def stage_record(self, source: str, row_hash: str, payload: dict,
                     confidence: float | None, note: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO staging_records(source, row_hash, payload, confidence, note) "
            "VALUES (?,?,?,?,?) ON CONFLICT(source, row_hash) DO UPDATE SET "
            "payload = excluded.payload, confidence = excluded.confidence",
            (source, row_hash, json.dumps(payload, default=str), confidence, note),
        )

    # -- FTS ----------------------------------------------------------------
    def rebuild_fts(self) -> None:
        """Repopulate the whole FTS index in two set-based statements. Far
        cheaper than per-row reindexing during a bulk import."""
        self.conn.execute("DELETE FROM contacts_fts")
        self.conn.execute(
            "INSERT INTO contacts_fts(entity_type, entity_id, text) "
            "SELECT 'contact', c.contact_id, "
            "  TRIM(COALESCE(c.full_name,'')||' '||COALESCE(c.first_name,'')||' '||"
            "  COALESCE(c.last_name,'')||' '||COALESCE(o.name,'')||' '||"
            "  COALESCE((SELECT GROUP_CONCAT(e.email,' ') FROM emails e WHERE e.contact_id=c.contact_id),'')) "
            "FROM contacts c LEFT JOIN organizations o ON o.org_id=c.org_id "
            "WHERE c.is_deleted = 0")
        self.conn.execute(
            "INSERT INTO contacts_fts(entity_type, entity_id, text) "
            "SELECT 'org', org_id, name FROM organizations WHERE is_deleted = 0")

    def _reindex_contact(self, contact_id: int) -> None:
        if self.defer_fts:
            return
        c = self.conn.execute(
            "SELECT full_name, first_name, last_name FROM contacts WHERE contact_id = ?",
            (contact_id,),
        ).fetchone()
        if not c:
            return
        emails = [r["email"] for r in self.conn.execute(
            "SELECT email FROM emails WHERE contact_id = ?", (contact_id,))]
        org = self.conn.execute(
            "SELECT o.name FROM contacts c LEFT JOIN organizations o ON o.org_id = c.org_id "
            "WHERE c.contact_id = ?", (contact_id,)).fetchone()
        text = " ".join(filter(None, [
            c["full_name"], c["first_name"], c["last_name"],
            org["name"] if org else None, *emails]))
        self.conn.execute(
            "DELETE FROM contacts_fts WHERE entity_type = 'contact' AND entity_id = ?",
            (contact_id,))
        self.conn.execute(
            "INSERT INTO contacts_fts(entity_type, entity_id, text) VALUES ('contact', ?, ?)",
            (contact_id, text))

    def _reindex_org(self, org_id: int) -> None:
        if self.defer_fts:
            return
        o = self.conn.execute(
            "SELECT name FROM organizations WHERE org_id = ?", (org_id,)).fetchone()
        if not o:
            return
        self.conn.execute(
            "DELETE FROM contacts_fts WHERE entity_type = 'org' AND entity_id = ?", (org_id,))
        self.conn.execute(
            "INSERT INTO contacts_fts(entity_type, entity_id, text) VALUES ('org', ?, ?)",
            (org_id, o["name"]))

    # -- merge (reversible) -------------------------------------------------
    def merge_contacts(self, survivor: int, loser: int, origin: str = "cli") -> None:
        if survivor == loser:
            return
        for tbl in ("emails", "phones", "addresses", "source_records"):
            self.conn.execute(
                f"UPDATE {tbl} SET contact_id = ? WHERE contact_id = ?", (survivor, loser))
        self.conn.execute(
            "UPDATE entity_tags SET entity_id = ? WHERE entity_type = 'contact' AND entity_id = ?",
            (survivor, loser))
        self.conn.execute(
            "UPDATE external_ids SET contact_id = ? WHERE contact_id = ?", (survivor, loser))
        self.conn.execute(
            "UPDATE contacts SET is_deleted = 1, merged_into = ?, updated_at = datetime('now') "
            "WHERE contact_id = ?", (survivor, loser))
        self.conn.execute(
            "DELETE FROM contacts_fts WHERE entity_type = 'contact' AND entity_id = ?", (loser,))
        self.log_change("contact", loser, "merge", origin)
        self._reindex_contact(survivor)

    # -- prune (reversible by default) --------------------------------------
    def prune_by_state(self, source: str, keep_states, hard: bool = False,
                       dry_run: bool = False, origin: str = "prune") -> dict:
        """Remove members of `source` whose org address state is not in
        `keep_states`. Tombstones org + its contacts (recoverable) unless
        `hard=True`. Returns a counts summary."""
        keep = {s.strip().upper() for s in keep_states if s.strip()}
        src_orgs = {r[0] for r in self.conn.execute(
            "SELECT DISTINCT org_id FROM source_records WHERE source = ? AND org_id IS NOT NULL",
            (source,))}
        in_keep = {r[0] for r in self.conn.execute(
            "SELECT DISTINCT org_id FROM addresses WHERE org_id IS NOT NULL AND state IN (%s)"
            % ",".join("?" * len(keep)), tuple(keep))} if keep else set()
        removable = src_orgs - in_keep

        self.conn.execute("DROP TABLE IF EXISTS _prune_orgs")
        self.conn.execute("CREATE TEMP TABLE _prune_orgs(org_id INTEGER PRIMARY KEY)")
        self.conn.executemany("INSERT OR IGNORE INTO _prune_orgs VALUES (?)",
                              [(o,) for o in removable])

        n_contacts = self.conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE is_deleted = 0 "
            "AND org_id IN (SELECT org_id FROM _prune_orgs)").fetchone()[0]
        summary = {"source": source, "keep_states": sorted(keep),
                   "orgs_removed": len(removable), "orgs_kept": len(in_keep & src_orgs),
                   "contacts_removed": n_contacts, "mode": "hard" if hard else "tombstone"}
        if dry_run or not removable:
            summary["dry_run"] = dry_run
            self.conn.execute("DROP TABLE IF EXISTS _prune_orgs")
            return summary

        # Audit log (delete events drive outbound sync).
        self.conn.execute(
            "INSERT INTO change_log(entity_type, entity_id, op, origin) "
            "SELECT 'contact', contact_id, 'delete', ? FROM contacts "
            "WHERE org_id IN (SELECT org_id FROM _prune_orgs)", (origin,))
        self.conn.execute(
            "INSERT INTO change_log(entity_type, entity_id, op, origin) "
            "SELECT 'org', org_id, 'delete', ? FROM _prune_orgs", (origin,))

        # Drop from the search index either way.
        self.conn.execute(
            "DELETE FROM contacts_fts WHERE entity_type='contact' AND entity_id IN "
            "(SELECT contact_id FROM contacts WHERE org_id IN (SELECT org_id FROM _prune_orgs))")
        self.conn.execute(
            "DELETE FROM contacts_fts WHERE entity_type='org' AND entity_id IN "
            "(SELECT org_id FROM _prune_orgs)")

        if hard:
            self.conn.execute("DROP TABLE IF EXISTS _prune_contacts")
            self.conn.execute(
                "CREATE TEMP TABLE _prune_contacts AS "
                "SELECT contact_id FROM contacts WHERE org_id IN (SELECT org_id FROM _prune_orgs)")
            for tbl in ("emails", "phones", "addresses", "source_records", "external_ids"):
                self.conn.execute(
                    f"DELETE FROM {tbl} WHERE contact_id IN (SELECT contact_id FROM _prune_contacts)")
                self.conn.execute(
                    f"DELETE FROM {tbl} WHERE org_id IN (SELECT org_id FROM _prune_orgs)")
            self.conn.execute(
                "DELETE FROM entity_tags WHERE (entity_type='contact' AND entity_id IN (SELECT contact_id FROM _prune_contacts)) "
                "OR (entity_type='org' AND entity_id IN (SELECT org_id FROM _prune_orgs))")
            self.conn.execute("DELETE FROM contacts WHERE contact_id IN (SELECT contact_id FROM _prune_contacts)")
            self.conn.execute("DELETE FROM organizations WHERE org_id IN (SELECT org_id FROM _prune_orgs)")
            self.conn.execute("DROP TABLE IF EXISTS _prune_contacts")
        else:
            self.conn.execute(
                "UPDATE contacts SET is_deleted = 1, updated_at = datetime('now') "
                "WHERE org_id IN (SELECT org_id FROM _prune_orgs)")
            self.conn.execute(
                "UPDATE organizations SET is_deleted = 1, updated_at = datetime('now') "
                "WHERE org_id IN (SELECT org_id FROM _prune_orgs)")

        self.conn.execute("DROP TABLE IF EXISTS _prune_orgs")
        return summary

    # -- queries ------------------------------------------------------------
    def search(self, text: str, limit: int = 25) -> list[dict]:
        rows = self.conn.execute(
            "SELECT entity_type, entity_id FROM contacts_fts "
            "WHERE contacts_fts MATCH ? LIMIT ?",
            (_fts_query(text), limit),
        ).fetchall()
        out = []
        for r in rows:
            if r["entity_type"] == "contact":
                rec = self.get_contact(r["entity_id"])
            else:
                rec = self.get_org(r["entity_id"])
            if rec:
                out.append(rec)
        return out

    def get_contact(self, contact_id: int) -> dict | None:
        c = self.conn.execute(
            "SELECT * FROM contacts WHERE contact_id = ?", (contact_id,)).fetchone()
        if not c:
            return None
        d = dict(c)
        d["attrs"] = json.loads(d.get("attrs") or "{}")
        d["emails"] = [dict(r) for r in self.conn.execute(
            "SELECT email, email_norm, is_invalid, is_primary FROM emails WHERE contact_id = ?",
            (contact_id,))]
        d["phones"] = [dict(r) for r in self.conn.execute(
            "SELECT phone_raw, phone_e164, kind FROM phones WHERE contact_id = ?",
            (contact_id,))]
        d["addresses"] = [dict(r) for r in self.conn.execute(
            "SELECT line1, city, state, zip, kind FROM addresses WHERE contact_id = ?",
            (contact_id,))]
        d["tags"] = [dict(r) for r in self.conn.execute(
            "SELECT t.kind, t.value FROM tags t JOIN entity_tags et ON et.tag_id = t.tag_id "
            "WHERE et.entity_type = 'contact' AND et.entity_id = ?", (contact_id,))]
        if c["org_id"]:
            org = self.conn.execute(
                "SELECT name FROM organizations WHERE org_id = ?", (c["org_id"],)).fetchone()
            d["org_name"] = org["name"] if org else None
            # Fall back to the org's address when the person has none of their
            # own (e.g. TIPS stores the address on the member org).
            if not d["addresses"]:
                d["addresses"] = [dict(r) for r in self.conn.execute(
                    "SELECT line1, city, state, zip, kind FROM addresses WHERE org_id = ?",
                    (c["org_id"],))]
        return d

    def get_org(self, org_id: int) -> dict | None:
        o = self.conn.execute(
            "SELECT * FROM organizations WHERE org_id = ?", (org_id,)).fetchone()
        if not o:
            return None
        d = dict(o)
        d["attrs"] = json.loads(d.get("attrs") or "{}")
        d["entity"] = "org"
        return d

    def stats(self) -> dict:
        def n(sql: str) -> int:
            return self.conn.execute(sql).fetchone()[0]
        by_source = {r["source"]: r["c"] for r in self.conn.execute(
            "SELECT source, COUNT(*) c FROM source_records GROUP BY source")}
        return {
            "organizations": n("SELECT COUNT(*) FROM organizations WHERE is_deleted = 0"),
            "contacts": n("SELECT COUNT(*) FROM contacts WHERE is_deleted = 0"),
            "contacts_merged": n("SELECT COUNT(*) FROM contacts WHERE is_deleted = 1"),
            "emails": n("SELECT COUNT(*) FROM emails"),
            "phones": n("SELECT COUNT(*) FROM phones"),
            "source_records": n("SELECT COUNT(*) FROM source_records"),
            "staging_pending": n("SELECT COUNT(*) FROM staging_records WHERE status = 'pending'"),
            "by_source": by_source,
        }


def _fts_query(text: str) -> str:
    """Make a forgiving prefix-OR FTS5 query from free text."""
    import re
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return '""'
    return " OR ".join(f'{t}*' for t in tokens)


def iter_contacts(conn: sqlite3.Connection) -> Iterable[dict]:
    repo = Repository(conn)
    for r in conn.execute("SELECT contact_id FROM contacts WHERE is_deleted = 0"):
        yield repo.get_contact(r["contact_id"])
