-- NTXP Contacts — migration 0004: persisted model-council answers.
-- Every council decision (consensus choice + per-judge provenance + cost) is
-- stored so effectiveness can be audited and reviewed over time.

CREATE TABLE council_answers (
    answer_id   INTEGER PRIMARY KEY,
    kind        TEXT NOT NULL,              -- pick_value | match | classify
    question    TEXT NOT NULL,
    choice      TEXT,                       -- winning option id (NULL = abstained)
    confidence  REAL NOT NULL DEFAULT 0,
    cost        REAL NOT NULL DEFAULT 0,
    mode        TEXT NOT NULL,              -- jev-only | escalated
    voters      TEXT,                       -- JSON list of judges backing the choice
    provenance  TEXT NOT NULL,              -- JSON: every judge's verdict
    options     TEXT,                       -- JSON: the options considered
    contact_id  INTEGER REFERENCES contacts(contact_id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX ix_council_created ON council_answers(created_at);
CREATE INDEX ix_council_contact ON council_answers(contact_id);
