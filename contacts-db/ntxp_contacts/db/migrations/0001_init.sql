-- NTXP Contacts Database — initial schema (migration 0001)
-- Semi-normalized: entities we query/dedup on are normalized; irreducibly
-- variable per-source fields live in JSON `attrs` columns.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Canonical entities
-- ---------------------------------------------------------------------------

CREATE TABLE organizations (
    org_id      INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    name_norm   TEXT NOT NULL,            -- normalized dedup key
    website     TEXT,
    license_no  TEXT,
    attrs       TEXT NOT NULL DEFAULT '{}',   -- JSON: EMR years, vendor #, enterprise type, ...
    is_deleted  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX ix_org_name_norm ON organizations(name_norm);

CREATE TABLE contacts (
    contact_id  INTEGER PRIMARY KEY,
    org_id      INTEGER REFERENCES organizations(org_id),
    first_name  TEXT,
    last_name   TEXT,
    full_name   TEXT,
    name_norm   TEXT NOT NULL,            -- normalized "first last"
    block_key   TEXT,                     -- indexed dedup blocking key (last-name prefix)
    title       TEXT,
    attrs       TEXT NOT NULL DEFAULT '{}',   -- JSON: region, contact_type, membership_date, ...
    is_deleted  INTEGER NOT NULL DEFAULT 0,   -- tombstone for reversible merges
    merged_into INTEGER REFERENCES contacts(contact_id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX ix_contact_name_norm ON contacts(name_norm);
CREATE INDEX ix_contact_org ON contacts(org_id);
CREATE INDEX ix_contact_block ON contacts(block_key);

-- ---------------------------------------------------------------------------
-- Multi-valued comms. Owned by a contact XOR an org.
-- ---------------------------------------------------------------------------

CREATE TABLE emails (
    email_id    INTEGER PRIMARY KEY,
    contact_id  INTEGER REFERENCES contacts(contact_id),
    org_id      INTEGER REFERENCES organizations(org_id),
    email       TEXT NOT NULL,
    email_norm  TEXT NOT NULL,
    is_invalid  INTEGER NOT NULL DEFAULT 0,
    is_primary  INTEGER NOT NULL DEFAULT 0,
    CHECK ((contact_id IS NOT NULL) <> (org_id IS NOT NULL))
);
CREATE UNIQUE INDEX ux_email_owner
    ON emails(email_norm, COALESCE(contact_id, 0), COALESCE(org_id, 0));
CREATE INDEX ix_email_norm ON emails(email_norm);

CREATE TABLE phones (
    phone_id    INTEGER PRIMARY KEY,
    contact_id  INTEGER REFERENCES contacts(contact_id),
    org_id      INTEGER REFERENCES organizations(org_id),
    phone_raw   TEXT NOT NULL,
    phone_e164  TEXT,                      -- normalized; NULL if unparseable
    kind        TEXT NOT NULL DEFAULT 'main',   -- main|office|cell|fax
    CHECK ((contact_id IS NOT NULL) <> (org_id IS NOT NULL))
);
CREATE UNIQUE INDEX ux_phone_owner
    ON phones(COALESCE(phone_e164, phone_raw), kind, COALESCE(contact_id, 0), COALESCE(org_id, 0));
CREATE INDEX ix_phone_e164 ON phones(phone_e164);
CREATE INDEX ix_phone_contact ON phones(contact_id);

CREATE TABLE addresses (
    address_id  INTEGER PRIMARY KEY,
    contact_id  INTEGER REFERENCES contacts(contact_id),
    org_id      INTEGER REFERENCES organizations(org_id),
    line1       TEXT,
    city        TEXT,
    state       TEXT,
    zip         TEXT,                      -- stored zero-padded as TEXT
    addr_norm   TEXT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'main',
    CHECK ((contact_id IS NOT NULL) <> (org_id IS NOT NULL))
);
CREATE UNIQUE INDEX ux_addr_owner
    ON addresses(addr_norm, COALESCE(contact_id, 0), COALESCE(org_id, 0));
CREATE INDEX ix_addr_org ON addresses(org_id);
CREATE INDEX ix_email_contact ON emails(contact_id);

-- ---------------------------------------------------------------------------
-- Controlled-vocabulary tags / classifications
-- ---------------------------------------------------------------------------

CREATE TABLE tags (
    tag_id  INTEGER PRIMARY KEY,
    kind    TEXT NOT NULL,                 -- certification|region|trade|contact_type|cjp|member|event|source
    value   TEXT NOT NULL,
    UNIQUE (kind, value)
);

CREATE TABLE entity_tags (
    tag_id      INTEGER NOT NULL REFERENCES tags(tag_id),
    entity_type TEXT NOT NULL,             -- contact|org
    entity_id   INTEGER NOT NULL,
    PRIMARY KEY (tag_id, entity_type, entity_id)
);
CREATE INDEX ix_entity_tags_entity ON entity_tags(entity_type, entity_id);

-- ---------------------------------------------------------------------------
-- Provenance + idempotency anchor: one row per source row, ever.
-- ---------------------------------------------------------------------------

CREATE TABLE source_records (
    source_record_id INTEGER PRIMARY KEY,
    source        TEXT NOT NULL,           -- tips|buildingconnectd|approved_subs|luncheon|cjp_pdf
    source_pk     TEXT,                    -- native id if any (MemberID, Number, Vendor)
    row_hash      TEXT NOT NULL,           -- sha256 of normalized source fields
    raw           TEXT NOT NULL,           -- JSON of the original row
    contact_id    INTEGER REFERENCES contacts(contact_id),
    org_id        INTEGER REFERENCES organizations(org_id),
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, source_pk, row_hash)
);
CREATE INDEX ix_src_resolved ON source_records(source, source_pk);

-- Staging queue for low-confidence rows (e.g. OCR). Promoted to canonical
-- tables only after confirmation; never participates in auto-merge.
CREATE TABLE staging_records (
    staging_id  INTEGER PRIMARY KEY,
    source      TEXT NOT NULL,
    row_hash    TEXT NOT NULL,
    payload     TEXT NOT NULL,             -- JSON CanonicalRecord
    confidence  REAL,
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending|approved|rejected|promoted
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, row_hash)
);

-- ---------------------------------------------------------------------------
-- Bi-directional sync
-- ---------------------------------------------------------------------------

CREATE TABLE external_ids (
    system         TEXT NOT NULL,          -- hubspot|jobtread|quo|lightfield|govtribe
    external_id    TEXT NOT NULL,
    contact_id     INTEGER REFERENCES contacts(contact_id),
    org_id         INTEGER REFERENCES organizations(org_id),
    remote_hash    TEXT,                   -- hash of last-synced remote payload
    last_synced_at TEXT,
    sync_state     TEXT NOT NULL DEFAULT 'linked',  -- linked|pending|error
    PRIMARY KEY (system, external_id),
    CHECK ((contact_id IS NOT NULL) <> (org_id IS NOT NULL))
);
CREATE INDEX ix_extid_contact ON external_ids(contact_id);
CREATE INDEX ix_extid_org ON external_ids(org_id);

-- Append-only change log driving outbound sync.
CREATE TABLE change_log (
    seq         INTEGER PRIMARY KEY,       -- monotonic
    entity_type TEXT NOT NULL,             -- contact|org
    entity_id   INTEGER NOT NULL,
    field       TEXT,                      -- NULL = whole-entity create/delete/merge
    op          TEXT NOT NULL,             -- insert|update|delete|merge
    changed_at  TEXT NOT NULL DEFAULT (datetime('now')),
    origin      TEXT NOT NULL              -- import|cli|mcp|pull:<system>
);
CREATE INDEX ix_changelog_entity ON change_log(entity_type, entity_id);

CREATE TABLE sync_state (
    system      TEXT PRIMARY KEY,
    last_seq    INTEGER NOT NULL DEFAULT 0,   -- high-water mark into change_log
    last_pull_at TEXT
);

-- ---------------------------------------------------------------------------
-- Full-text search index (manually maintained by the repository layer)
-- ---------------------------------------------------------------------------

CREATE VIRTUAL TABLE contacts_fts USING fts5(
    entity_type UNINDEXED,
    entity_id   UNINDEXED,
    text
);
