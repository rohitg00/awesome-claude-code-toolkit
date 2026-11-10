# NTXP Contacts Platform — Blueprint & Resume Flags

> **Handoff protocol.** This file is the single source of truth for the build.
> Any model resuming work reads this first, finds the first task not `DONE`,
> reads its **Resume** notes + linked files, and continues. Update the flag and
> the `CHANGELOG.md` entry when a task changes state. Flags:
> `TODO` · `IN_PROGRESS` · `DONE` · `BLOCKED(reason)`.

Repo: `ntxptrevor/awesome-claude-code-toolkit` · package: `contacts-db/ntxp_contacts`
· branch: `claude/contacts-database-consolidation-7aempk` · PR: #59.
Tests: `cd contacts-db && pytest` (set `NTXP_TEST_PG_URL` for the Postgres suite).

## Vision

One canonical, de-duplicated NTXP contacts database (SQLite local / PostgreSQL
cloud) that every NTXP tool reads and writes; Lightfield is the canonical hub;
all sources reconcile to it on change-deltas; a nightly Workspace sweep collects,
JEV grades, enrichment backfills, and a user-facing page + MCP + hooks expose it.

## Status board

| # | Layer / Feature | Flag | Files |
|---|---|---|---|
| D | User-facing HTML page | DONE | artifact `ntxp-contacts-page.html` |
| C | Dual-target cloud DB (SQLite/Postgres) | DONE | `db/pg.py`, `db/connection.py`, migrations |
| A | Delta two-way reconciliation | DONE | `sync/reconcile.py`, `sync/adapters.py`, `sync/engine.py` |
| E | Nightly Google Workspace sweep | DONE | `collect/workspace.py` |
| F | JEV qualification & grading | DONE | `qualify/grader.py` |
| G/H/I | Enrichment / photos / LinkedIn | DONE | `enrich/*`, `docs/ENRICHMENT.md` |
| B | Tool-agnostic context hooks | DONE | `context/hotlink.py` |
| **F1** | **Stateless cloud MCP 2.0 + OAuth + auto-hooks** | DONE (code) · BLOCKED(deploy) | `remote/*`, `hooks/*` |
| **F2a** | **One-way iOS/iPhone contact sync (CardDAV/vCard)** | DONE (code) · BLOCKED(deploy) | `remote/vcard.py`, `remote/carddav.py` |
| **F2b** | **Mini model council (JEV + cheap LLMs)** | DONE | `council/*`, `docs/COUNCIL.md` |
| **F2c** | **Whitelisted connector middle-layer (Zapier-style)** | DONE | `connectors/*`, `docs/CONNECTORS.md` |
| M | Mirror to NTXP Forge repo `ntxp-contacts` | BLOCKED(repo access) | scratchpad bundle ready |
| **L1** | **Live app at contacts.ntxpllc.cloud** (real Google OAuth, NTXP-DOC-STANDARD 2.1 tokens, full UI spec, live `/api`) | DONE (code) · BLOCKED(deploy) | `web/index.html`, `remote/api.py`, `remote/http_server.py` |
| **L2** | **Supabase as canonical DB + persisted council answers** (pooler-safe, RLS deny-all) | DONE (code) · BLOCKED(Supabase project) | `db/pg.py`, `db/migrations/runner.py`, `0004_council*.sql`, `council/router.py` |
| **L3** | **Google Sheet live mirror** (Apps Script, domain-OAuth ×2, menu/sidebar/reports) | DONE (logic tested) · UNVERIFIED in Google runtime | `sheets/*` |
| **L4** | **Hostinger deploy kit** (Docker + Caddy + deploy.sh) | WRITTEN · image NOT built (no Docker daemon here) | `deploy/*` |
| **L5** | **Front-end design audit** (standard + WCAG + axe, 52 checks) | DONE — 52/52 | `tools/ui_audit.py` |
| **P1** | **Interlinks: NTXP Schedules / Master Contracts / Form Fill** (signed outbound webhooks, inbound hooks, `/api/v1` autofill + context, Master Contracts watcher) | DONE (code) · Master Contracts integration tested against its REAL server · Schedules/Form Fill UNVERIFIED against the real apps | `peers/*`, `remote/peer_api.py`, `docs/INTEGRATIONS.md` |
| **P2** | **Shared-Supabase safety** (dedicated role+schema, scoped RLS lockdown, `SET LOCAL search_path` per txn) | DONE — verified on real PG incl. a neighbour-app canary | `db/pg.py`, `deploy/supabase_setup.sql` |
| **P3** | **Retarget to contacts.ntxpllc.cloud** (image from CI, existing proxy, mounted engine, runbook) | WRITTEN · NOT DEPLOYED (no Hostinger/Supabase/Docker access in session) | `deploy/*`, `.github/workflows/contacts-image.yml` |

