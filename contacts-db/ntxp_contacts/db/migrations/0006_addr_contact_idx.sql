-- NTXP Contacts — migration 0006: the list view joins addresses on contact_id (BASE city/state subqueries,
-- run per row for every list, count and facet call). Only org_id was indexed, so each was a table scan.
CREATE INDEX IF NOT EXISTS ix_addr_contact ON addresses(contact_id);
