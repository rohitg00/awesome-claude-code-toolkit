# NTXP API Log — Claude Skill

A Claude-installable skill that bundles the **NTXP API Log**: one shared,
encrypted registry of API endpoints, credentials (URL, key, key number, login),
and running cost — plus a CLI, an NTXP-branded dashboard with optional Google
sign-in, and an MCP server. See [`SKILL.md`](./SKILL.md) for how Claude uses it.

## What's in the installable `.zip`

```
ntxp-api-log/
  SKILL.md            skill instructions + YAML frontmatter (name, description)
  README.md           this file
  pyproject.toml      installs the `ntxp-apilog` CLI + ntxp_apilog package
  requirements.txt    runtime deps (click, cryptography; mcp optional)
  ntxp_apilog/        the package (cli, server, dashboard, mcp_server, crypto, auth, db)
  apilog.db           a pre-initialized (migrated, empty) SQLite database
```

> The bundled `apilog.db` ships **empty** (schema only) — no credentials are
> included. Encryption keys are generated locally on first use and are never
> bundled.

## Install

**Claude.ai / Claude Desktop:** upload `ntxp-api-log-skill.zip` in the skills
UI (Settings → Capabilities → Skills → upload).

**Claude Code:** unzip into your skills directory (e.g.
`~/.claude/skills/ntxp-api-log/`), or add this repo as a plugin marketplace.

Then, from the skill directory:

```bash
pip install -e .
export NTXP_APILOG_DB_PATH="$(pwd)/apilog.db"
ntxp-apilog list           # works immediately (empty registry)
ntxp-apilog serve          # open the dashboard
```

## Rebuild the `.zip`

The package source of truth lives in `api-log-db/` at the repo root. To
re-assemble the installable zip (bundling the latest package + a fresh empty DB):

```bash
skills/ntxp-api-log/build.sh
```

It stages `SKILL.md`, `README.md`, the `ntxp_apilog` package, install metadata,
and a freshly migrated `apilog.db`, then writes `ntxp-api-log-skill.zip`.

## Security notes

- Secret fields are Fernet-encrypted at rest; set one shared `NTXP_APILOG_KEY`
  across everyone sharing the database.
- The dashboard binds to loopback unless you enable Google sign-in; serve it
  behind TLS when exposed, since it carries credentials and session cookies.
- Never commit a populated `apilog.db` or the key file (both are gitignored).
