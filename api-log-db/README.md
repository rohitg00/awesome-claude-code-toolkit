# NTXP API Log

One **shared registry of every API** used across NTXP tools — base URL, key
number, login info, and running cost — in a single SQLite file that any tool can
read, update, and (crucially) that **Claude can query and fill in automatically**
the moment a system, skill, or user needs an API.

- **Single source of truth** — one SQLite DB (`~/.ntxp/apilog.db` by default;
  point `NTXP_APILOG_DB_PATH` at a shared/synced location so everyone uses one).
- **Encrypted secrets** — API keys, key numbers, and console passwords are
  stored as Fernet ciphertext, not plaintext.
- **Audited reveals** — every time a live credential is read (CLI `--reveal`,
  dashboard reveal, or Claude's `get_credentials`) it is written to an access log.
- **Cost tracking** — append-only usage log gives a live spend total per API and
  per month.
- **Four access layers over one core library** — Python API, the
  `ntxp-apilog` CLI, an **NTXP-branded HTML dashboard**, and an **MCP server** so
  Claude-based tools query the registry directly.

> **Security:** this directory ships **code only**. The built `.db`, the
> encryption key, and any exports are gitignored and never committed.

## Install

```bash
pip install -e api-log-db                # core (CLI + dashboard + crypto)
pip install -e "api-log-db[mcp,dev]"     # + MCP server, tests
```

## Quick start

```bash
ntxp-apilog gen-key                      # mint an encryption key (see below)
export NTXP_APILOG_KEY=<the value>       # set on every machine sharing the DB
ntxp-apilog init                         # create DB + run migrations

ntxp-apilog add OpenAI \
  --provider "OpenAI, Inc." --category llm \
  --base-url https://api.openai.com/v1 \
  --auth-type bearer --api-key sk-live-xxxx \
  --cost-model "\$0.01 / 1K tokens" --monthly-budget 200 \
  --purpose "LLM completions for NTXP skills" --owner you@ntxp.com

ntxp-apilog list                         # masked overview + spend
ntxp-apilog search "llm"                 # full-text search
ntxp-apilog log-cost OpenAI 1.25 --units 125000 --unit-kind tokens
ntxp-apilog serve                        # open the dashboard (http://127.0.0.1:8787)
```

## The dashboard

`ntxp-apilog serve` launches the NTXP-branded single-page dashboard. It shows
every API with stat cards (count, total spend, top spend), a searchable/filterable
table, masked secrets with an audited **reveal/copy**, an add/edit form, a
**+ Cost** logger, and soft delete.

It binds to **loopback (`127.0.0.1`) by default** because it serves live
credentials.

### Sharing the dashboard with Google sign-in

To let a team **share one dashboard** over the network, turn on Google OAuth and
restrict it to an email/domain allowlist. With it enabled, every route requires a
signed-in, allow-listed Google account; audited reveals are attributed to the
signed-in user (`user:<email>`).

1. In Google Cloud Console, create an **OAuth 2.0 Client ID** (type: Web
   application) and add the redirect URI the server prints at startup
   (e.g. `https://apilog.ntxp.com/auth/callback`).
2. Set the env vars and run:

```bash
export NTXP_APILOG_GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
export NTXP_APILOG_GOOGLE_CLIENT_SECRET=xxxx
export NTXP_APILOG_ALLOWED_DOMAIN=ntxp.com      # and/or NTXP_APILOG_ALLOWED_EMAILS
export NTXP_APILOG_OAUTH_REDIRECT=https://apilog.ntxp.com/auth/callback
export NTXP_APILOG_HTTPS=1                       # mark the session cookie Secure
ntxp-apilog serve --host 0.0.0.0 --port 8787
```

Auth routes: `/auth/login` (→ Google), `/auth/callback`, `/auth/logout`,
`/auth/me`. Sessions are HttpOnly cookies (12 h). **Off by default** — with no
client id/secret set, the dashboard runs loopback-only with no login.
Serve it behind TLS (a reverse proxy) since it carries credentials and cookies;
without an allowlist *any* Google account can sign in (the server warns).

## How Claude "fills it in" (MCP)

Run `ntxp-apilog mcp-serve` to expose the registry as MCP tools, and register it
via [`mcp-configs/ntxp-apilog.json`](../mcp-configs/ntxp-apilog.json). The
companion rule [`rules/api-credentials.md`](../rules/api-credentials.md) tells
Claude to consult the log **before** asking a user for a URL or key.

| Tool | Purpose |
|---|---|
| `find_api(query)` | Search the log; returns metadata + masked previews + `has_api_key`. |
| `get_api(name_or_id)` | Full metadata for one API (masked, not audited). |
| `get_credentials(name_or_id, requested_by, purpose)` | **The fill-it-in path** — reveals URL + key/login + ready `auth_header`. Audited. |
| `upsert_api(...)` | Register/update an API discovered during a task. |
| `log_usage(name_or_id, cost, …)` | Record a cost event so the spend total stays live. |
| `stats()` | Counts by status/category and spend by API/month. |

**The loop:** a skill needs to call the Stripe API → Claude calls
`find_api("stripe")` → if present, `get_credentials("Stripe", requested_by="skill:invoice-reconciliation")`
returns the base URL and key to drop straight into the request → after the call,
`log_usage("Stripe", 0.02, …)`. If the API isn't on file, Claude `upsert_api`s it
so the next request reuses it.

## Architecture

```
ntxp_apilog/
  config.py            DB path, key path, dashboard host/port, vocabularies
  crypto.py            Fernet encrypt/decrypt/mask; key from env or 0600 file
  model.py             ApiEntry / UsageEvent dataclasses + name normalization
  db/                  connection (WAL/FK), repository (all SQL + FTS), migrations
  cli.py               the `ntxp-apilog` command
  server.py            stdlib HTTP server: dashboard + JSON API + OAuth gate
  auth.py              Google OAuth login (config, allowlist, sessions)
  dashboard/index.html NTXP-branded single-page dashboard
  mcp_server.py        FastMCP tools (find/get/get_credentials/upsert/log_usage/stats)
```

### Schema (migration `0001`)

- **`apis`** — the registry. Secret columns (`api_key_enc`, `key_number_enc`,
  `login_secret_enc`) hold ciphertext; `name_norm` is the unique merge key.
- **`usage_log`** — append-only cost/usage events (drives spend totals).
- **`access_log`** — audit trail of every credential reveal/fill (who, why, when).
- **`apis_fts`** — FTS5 index over name/provider/purpose/tags/category.

## Encryption & key management

Secrets are encrypted with a symmetric Fernet key resolved in this order:

1. `NTXP_APILOG_KEY` (a urlsafe-base64 32-byte key) — **recommended for shared DBs**.
2. Otherwise an auto-generated key file at `~/.ntxp/apilog.key` (0600).

For a shared database, generate one key (`ntxp-apilog gen-key`) and set
`NTXP_APILOG_KEY` to it on every machine/tool — otherwise each host mints its own
key and cannot decrypt the others' secrets.

## Configuration

| Env var | Purpose | Default |
|---|---|---|
| `NTXP_APILOG_DB_PATH` | Shared DB file location | `~/.ntxp/apilog.db` |
| `NTXP_APILOG_KEY` | Fernet encryption key (preferred) | — |
| `NTXP_APILOG_KEY_PATH` | Key file location (fallback) | `~/.ntxp/apilog.key` |
| `NTXP_APILOG_GOOGLE_CLIENT_ID` | Google OAuth client id (enables sign-in) | — |
| `NTXP_APILOG_GOOGLE_CLIENT_SECRET` | Google OAuth client secret | — |
| `NTXP_APILOG_OAUTH_REDIRECT` | OAuth redirect URI | `http://<host>:<port>/auth/callback` |
| `NTXP_APILOG_ALLOWED_EMAILS` | Comma-separated allowed emails | — |
| `NTXP_APILOG_ALLOWED_DOMAIN` | Allowed Google hosted domain | — |
| `NTXP_APILOG_HTTPS` | Mark the session cookie `Secure` | unset |

## Tests

```bash
pytest api-log-db/tests
```
