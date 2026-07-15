---
name: sshepherd
description: Zero-knowledge remote server operations over SSH — health checks, docker/systemd control, log tailing, config edits, read-only Postgres introspection, and declarative deploys — without the agent ever seeing a password, key, host, user, or port
---

# sshepherd

`sshepherd` is a compiled Bun/TypeScript CLI for operating a real server over SSH — built so an AI agent can drive the box without ever seeing a password, private key, hostname, username, or port. Every operation resolves through an ssh alias already configured in `~/.ssh/config` (or a db pg-target / deploy recipe name that itself resolves to an alias); OpenSSH performs the actual authentication, entirely outside the process. The CLI shells out to the system `ssh` binary, never the `ssh2` npm library, so credential handling stays inside OpenSSH's own trusted code path.

## The zero-knowledge model

The agent passes only a **name** — an ssh alias (`lms-server`), a pg-target (`prod`), or a recipe (`demo`) — never a connection tuple. There is no flag to pass a raw host/user/port/password. Every response envelope echoes back only the alias it was given; there is no host/user/port field anywhere in the response shape. ssh's own stderr is discarded and classified into a small error enum instead, because OpenSSH's stderr phrasing can leak a hostname no redaction allowlist would catch. `.env`-shaped files are masked by default (`KEY=***MASKED***`) unless the agent passes `--reveal KEY1,KEY2`, and `files download` writes remote bytes straight to a local path without ever returning content in the JSON envelope.

## Command shape

```bash
sshepherd <group> <action> [positionals...] [--flag value]

sshepherd --help                    # lists the 9 registry groups + setup
sshepherd <group> --help            # a group's actions + args/flags
sshepherd <group> <action> --help   # one action's args
```

Output is JSON to stdout by default (one envelope per call). Exit codes: `0` success, `1` the op ran and failed (transport/command error or a refused `CONFIRMATION_REQUIRED`), `2` a usage error (no ssh connection attempted).

The first positional differs by group: `db` uses a pg-target name, `deploy` uses a recipe name, `hosts list` / `db list` take none (host-local), and every other group takes an ssh alias.

## Global flags

| Flag | Effect |
|---|---|
| `--yes` | confirm a mutating op — required; sshepherd never prompts interactively |
| `--dry-run` | `deploy run` only: print the resolved plan, execute nothing |
| `--pretty` | render a human table/key-value view instead of JSON |
| `--reveal <keys>` | `files cat` only: comma-separated env keys to unmask |
| `--from <path>` | `config put` only: local file to read + base64-encode |

## The 9 registry-driven groups (52 ops)

```bash
# hosts — alias names only, never host/user/port
sshepherd hosts list
sshepherd hosts test lms-server
sshepherd hosts info lms-server

# check — health snapshots
sshepherd check overview lms-server
sshepherd check mem lms-server
sshepherd check disk lms-server
sshepherd check cpu lms-server
sshepherd check ports lms-server
sshepherd check oom-history lms-server
sshepherd check kernel lms-server

# logs
sshepherd logs docker lms-server lms-app --tail 100
sshepherd logs service lms-server nginx --tail 100
sshepherd logs docker-daemon lms-server --tail 100
sshepherd logs nginx lms-server error --tail 100

# services — docker + systemd
sshepherd services ps lms-server
sshepherd services stats lms-server
sshepherd services inspect lms-server lms-app
sshepherd services compose-ps lms-server /opt/lms/docker-compose.yml
sshepherd services healthcheck lms-server lms-app
sshepherd services systemctl-status lms-server nginx
sshepherd services restart lms-server lms-app --yes
sshepherd services systemctl-start lms-server nginx --yes
sshepherd services systemctl-stop lms-server nginx --yes
sshepherd services systemctl-restart lms-server nginx --yes
sshepherd services systemctl-reload lms-server nginx --yes

# files — .env masked by default
sshepherd files ls lms-server /opt/lms
sshepherd files cat lms-server /opt/lms/.env --reveal DB_HOST
sshepherd files tail lms-server /var/log/syslog --n 100
sshepherd files download lms-server /opt/lms/backup.sql ./backup.sql
sshepherd files disk-usage lms-server /var/lib/docker
sshepherd files upload lms-server ./local.conf /opt/lms/local.conf --yes

# config — backs up before writing, allowlist-gated
sshepherd config get lms-server /etc/nginx/nginx.conf
sshepherd config validate lms-server /etc/nginx/nginx.conf
sshepherd config put lms-server /etc/nginx/nginx.conf --from ./nginx.conf --yes
sshepherd config reload lms-server nginx --yes

# db — Postgres, read-only, single SELECT
sshepherd db list
sshepherd db tables prod
sshepherd db activity prod
sshepherd db connections prod
sshepherd db slow prod
sshepherd db size prod
sshepherd db query prod "SELECT count(*) FROM users"

# deploy — declarative TOML recipes
sshepherd deploy run demo --dry-run
sshepherd deploy run demo --yes
sshepherd deploy status demo
sshepherd deploy rollback demo --yes
sshepherd deploy logs demo --tail 100
sshepherd deploy migrate demo --yes

# security
sshepherd security harden lms-server --yes
sshepherd security ssh-audit lms-server
sshepherd security listeners lms-server
sshepherd security authorized-keys lms-server
sshepherd security fail2ban lms-server
```

A separate `setup` group (not one of the 9) writes sshepherd's own local config — registering ssh aliases, scaffolding pg-targets, allowlists, and deploy recipes. Every setup action is agent-invocable and `--yes`-gated, with one narrow exception: `setup ssh-alias install` opens a one-shot local browser form that only a human can type a password into — the password goes straight into `sshpass`'s stdin and never crosses back into the agent's context.

## Notes

- **No raw exec, ever.** There is no `sshepherd exec "<command>"`. A novel need is authored as a named, versioned recipe step — reviewable, not a free-text shell escape hatch.
- **Every mutating op needs `--yes` and writes an audit line** (`~/.local/state/sshepherd/audit.jsonl`) — timestamp, alias, command, an arg hash, and outcome — on success and failure alike.
- **`config put` always backs up first**, copying the existing file to `<path>.bak-<UTC-timestamp>` in the same round trip, and refuses any path not on that alias's allowlist.
- **`db query` takes a single SELECT** wrapped in `BEGIN TRANSACTION READ ONLY`; the real boundary is a read-only DB role on the target, with client-side checks as UX guardrails.
- **`security harden` won't lock out the current session** unless `--keep-session=false` is passed — directives that could disable the session's own auth method are held back by default.