---

## F1 — Stateless cloud-hosted MCP 2.0 + OAuth + auto-hooks  `DONE (code) · BLOCKED(deploy)`

**Built:** `remote/http_server.py` (stateless streamable-HTTP MCP via FastMCP v1 +
pure-ASGI `AuthMiddleware`), `remote/auth.py` (Google-Workspace OAuth-token verify,
`google|static|none` modes), `remote/maps.py` (Google/Apple maps links),
`remote/plugin.mcp.json` (remote MCP the plugin ships → install = register),
`hooks/contact_context.py` + `hooks/hooks.json` (UserPromptSubmit hook injects
contact cards, blue hotlinks, Maps links, alternate-info preview), `locate_address`
MCP tool, `ntxp serve-http` CLI, `remote` extra (`mcp<2`, uvicorn). Validated:
app builds, `/health` 200, unauthorized `/mcp` 401, hook injects context; 58 tests.
**Remaining (not code):** deploy to the VPS; register the Google OAuth app; set
`NTXP_MCP_URL`/token in the plugin config.

### Original plan (for reference)

**Intent.** An optional, cloud-hosted, stateless **streamable-HTTP MCP** that any
tool/skill/workflow can call for live company-contact access. Clicking it in
plugin settings (or asking for it) offers OAuth re-auth and auto-registers the
MCP in Claude's settings with **zero setup beyond OAuth**. Hooks auto-monitor
conversations for contact queries and inject contact data, blue hyperlinks, live
alternate-info previews, and live Maps location links for addresses.

**Steps.**
1. `remote/http_server.py` — wrap the existing FastMCP tools (`mcp_server.py`)
   with the streamable-HTTP transport; stateless (no server-side session needed;
   all state in the DB). `[ ]`
2. `remote/auth.py` — bearer-token verifier: validate a Google Workspace OAuth
   access token, require `hd == ntxpllc.com`. Pluggable; dev bypass via env. `[ ]`
3. `remote/plugin.mcp.json` — remote MCP entry (`type: http`, `url`,
   `headers: Authorization`) the plugin ships so install = register. `[ ]`
4. `hooks/` — `UserPromptSubmit` hook that detects contact-ish queries and calls
   `context.hotlink`/`enrich` to inject cards, hotlinks, Maps links, alt-info. `[ ]`
5. `remote/maps.py` — `maps_link(address)` → Google Maps URL. `[ ]`
6. Tests for auth gate, maps links, hook payload shaping. `[ ]`

**Resume context.** Reuse `mcp_server.build_server()`. FastMCP ≥1.0 exposes
`.run(transport="streamable-http")` / an ASGI app. Keep it **stateless** so it
scales on the VPS behind the agent proxy. OAuth = token *verification* (not a full
AS) for v1.

**Blockers to flag (not code):** hosting/deploy to the Hostinger VPS; the Google
OAuth app (client id/secret, redirect) under ntxpllc.com.

## F2a — One-way iOS/iPhone contact sync  `DONE (code) · BLOCKED(deploy)`

**Built:** `remote/vcard.py` (vCard 3.0 render + `export_vcards`, exposure-gated),
`remote/carddav.py` (read-only CardDAV: OPTIONS/PROPFIND/REPORT/GET, token-gated,
mounted at `/carddav` by `build_http_app`), `ntxp vcard-export` CLI. Validated:
vCard fields, held-back exclusion, CardDAV multistatus XML + vCard payloads, and
routing/auth through the full app. **Remaining:** deploy (same host as F1) + issue
per-user tokens. 65 tests.

### Original plan (for reference)

**Intent.** OAuth establishes a **one-way** (read-only) contact feed so a new
hire has company contacts on iOS day one.

**Steps.**
1. `remote/vcard.py` — render canonical contacts (exposed/graded only) to vCard
   3.0/4.0, incl. photo + org + title + labels. `[ ]`
