---
name: anywrite
description: Drive Anytype from the CLI — create/update/search notes, tasks, and PKM objects, manage spaces, properties, tags, types, templates, lists, files, chat, and members via all 52 endpoints of the Anytype local API in one compiled binary
---

# anywrite

`anywrite` is a compiled Bun/TypeScript CLI that talks to the Anytype desktop app's local HTTP API (`http://localhost:31009` by default). It covers all 52 endpoints of the Anytype local API spec (2025-11-08) — spaces, objects, properties, tags, types, templates, lists, chat, files, members, search, and auth — as a single binary with zero dependencies and no MCP server. Anytype desktop must be running for any command to work.

## Auth

```bash
anywrite auth --status          # shows configured yes/no + active source, never the key itself
anywrite auth                   # starts the challenge flow: a 4-digit code pops up in Anytype desktop
anywrite auth --code 1234       # completes the exchange, writes ~/.anywrite/config.json
```

Config precedence: `ANYTYPE_API_KEY` env var → `~/.anywrite/config.json` → a read-only fallback to an existing `anytype-cli` key, if present. The API key is never printed or logged.

## Command shape

```bash
anywrite <resource> <action> [positionals] [--flag value]

anywrite --help                 # lists all resources
anywrite objects --help         # actions + generated flags for one resource
```

Positionals for `space`/`type`/`property` accept either a **name or an id** — the CLI resolves names to ids automatically. Useful global flags: `--all` (paginate the full result set), `--pretty` (table view), `--json '<raw>'` (merge a raw JSON body, needed for search filters and `lists add`), `--property key=value` (format-aware, repeatable), `--file <path>` (upload), `--follow` (consume an SSE chat stream).

## Workflows

**Create structured content** — property → tags → type → objects → verify:
```bash
anywrite properties create <space> --format select --name Stage
anywrite tags create <space> stage --color yellow --name Backlog
anywrite types create <space> --layout action --name Ticket --plural_name Tickets
anywrite objects create <space> --type ticket --name "Wire auth" --property stage=Backlog --body "notes"
anywrite verify <space> <object_id> --property stage=Backlog --pretty
```

**Find and update by property** — tag id → filtered search → update → verify:
```bash
anywrite tags list <space> stage --pretty   # filters need the tag ID, not the name
anywrite search space <space> --all --json '{"types":["ticket"],"filters":{"operator":"and","conditions":[{"property_key":"stage","condition":"eq","select":"<tag_id>"}]}}'
anywrite objects update <space> <hit_id> --property stage=Shipped
anywrite verify <space> <hit_id> --property stage=Shipped --pretty
```

## Quick reference — 12 resources

```bash
# spaces
anywrite spaces list
anywrite spaces create --name "My Space"

# objects
anywrite objects list <space> --all
anywrite objects create <space> --type task --name "Buy milk" --body "notes here"
anywrite objects update <space> <object_id> --markdown "..." --status "Done"
anywrite objects delete <space> <object_id>          # archives (soft delete)

# properties / tags / types
anywrite properties create <space> --format select --name Priority
anywrite tags create <space> <property_id> --color red --name Urgent
anywrite types create <space> --layout basic --name Task --plural_name Tasks

# templates (read-only)
anywrite templates list <space> <type_id>

# lists (add/remove only work on collections, not sets)
anywrite lists add <space> <list_id> --json '{"objects":["obj_id_1","obj_id_2"]}'
anywrite lists objects <space> <list_id> <view_id>

# files
anywrite files upload <space> --file /path/to/image.png
anywrite files download <space> <file_id> --output /path/to/save.png

# members (read-only)
anywrite members list <space>

# search — structured filters/sort go in the --json body
anywrite search global --query "task" --types task
anywrite search space <space> --query "task" --json '{"types":["task"]}'

# chat
anywrite chat send <space> <chat_id> --text "hello"
anywrite chat messages <space> <chat_id> --all
anywrite chat stream <space> <chat_id> --follow   # SSE, one JSON line per event

# verify — composite client-side check after a batch mutation
anywrite verify <space> <object_id...> --property status="To Do" --pretty
```

## Notes (all live-verified against the running Anytype desktop)

- **The body flag differs by action.** `objects create` takes `--body`, `objects update` takes `--markdown`, and `objects get` returns content under `markdown`. Using the wrong flag silently ignores the content.
- **Property flags are `--status` and `--property` only** — there is no per-property generated flag. An unknown flag is silently ignored, producing a successful create with the property simply missing.
- **Search filters need the tag ID; `--property` takes the name.** Inside a `--json` filter body the API wants raw ids — a tag name returns a 400. Look the id up with `tags list` first.
- **`lists add`/`lists remove` only work on collections**, not sets (sets are query-driven and read-only for membership).
- **Delete is a soft archive everywhere and is idempotent** — deleting twice returns `archived: true` both times, never a 410.
- **Object bodies round-trip semantically, not byte-identically** (code-fence language tags drop, blank lines collapse). Check key content instead of string-diffing a body to verify a write.
- **Platform ceilings — no endpoint exists**, so the CLI can't do them: block-level editing, member invite/role management, template create/update/delete, and space deletion.

## Errors

Any 4xx/5xx from the API prints the response body verbatim to stderr and exits 1. A usage error (unknown resource/action, missing required flag, an unresolvable name) exits 2 with a short message and makes no API call.
