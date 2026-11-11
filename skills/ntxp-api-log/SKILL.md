---
name: ntxp-api-log
description: Look up, register, and fill in API endpoints/credentials/cost from the shared NTXP API Log. Use whenever a system, skill, or user needs an API's base URL, key, key number, or login — consult this log BEFORE asking the user for a credential. Also use to register a newly discovered API, record usage/cost, or open the NTXP-branded dashboard. Bundles the ntxp_apilog Python package, an NTXP-branded dashboard with optional Google sign-in, an MCP server, and a pre-initialized SQLite database.
---

# NTXP API Log

One **shared, encrypted registry** of every API used across NTXP tools — base
URL, key number, login info, and running cost — with a CLI, an NTXP-branded
dashboard (optional Google sign-in), and an MCP server. This skill bundles the
`ntxp_apilog` package and a pre-initialized `apilog.db` so it works as soon as
it's installed.

**The core behavior:** when you need an API, look it up here and *fill it in*
instead of stopping to ask the user for a URL or key.

## Setup (once)

From the skill directory:

```bash
pip install -e .              # installs ntxp_apilog + the `ntxp-apilog` CLI
# (or: pip install -r requirements.txt && pip install -e .)
```

The bundled `apilog.db` is already migrated. To use it, point the tools at it
(or copy it to the shared location):

```bash
export NTXP_APILOG_DB_PATH="$(pwd)/apilog.db"   # this skill's bundled DB
# For a team, point this at a synced/shared file and set ONE shared key:
ntxp-apilog gen-key            # prints a Fernet key
export NTXP_APILOG_KEY=<the value>   # set the SAME key everywhere sharing the DB
```

Secrets (API keys, key numbers, login passwords) are **encrypted at rest** with
`NTXP_APILOG_KEY` (or an auto-generated `~/.ntxp/apilog.key`). Use the same key
on every machine/tool that shares the database, or they can't decrypt each
other's secrets.

## When an API is requested (the fill-it-in loop)

1. **Search first** — before asking the user for anything:
   ```bash
   ntxp-apilog search "<service or purpose>"     # e.g. "stripe", "llm", "maps"
   ```
2. **Reveal credentials** to drop into the request (audited):
   ```bash
   ntxp-apilog show "<name or id>" --reveal --accessor "skill:<name>" --purpose "<why>"
   ```
   Use the returned `base_url` + `api_key`/`login_*` to build the live call.
   Never echo a revealed secret back into chat, a file, or a commit.
3. **Register** anything new so the next request reuses it:
   ```bash
   ntxp-apilog add "<Name>" --provider "<vendor>" --category <cat> \
     --base-url <url> --auth-type bearer --api-key <key> \
     --cost-model "<$/unit>" --purpose "<what it's for>"
   ```
4. **Record cost** after using an API on someone's behalf:
   ```bash
   ntxp-apilog log-cost "<name or id>" <cost> --units <n> --unit-kind tokens \
     --requested-by "skill:<name>"
   ```

Other commands: `ntxp-apilog list`, `ntxp-apilog stats`, `ntxp-apilog export`.

## Dashboard

```bash
ntxp-apilog serve            # http://127.0.0.1:8787 (loopback)
```

NTXP-branded SPA: stat cards, searchable table, masked secrets with audited
reveal/copy, add/edit form, cost logging, soft delete. To share it on a network,
enable Google sign-in (see below) and serve behind TLS.

### Optional: Google sign-in (to share the dashboard)

Off by default. Create an OAuth 2.0 Web client in Google Cloud, add the redirect
URI the server prints, then:

```bash
export NTXP_APILOG_GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
export NTXP_APILOG_GOOGLE_CLIENT_SECRET=xxxx
export NTXP_APILOG_ALLOWED_DOMAIN=ntxp.com        # and/or NTXP_APILOG_ALLOWED_EMAILS
export NTXP_APILOG_HTTPS=1
ntxp-apilog serve --host 0.0.0.0
```

Only allow-listed Google accounts can then reach the registry; reveals are
attributed to the signed-in user.

## Use from Claude tools (MCP)

```bash
ntxp-apilog mcp-serve        # stdio MCP server
```

Tools: `find_api`, `get_api`, **`get_credentials`** (the fill-it-in path,
audited), `upsert_api`, `log_usage`, `stats`. Register the server in your MCP
config (`command: ntxp-apilog`, `args: ["mcp-serve"]`) and set
`NTXP_APILOG_DB_PATH` + `NTXP_APILOG_KEY` in its env. Prefer these tools over
re-asking the user — this DB is the canonical store.

## Files in this skill

- `SKILL.md` — this file
- `README.md` — install & packaging notes
- `ntxp_apilog/` — the Python package (CLI, dashboard, MCP, crypto, OAuth)
- `pyproject.toml`, `requirements.txt` — install metadata
- `apilog.db` — pre-initialized (migrated, empty) SQLite database
