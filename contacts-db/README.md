# Deploy `contacts.ntxpllc.cloud`

Stack: **Hostinger VPS** (existing proxy → this container) → `ntxp serve-http` (live page, `/api`, `/api/v1`, `/mcp`, `/carddav`,
peer webhooks) → **Supabase Postgres** (dedicated `ntxp_contacts` schema). Interlinked with NTXP Schedules / Master Contracts /
Form Fill — see [../docs/INTEGRATIONS.md](../docs/INTEGRATIONS.md).

* **[RUNBOOK.md](RUNBOOK.md)** — the exact steps (Hostinger connector calls with confirmation gates, or manual ssh).
* `docker-compose.yml` — joins the VPS's existing proxy (no ports published, no second Caddy); `.env.example` — every setting.
* `supabase_setup.sql` — one-time dedicated role + schema; safe in a Supabase project shared with other apps.
* `Dockerfile` — built by CI (`.github/workflows/contacts-image.yml`) because the Hostinger Docker Manager can only pull images.

## Security model
- **Sign-in**: Google Workspace token, `hd == ntxpllc.com`, checked server-side on every request. Peer apps use per-peer service tokens that work on `/api/v1` **only**.
- **Supabase**: dedicated role + schema; RLS enabled with **no policies** on every table (re-applied after each migration, scoped to this schema only) and anon/authenticated grants revoked; the schema must not be added to the Data API's exposed schemas.
- **Network**: outbound peer URLs restricted to `https://*.ntxpllc.cloud`; CSP/XFO/nosniff on the page; TLS at the existing proxy.
- **Proprietary assets** (NTXP document engine, logo) are mounted from the VPS, never in git or in the registry image.
- **Untrusted data**: contact fields come from Gmail/Calendar/CRMs — escaped in the page, `<`/`>` stripped before the renderer.
