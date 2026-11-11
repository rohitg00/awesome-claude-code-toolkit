-- NTXP Contacts — migration 0006 (PostgreSQL): see the SQLite variant.
CREATE INDEX IF NOT EXISTS ix_addr_contact ON addresses(contact_id);
