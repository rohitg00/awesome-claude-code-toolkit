-- NTXP Contacts — one-time Supabase setup. Run in the Supabase SQL editor as the `postgres` role.
-- Safe in a project SHARED with other NTXP apps: it creates a dedicated role + schema and never
-- touches anything else. The app's migrations and RLS lockdown only ever act inside this schema.
--
-- 1) Replace <<PASSWORD>> with a long random password (e.g. `openssl rand -base64 36`).
-- 2) Connect the app as  ntxp_contacts_app.<project-ref>  (Supavisor "Session pooler", port 5432).
--    Connection string: Project Settings > Database > Connection string > Session pooler.

CREATE ROLE ntxp_contacts_app LOGIN PASSWORD '<<PASSWORD>>' NOBYPASSRLS NOCREATEDB NOCREATEROLE;
GRANT ntxp_contacts_app TO postgres;                              -- lets postgres create the schema owned by it
CREATE SCHEMA IF NOT EXISTS ntxp_contacts AUTHORIZATION ntxp_contacts_app;
ALTER ROLE ntxp_contacts_app SET search_path = ntxp_contacts;     -- every session (and pooler connection) lands here
REVOKE ALL ON SCHEMA ntxp_contacts FROM PUBLIC;                   -- only the owner role can use it
-- Do NOT add `ntxp_contacts` to Settings > API > Exposed schemas: contact PII must never be reachable
-- through the Supabase Data API. (Exposed schemas default to `public` only.)
