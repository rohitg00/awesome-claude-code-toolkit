-- NTXP Master Contracts Database — initial schema (migration 0001)
-- Semi-normalized: the fields we query / display / poll on are columns; the
-- irreducibly variable per-contract extras live in a JSON `attrs` column so the
-- table stays stable while the model stays adaptable.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Owner entities (the contracting authority that issued the contract). Holds
-- the contact info the per-contract profile screen renders: website plus
-- customer-service and accounting lines for click-to-call/text + contact file.
-- ---------------------------------------------------------------------------
CREATE TABLE owner_entities (
    owner_id                INTEGER PRIMARY KEY,
    name                    TEXT NOT NULL,
    name_norm               TEXT NOT NULL,          -- dedup key
    website                 TEXT,
    main_phone              TEXT,
    customer_service_phone  TEXT,
    accounting_phone        TEXT,
    email                   TEXT,
    address                 TEXT,
    attrs                   TEXT NOT NULL DEFAULT '{}',
    created_at              TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX ux_owner_name_norm ON owner_entities(name_norm);

-- ---------------------------------------------------------------------------
-- Contracts — the master log. One row per Job Order / Cooperative / Master
-- Subcontract Agreement.
-- ---------------------------------------------------------------------------
CREATE TABLE contracts (
    contract_id             INTEGER PRIMARY KEY,
    contract_title          TEXT NOT NULL,
    contract_no             TEXT,                   -- contract / RFP #
    contract_no_norm        TEXT,                   -- alnum-collapsed match key
    contract_type           TEXT,                   -- see config.CONTRACT_TYPES
    owner_id                INTEGER REFERENCES owner_entities(owner_id),
    owner_entity            TEXT,                   -- denormalized for fast log render
    recipient               TEXT NOT NULL DEFAULT 'NTXP LLC',
    location                TEXT,
    estimated_budget        REAL,
    award_date              TEXT,                   -- ISO yyyy-mm-dd
    duration                TEXT,
    expiration_date         TEXT,                   -- ISO yyyy-mm-dd
    coefficient_multiplier  REAL,
    cooperative_fee         TEXT,
    allowable_scope         TEXT,
    notes                   TEXT,
    pdf_url                 TEXT,                   -- live link to signed PDF
    is_executed             INTEGER NOT NULL DEFAULT 0,   -- 0 => flagged unexecuted
    attrs                   TEXT NOT NULL DEFAULT '{}',
    rev                     INTEGER NOT NULL DEFAULT 1,   -- bumped on every field save
    is_deleted              INTEGER NOT NULL DEFAULT 0,
    created_at              TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX ix_contract_no_norm ON contracts(contract_no_norm);
CREATE INDEX ix_contract_owner ON contracts(owner_id);
CREATE INDEX ix_contract_exp ON contracts(expiration_date);
CREATE INDEX ix_contract_type ON contracts(contract_type);

-- ---------------------------------------------------------------------------
-- Jobs performed under a contract — cached from the jobs system (JobTread) so
-- the profile screen can roll up a job list + total sales, and other tools can
-- poll without a live JobTread call.
-- ---------------------------------------------------------------------------
CREATE TABLE jobs (
    job_id          INTEGER PRIMARY KEY,
    contract_id     INTEGER REFERENCES contracts(contract_id),
    name            TEXT NOT NULL,
    customer        TEXT,
    status          TEXT,
    contract_value  REAL,
    sales_amount    REAL,                           -- invoiced / recognized sales
    source          TEXT NOT NULL DEFAULT 'jobtread',
    external_id     TEXT,
    attrs           TEXT NOT NULL DEFAULT '{}',
    synced_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, external_id)
);
CREATE INDEX ix_jobs_contract ON jobs(contract_id);

-- ---------------------------------------------------------------------------
-- Provenance + idempotency anchor: one row per imported source row, ever.
-- ---------------------------------------------------------------------------
CREATE TABLE source_records (
    source_record_id INTEGER PRIMARY KEY,
    source        TEXT NOT NULL,
    source_pk     TEXT,
    row_hash      TEXT NOT NULL,
    raw           TEXT NOT NULL,                    -- JSON of the original row
    contract_id   INTEGER REFERENCES contracts(contract_id),
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, source_pk, row_hash)
);

-- ---------------------------------------------------------------------------
-- Append-only audit/change log. Field-level rows are what make concurrent
-- editing safe (two editors touching different fields never collide) and give
-- every save a who/when/what trail.
-- ---------------------------------------------------------------------------
CREATE TABLE change_log (
    seq         INTEGER PRIMARY KEY,                -- monotonic
    contract_id INTEGER NOT NULL,
    field       TEXT,                               -- NULL = whole-row op
    old_value   TEXT,
    new_value   TEXT,
    op          TEXT NOT NULL,                      -- insert|update|delete
    actor       TEXT NOT NULL DEFAULT 'system',     -- editor identity / origin
    changed_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX ix_changelog_contract ON change_log(contract_id);

-- ---------------------------------------------------------------------------
-- Full-text search index (maintained by the repository layer).
-- ---------------------------------------------------------------------------
CREATE VIRTUAL TABLE contracts_fts USING fts5(
    contract_id UNINDEXED,
    text
);
