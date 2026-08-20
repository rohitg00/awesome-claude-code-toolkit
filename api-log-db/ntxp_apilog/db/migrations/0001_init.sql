-- NTXP API Log — initial schema (migration 0001)
-- One shared registry of APIs: endpoint, credentials, and running cost.
-- Secret columns (api_key_enc, key_number_enc, login_secret_enc) hold Fernet
-- ciphertext (see crypto.py); everything else is plaintext metadata.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- The registry: one row per API.
-- ---------------------------------------------------------------------------

CREATE TABLE apis (
    api_id          INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,                 -- human label, e.g. "OpenAI"
    name_norm       TEXT NOT NULL,                 -- lowercased dedup key
    provider        TEXT,                          -- vendor/company
    category        TEXT,                          -- llm|payments|maps|...
    base_url        TEXT,                          -- the API URL
    docs_url        TEXT,
    login_url       TEXT,                          -- provider console / portal
    purpose         TEXT,                          -- what it's for (intent match)
    auth_type       TEXT NOT NULL DEFAULT 'api_key', -- api_key|bearer|basic|oauth2|none

    -- secrets (encrypted at rest)
    api_key_enc     TEXT,                          -- the request token/secret
    key_number_enc  TEXT,                          -- key id / account / project no.
    login_user      TEXT,                          -- console username/email
    login_secret_enc TEXT,                         -- console password

    -- cost
    cost_model      TEXT,                          -- "$0.01 / 1K tokens", "$20/mo"
    currency        TEXT NOT NULL DEFAULT 'USD',
    monthly_budget  REAL,

    status          TEXT NOT NULL DEFAULT 'active', -- active|inactive|revoked|trial
    owner           TEXT,                          -- who registered it
    tags            TEXT NOT NULL DEFAULT '[]',    -- JSON array
    notes           TEXT,
    attrs           TEXT NOT NULL DEFAULT '{}',    -- JSON: arbitrary extra fields

    is_deleted      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX ux_apis_name_norm ON apis(name_norm) WHERE is_deleted = 0;
CREATE INDEX ix_apis_category ON apis(category);
CREATE INDEX ix_apis_status ON apis(status);

-- ---------------------------------------------------------------------------
-- Cost / usage log: append-only, drives the running spend total.
-- ---------------------------------------------------------------------------

CREATE TABLE usage_log (
    log_id       INTEGER PRIMARY KEY,
    api_id       INTEGER NOT NULL REFERENCES apis(api_id),
    occurred_at  TEXT NOT NULL DEFAULT (datetime('now')),
    cost         REAL NOT NULL DEFAULT 0,
    currency     TEXT NOT NULL DEFAULT 'USD',
    units        REAL,                              -- tokens|requests|GB|...
    unit_kind    TEXT,
    description  TEXT,
    requested_by TEXT,                              -- system|skill:<name>|user:<email>
    origin       TEXT NOT NULL DEFAULT 'cli'        -- cli|mcp|dashboard
);
CREATE INDEX ix_usage_api ON usage_log(api_id);
CREATE INDEX ix_usage_when ON usage_log(occurred_at);

-- ---------------------------------------------------------------------------
-- Access log: audit trail for every credential read (who/what/why).
-- Because this DB hands out live secrets, reveals are always recorded.
-- ---------------------------------------------------------------------------

CREATE TABLE access_log (
    access_id    INTEGER PRIMARY KEY,
    api_id       INTEGER NOT NULL REFERENCES apis(api_id),
    accessed_at  TEXT NOT NULL DEFAULT (datetime('now')),
    action       TEXT NOT NULL,                     -- view|reveal|fill
    accessor     TEXT,                              -- system|skill:<name>|user:<email>
    purpose      TEXT,
    origin       TEXT NOT NULL DEFAULT 'cli'        -- cli|mcp|dashboard
);
CREATE INDEX ix_access_api ON access_log(api_id);

-- ---------------------------------------------------------------------------
-- Full-text search index (maintained by the repository layer).
-- ---------------------------------------------------------------------------

CREATE VIRTUAL TABLE apis_fts USING fts5(
    api_id      UNINDEXED,
    text                                            -- name, provider, purpose, tags, category
);
