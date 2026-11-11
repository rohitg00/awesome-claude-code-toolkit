-- NTXP Contacts — migration 0003: enrichment (missing-field backfill, photo,
-- LinkedIn cross-reference). Confirmed values land on the contact; every
-- proposed value is kept as a graded candidate for review/audit.

ALTER TABLE contacts ADD COLUMN photo_url TEXT;
ALTER TABLE contacts ADD COLUMN linkedin_url TEXT;

CREATE TABLE enrichment_candidates (
    cand_id     INTEGER PRIMARY KEY,
    contact_id  INTEGER NOT NULL REFERENCES contacts(contact_id),
    field       TEXT NOT NULL,       -- email|phone|address|website|photo|linkedin
    value       TEXT NOT NULL,
    source      TEXT NOT NULL,       -- gravatar|public_directory|linkedin|holehe|...
    grade       REAL NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'proposed',  -- proposed|confirmed|rejected
    evidence    TEXT,                -- JSON notes (corroborating sources, query, ...)
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (contact_id, field, value, source)
);
CREATE INDEX ix_cand_contact ON enrichment_candidates(contact_id);
CREATE INDEX ix_cand_status ON enrichment_candidates(status);
CREATE INDEX ix_cand_field ON enrichment_candidates(field);
