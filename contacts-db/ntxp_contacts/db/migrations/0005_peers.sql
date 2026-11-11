-- NTXP Contacts — migration 0005: interlinking with NTXP Schedules / Master Contracts / Form Fill.
--   peer_outbox   durable queue of signed outbound webhooks (retry + dead-letter)
--   peer_cursor   per-peer watch cursors (change_log seq we've emitted; remote seq we've pulled)
--   peer_context  facts pulled/pushed from peers (contracts, schedule assignments) shown on contact cards
--   peer_seen     inbound event ids, so a re-delivered webhook is applied once

CREATE TABLE peer_outbox (
    outbox_id       INTEGER PRIMARY KEY,
    peer            TEXT NOT NULL,
    event_id        TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    payload         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',   -- pending | sending | delivered | dead
    attempts        INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_error      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    delivered_at    TEXT,
    UNIQUE (peer, event_id)
);
CREATE INDEX ix_outbox_due ON peer_outbox(status, next_attempt_at);

CREATE TABLE peer_cursor (
    peer        TEXT NOT NULL,
    stream      TEXT NOT NULL,
    cursor      TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (peer, stream)
);

CREATE TABLE peer_context (
    ctx_id      INTEGER PRIMARY KEY,
    peer        TEXT NOT NULL,
    kind        TEXT NOT NULL,                          -- contract | assignment
    ref         TEXT NOT NULL,                          -- the peer's own id
    org_id      INTEGER REFERENCES organizations(org_id),
    contact_id  INTEGER REFERENCES contacts(contact_id),
    payload     TEXT NOT NULL,
    observed_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (peer, kind, ref)
);
CREATE INDEX ix_ctx_org ON peer_context(org_id);
CREATE INDEX ix_ctx_contact ON peer_context(contact_id);

CREATE TABLE peer_seen (
    peer        TEXT NOT NULL,
    event_id    TEXT NOT NULL,
    seen_at     TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (peer, event_id)
);
