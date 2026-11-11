-- NTXP Contacts — migration 0002 (PostgreSQL): JEV qualification / grading.

CREATE TABLE contact_grade (
    contact_id   BIGINT PRIMARY KEY REFERENCES contacts(contact_id),
    grade        DOUBLE PRECISION NOT NULL DEFAULT 0,
    grade_band   TEXT NOT NULL DEFAULT 'D',
    sources      INTEGER NOT NULL DEFAULT 0,
    min_distance INTEGER,
    freshest_at  TIMESTAMPTZ,
    age_days     INTEGER,
    is_exposed   INTEGER NOT NULL DEFAULT 1,
    is_synced    INTEGER NOT NULL DEFAULT 1,
    reason       TEXT,
    computed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_grade_band ON contact_grade(grade_band);
CREATE INDEX ix_grade_exposed ON contact_grade(is_exposed);
