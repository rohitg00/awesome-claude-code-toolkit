---
description: Query and manage the NTXP master contacts database
---

# NTXP Contacts

The NTXP contacts database is the single, de-duplicated source of truth for all
NTXP tools. It lives in `contacts-db/` (Python package `ntxp_contacts`) and
stores data in one SQLite file (`~/.ntxp/contacts.db`, override with
`NTXP_DB_PATH`).

## Setup

```bash
pip install -e contacts-db
ntxp init
```

## Common tasks

- **Search:** `ntxp query "<name | org | email>"`
- **Import a source:** `ntxp import <source> <file>` where source is
  `tips | buildingconnectd | approved_subs | luncheon | cjp_pdf`
- **Import everything from a folder:** `ntxp import all --all <dir>`
- **Stats / provenance:** `ntxp stats`
- **Export:** `ntxp export --format csv|json --out <file>`
- **Review near-duplicates:** `ntxp dedup review`, then `ntxp dedup merge <survivor> <loser>`
- **Regional cleanup:** `ntxp prune --source tips --keep-states TX,OK` — tombstone a source's members outside the given states (reversible; add `--dry-run` to preview, `--hard` to delete permanently)
- **CRM sync (dry-run):** `ntxp sync push --system <quo|lightfield> --dry-run`

Re-running an import is safe — unchanged rows are skipped and changed rows
update in place (no duplicates).

## Use from Claude tools (MCP)

Run `ntxp mcp-serve` to expose the DB as MCP tools (`search_contacts`,
`get_contact`, `upsert_contact`, `export_contacts`, `stats`, `sync_plan`,
`record_sync_result`). Register it via `mcp-configs/ntxp-contacts.json`.

When the user asks to look up, add, or reconcile a contact, prefer these tools
over re-parsing raw spreadsheets — this DB is the canonical store.