2. `remote/carddav.py` — minimal **read-only CardDAV** collection (PROPFIND/REPORT)
   OR a signed `.vcf` subscription URL per user (simpler; iOS "Add Subscribed
   Contacts"-style via CardDAV). Token-scoped, one-way. `[ ]`
3. Respect the exposure gate: never emit `is_exposed=0` contacts. `[ ]`
4. Tests: vCard render + exposure filtering. `[ ]`

**Resume context.** CardDAV read-only is the clean iOS path; a per-user bearer
token grants access. No write-back (one-way by design).

**Blockers:** hosting + per-user token issuance (ties to F1 auth).

## F2b — Mini model council (JEV + cheap LLMs)  `DONE`

**Built:** `council/` — `JEVJudge` (free, deterministic, default decider) +
key-gated OpenAI-compatible `DeepSeekJudge`/`GrokJudge`/`OpenAIJudge`; router
escalates to the cheapest available judge only when JEV is uncertain, then
weighted-votes with provenance. Env-overridable models/endpoints (near-zero
maintenance). `ntxp council` CLI; `council_decide` MCP tool; `docs/COUNCIL.md`
cost/capability table. Runs for free with no keys. 70 tests. **Live LLM voting
needs API keys** (framework + JEV path need none).

### Original plan (for reference)

**Intent.** Near-zero-cost council that divides qualification/decision tasks
across JEV (deterministic, free) + cheap LLMs (Grok, DeepSeek, others). Try the
OpenAI Responses/decisions API if the feature set fits.

**Steps.**
1. Check existing `ntxp-model-council` skill; integrate, don't duplicate. `[ ]`
2. `council/base.py` — `Judge` protocol (`decide(task) -> {choice, confidence,
   cost}`), registry, cost table. `[ ]`
3. `council/judges.py` — `JEVJudge` (free default, wraps `qualify.score`);
   `GrokJudge`, `DeepSeekJudge`, `OpenAIJudge` — activate only when API keys
   present; else skipped. `[ ]`
4. `council/router.py` — route by task type + cost cap; cheapest-capable first,
   escalate on low confidence; majority/weighted vote. `[ ]`
5. A tiny bench harness + a cost/capability table in `docs/COUNCIL.md`. `[ ]`
6. Tests: routing, JEV-only path works with no keys, vote logic. `[ ]`

**Resume context.** Keep JEV as the zero-cost default so the council runs with no
keys. LLM judges are optional, key-gated, stateless HTTP calls.

**Blockers:** API keys for live LLM testing (framework + JEV path need none).

## F2c — Whitelisted connector middle-layer  `DONE`

**Built:** `connectors/base.py` (service allowlist via `NTXP_CONNECTOR_ALLOWLIST`,
`map_contact` alias mapper, `ingest_contacts` through the resolver/dedup pipeline,
`PermissionError` on disallowed services — no secrets in repo), `connectors/zapier.py`
(Zapier MCP as the broker). `ntxp connector-import` CLI; `connector_import` MCP
tool; `docs/CONNECTORS.md`. 75 tests. **Live Zapier pulls + push-back are
agent-driven/approval-gated** (outward-facing).

### Original plan (for reference)

**Intent.** A Zapier-like whitelisted layer so users securely connect accounts to
scrape / add / sync contacts across many services.

**Steps.**
1. `connectors/base.py` — `Connector` protocol (`list_contacts`, `push_contact`),
   allowlist of permitted services, per-user auth handle (token ref, never
   secrets in repo). `[ ]`
2. `connectors/zapier.py` — adapter over the Zapier MCP (`mcp__Zapier__*`) as the
   real middle layer; map Zapier actions → canonical records via existing
   adapters/`reconcile`. `[ ]`
3. Document the allowlist + security model in `docs/CONNECTORS.md`. `[ ]`
4. Tests: allowlist enforcement, canonical mapping. `[ ]`

**Resume context.** Zapier MCP is available in-session (`mcp__Zapier__*`). Live
workflow creation is outward-facing — build the framework + mapping now; gate
actual workflow creation on explicit user go-ahead.

**Blockers:** user's Zapier account auth; explicit approval before creating live
workflows.

## M — Mirror to NTXP Forge `ntxp-contacts`  `BLOCKED(repo access)`

Standalone installable plugin **bundle is refreshed** (scratchpad
`ntxp-contacts/` + `ntxp-contacts-plugin.zip`, v0.3.0): `.claude-plugin/plugin.json`
(hooks wired), `.mcp.json`, `hooks/hooks.json`, `skills/`, `commands/`,
`install.sh` (`pip install pysrc[mcp,remote,postgres]`), `pysrc/` = the full
current package (remote/hooks/council/connectors/collect/enrich/context/qualify/
sync).

**Blocked:** `check_repo_access ntxptrevor/ntxp-contacts` → `not_found_or_no_access`.
This session's GitHub scope is only `ntxptrevor/awesome-claude-code-toolkit`.
**To unblock:** create the repo and grant this session access (reconnect GitHub /
add the repo to the Claude GitHub App at github.com/settings/installations), or
tell me the exact NTXP Forge owner/repo. Then: `add_repo` → push `pysrc` + manifests
→ keep `contacts-db/` as upstream, mirror on release.
**Resume note for another model:** the zip is the deliverable; do not re-push a new
repo without the user confirming the Forge owner.

---

## Changelog pointer
See `CHANGELOG.md` for dated, shipped entries. Keep it in lockstep with the flags
above.


## Live view (L1–L5) — resume notes
**State:** all code built and tested; 109 Python tests (SQLite + PostgreSQL 16), 11 Apps Script tests (Node, mutation-checked),
28 browser e2e checks, 52 UI-audit checks, and every report type renders audit-clean through the real NTXP document engine.

**Remaining = external, not code:**
1. Supabase project → `NTXP_DB_URL` (then `ntxp init`; RLS lockdown applies automatically).
2. Google OAuth Web client (consent screen **Internal**) → `NTXP_GOOGLE_CLIENT_ID`; this is also where the real token exchange gets its first test.
3. Hostinger VPS + DNS A record → `deploy/deploy.sh /path/to/ntxp-branded-document-2`; first real Docker build.
4. Install the Apps Script (`sheets/README.md`) and run its first-run checklist in a real Workspace account.
5. Not yet built: JobTread job lookup for the Drive-folder save (it currently matches the *Project filter* to a folder name under `!Active Projects`);
   uploaded **PDF/Word** templates (only `.json` doc-engine specs are supported; the UI says so).

**Design decisions worth knowing:** brand assets/engine are proprietary → served from `NTXP_ASSETS_DIR`/`NTXP_DOC_ENGINE`, never committed;
reports default to portrait 8.5×11 (org rule) and drop the Title column there so emails never wrap (the engine audit fails otherwise);
the 4 palettes are an owner-directed UI feature — only the default (`ntxp`) equals the standard exactly.


## Interlinks + deploy retarget (P1–P3) — resume notes
**State:** code complete; 154 Python tests (152 on SQLite + PostgreSQL 16 + real doc engine, 2 more in the mcp venv), 11 Node tests, 28 browser e2e, 52 UI-audit checks.
**Not deployed.** The session had no Hostinger connector, Supabase project, Docker daemon or Google OAuth client. `contacts.ntxpllc.cloud` had no DNS record
on 2026-10-30. Follow `deploy/RUNBOOK.md` (it names the exact Hostinger tool calls and the confirmation gates).

**Facts that shaped the design (from the hostinger-ntxp-skill):** the VPS Docker Manager only *pulls* images (CI builds → GHCR); an existing proxy owns 80/443
(so no second Caddy; compose joins its network — RUNBOOK step 1 must confirm Traefik vs other); the proprietary NTXP engine/logo can't be in a registry
image (license) → bind-mounted from `/docker/ntxp-contacts/{engine,assets}`.

**Open items / next model start here:**
1. Real Schedules and Form Fill apps: implement the contract in `docs/INTEGRATIONS.md` (their code wasn't available) and run the first end-to-end test;
   if their auth/shape differs, adapt `peers/inbound.py` / `peer_api.py` (each is small). Get their real hostnames for `NTXP_PEERS`.
2. Master Contracts auth: we send `Bearer svc.contacts.<secret>`; its dev server has no auth — confirm what protects it on `.cloud` (`peers/contracts.py::_get`).
3. First real deploy: Supabase (`deploy/supabase_setup.sql`), Google OAuth client (Internal), DNS A record, GHCR package public, engine copy (RUNBOOK §3).
4. UI: contract/assignment facts surface via labels + cards; no dedicated panel in the page yet.
5. Still unbuilt from before: JobTread job lookup for the Drive save; PDF/Word template upload.
