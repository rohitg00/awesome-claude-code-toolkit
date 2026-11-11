-- NTXP Contacts — migration 0002: JEV qualification / grading.
-- One grade row per canonical contact. Every source reference is kept (in
-- source_records); this table records the computed quality grade and the
-- exposure/sync gate so outdated data stays in the KB but is held back from the
-- UI and outbound sync.

CREATE TABLE contact_grade (
    contact_id   INTEGER PRIMARY KEY REFERENCES contacts(contact_id),
    grade        REAL NOT NULL DEFAULT 0,       -- probability grade [0,1]
    grade_band   TEXT NOT NULL DEFAULT 'D',     -- A|B|C|D
    sources      INTEGER NOT NULL DEFAULT 0,    -- corroboration: distinct sources
    min_distance INTEGER,                       -- closest distance-from-person observed
    freshest_at  TEXT,                          -- max last_seen across sources
    age_days     INTEGER,                       -- age of the freshest observation
    is_exposed   INTEGER NOT NULL DEFAULT 1,    -- surfaced in the UI
    is_synced    INTEGER NOT NULL DEFAULT 1,    -- eligible for outbound sync
    reason       TEXT,                          -- short human explanation
    computed_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX ix_grade_band ON contact_grade(grade_band);
CREATE INDEX ix_grade_exposed ON contact_grade(is_exposed);
