---
description: Query and manage the NTXP shared API Log (URLs, credentials, cost)
---

# NTXP API Log

The NTXP API Log is the single shared registry of every API used across NTXP
tools — base URL, key number, login info, and running cost. It lives in
`api-log-db/` (Python package `ntxp_apilog`) and stores data in one SQLite file
(`~/.ntxp/apilog.db`, override with `NTXP_APILOG_DB_PATH`). Secret fields are
encrypted at rest.

## Setup

```bash
pip install -e "api-log-db[mcp]"
ntxp-apilog gen-key                  # mint a key; export NTXP_APILOG_KEY=<value>
ntxp-apilog init
```

## Common tasks

- **Register/update an API:** `ntxp-apilog add <Name> --base-url … --api-key … --cost-model …`
- **List (masked) + spend:** `ntxp-apilog list [--status active] [--category llm]`
- **Search:** `ntxp-apilog search "<name | provider | purpose | tag>"`
- **Show (audited reveal):** `ntxp-apilog show <name|id> --reveal --accessor you@ntxp.com`
- **Log a cost:** `ntxp-apilog log-cost <name|id> <cost> --units N --unit-kind tokens`
- **Stats / spend:** `ntxp-apilog stats`
- **Dashboard:** `ntxp-apilog serve` → http://127.0.0.1:8787

## Use from Claude tools (MCP)

Run `ntxp-apilog mcp-serve` to expose the registry as MCP tools (`find_api`,
`get_api`, `get_credentials`, `upsert_api`, `log_usage`, `stats`). Register it via
`mcp-configs/ntxp-apilog.json`.

When a **system, skill, or user** needs an API, consult this log **before**
asking for a URL or key (see `rules/api-credentials.md`):

1. `find_api("<service>")` → check if it's on file.
2. `get_credentials(name, requested_by="skill:…", purpose="…")` → fill the URL +
   key/login straight into the request (audited).
3. `upsert_api(...)` to register anything new; `log_usage(...)` to track spend.
