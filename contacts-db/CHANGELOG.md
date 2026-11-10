# Changelog — NTXP Contacts Platform

All dates ISO. See `docs/BLUEPRINT.md` for the live status board and resume flags.

## [Unreleased]

### Added — live view (this branch)
- **Live app** (`web/index.html`, served at `/`): real Google Workspace sign-in (token client, `hd=ntxpllc.com`), NTXP-DOC-STANDARD 2.1
  look (navy band 1.00in, red accent fade, warm two-tone rows, centred cells / left paragraph columns), VIEW 1/3/5, click-to-reveal
  typable-then-checklist filters, proximity in miles, sortable headers, double-click inline edit with instant save, Google-style labels,
  blue hotlinks that become filters, animated hamburger → baby-blue REPORTS drawer, settings (dark mode, 4 palettes, template upload,
  council effectiveness), live full-size report document + DONE→PDF/Word via the NTXP engine, CSV, save to `!Active Projects`.
- **REST API** (`remote/api.py`): `/api/contacts|facets|report|report/render|report/custom|export.csv|council`, PATCH inline edits and labels
  (attributed in `change_log` as `ui:<email>` so they fan out through sync), exposure-gated, multi-value (checklist) filters.
- **Supabase support**: pooler-safe connections (prepared statements disabled for port 6543), deny-all RLS re-applied after every migration,
  `council_answers` table + `ntxp council-report` (consensus of effectiveness). Verified an `anon` role is denied.
- **Google Sheet mirror** (`sheets/`): Apps Script with domain gate, paging sync, NTXP-styled sheet, sidebar filters/reports, PDF-to-project-folder.
- **Hostinger deploy kit** (`deploy/`), **UI audit tool** (`tools/ui_audit.py`), geo helper for proximity (`geo.py`).

### Security
- Contact data is untrusted: escaped in the page; `<`/`>` stripped before the document-engine renderer; formula-injection guarded in the Sheet.
- Proprietary NTXP logo/engine are `.gitignore`d and served from deploy-time paths.

### Fixed (post-merge, from Codex review of #59)
- **Sweep recency**: re-seeing an old Gmail/Calendar/Drive record no longer bumps
  `last_seen_at` to now (`touch_source_record` preserves the data point's own
  date), so an old event stays correctly aged-out.
- **CardDAV exposure gate**: direct item `GET` and multiget `REPORT` now enforce
  `is_exposed`/`is_deleted`, not just the collection listing — a guessed/explicit
  `.vcf` can't leak a held-back or tombstoned contact.
- **CardDAV validators**: ctag/etag derive from the exposed set's size + newest
  revision (contact `updated_at`, bumped on real comms/field edits), so clients
  refetch after edits and visibility changes instead of caching stale vCards.
- **Reconcile churn**: `apply()` now skips an already-linked record whose
  `remote_hash` is unchanged — no redundant `change_log` write or fan-out.
- **DB override safety**: an explicit filesystem path to `--db`/the API forces
  SQLite and never falls through to `NTXP_DB_URL`, so a local command can't
  mutate the cloud database.

### Added
- **F2c — whitelisted connector middle-layer** (`connectors/*`, `docs/CONNECTORS.md`):
  service allowlist + alias mapper ingesting any connected account's contacts
  through the resolver/dedup pipeline; Zapier MCP as the secure broker (no secrets
  in repo). `ntxp connector-import` CLI; `connector_import` MCP tool.
- **F2b — mini model council** (`council/*`, `docs/COUNCIL.md`): JEV deterministic
  default decides for free; escalates to the cheapest available key-gated LLM judge
  (DeepSeek/Grok/OpenAI, env-overridable) only when uncertain; weighted vote with
  provenance. `ntxp council` CLI; `council_decide` MCP tool.
- **F2a — one-way iOS/iPhone contact sync** (`remote/vcard.py`, `remote/carddav.py`):
  vCard 3.0 rendering (exposure-gated) + a read-only CardDAV collection
  (OPTIONS/PROPFIND/REPORT/GET) mounted at `/carddav`, token-gated; `ntxp
  vcard-export` CLI. One-way by design — nothing writes back.
- **F1 — stateless cloud MCP 2.0 + OAuth + auto-hooks** (`remote/*`, `hooks/*`):
  streamable-HTTP MCP (FastMCP v1, stateless) with a pure-ASGI Bearer-token gate
  (`remote/auth.py`: Google Workspace OAuth / static / none); `remote/maps.py`
  live Google/Apple maps links + `locate_address` MCP tool; `remote/plugin.mcp.json`
  remote-MCP the plugin ships (install = register, zero setup beyond OAuth);
  `hooks/contact_context.py` UserPromptSubmit hook that injects contact cards,
  blue hotlinks, Maps links, and alternate-info previews; `ntxp serve-http` CLI;
  `remote` extra (mcp<2 + uvicorn). card() now carries address+maps+alternates.
- **Blueprint & handoff** (`docs/BLUEPRINT.md`) — staged flags + resume context so
  any model can continue mid-build.
- **Layer B — context hooks** (`context/hotlink.py`): `hotlink_text` wraps
  contacts/orgs/emails/phones in blue hotlinks; `contact_context` cards; CLI
  `context`/`hotlink`; MCP `contact_context`/`hotlink_text`.
- **Layers G/H/I — enrichment** (`enrich/*`, `docs/ENRICHMENT.md`): JEV-graded
  candidate pipeline; Gravatar/Libravatar/company-website/public-directory/LinkedIn
  resolvers; out-of-band OSINT (holehe/maigret/GHunt); `confirm_linkedin`
  (field + photo). CLI `enrich *`; MCP enrich tools; migration 0003.
- **Layer E — Workspace sweep** (`collect/workspace.py`): Gmail/Contacts/People/
  Calendar/Drive extractors tagged by channel + data-point date; `ntxp sweep`.
- **Layer F — JEV grading** (`qualify/grader.py`): source·recency·corroboration·
  distance grade + exposure/sync gate; `ntxp qualify`; migration 0002.
- **Layer A — delta reconciliation** (`sync/reconcile.py`, adapters): Lightfield-
  canonical hub; JobTread/QuickBooks/BuildingConnected; change-only; no-echo +
  fan-out; `ntxp reconcile`.
- **Layer C — dual-target DB** (`db/pg.py`): cloud PostgreSQL alongside embedded
  SQLite via `NTXP_DB_URL`; backend-aware migrations; `tsvector`+GIN FTS.
- **Layer D — user-facing page**: NTXP Contacts HTML artifact (banner, VIEW 1/3/5,
  inline edit, labels, hotlink→filter, sortable headers, REPORTS, Settings with
  dark mode + 4 palettes, exports).

### Validation
- Full suite: **51 tests pass** against SQLite and a real PostgreSQL 16 instance.

### Packaging
- Refreshed standalone installable plugin bundle (`ntxp-contacts-plugin.zip`,
  v0.3.0) with the full current package + auto hook + remote MCP config.

### Blocked (need external action)
- **M — mirror to NTXP Forge `ntxp-contacts`**: no repo access from this session
  (`not_found_or_no_access`). Needs the repo created + access granted, or the
  exact Forge owner/repo.
- Deploys: F1 cloud MCP + F2a CardDAV need the VPS + the Google OAuth app; F2b
  live LLM voting needs API keys; F2c live Zapier needs the user's Zapier auth.
