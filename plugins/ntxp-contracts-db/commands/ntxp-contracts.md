---
description: Query and manage the NTXP Master Contracts database
---

# NTXP Master Contracts

The Master Contracts database is the single, adaptable, pollable source of truth
for every contract NTXP works under — **Job Order Contracts, Cooperative
Contracts, and Master Subcontract Agreements**. It lives in `contracts-db/`
(Python package `ntxp_contracts`) and stores data in one SQLite file
(`~/.ntxp/contracts.db`, override with `NTXP_CONTRACTS_DB`).

Each entry tracks: contract title, contract/RFP #, type, location, estimated
budget, owner entity, recipient (defaults to **NTXP LLC**), award date,
duration, expiration date, coefficient multiplier, cooperative fee, allowable
scope terms, notes, a live link to the signed PDF, and an **executed flag**
(unexecuted copies are flagged everywhere).

## Setup

```bash
pip install -e contracts-db          # core has no third-party deps
ntxp-contracts init
```

## Common tasks

- **Editable dashboard (employees):** `ntxp-contracts serve-web` →
  http://127.0.0.1:8787/ — inline-editable contract log, instant save, multiple
  concurrent editors, Print / Download-PDF on Letter (8.5×11). Click a contract
  number to open its profile.
- **Add / update:** `ntxp-contracts add "Title" --number RFP-1 --type "Job Order Contract" --owner "TIPS USA"`
- **Import a CSV log (idempotent):** `ntxp-contracts import contract-log.csv`
- **Search:** `ntxp-contracts query "electrical"`
- **Profile (terms + owner contact + jobs/sales):** `ntxp-contracts show <id>`
- **Brand resolved from Claude settings:** `ntxp-contracts brand`

## Use from Claude tools (MCP)

Run `ntxp-contracts mcp-serve` to expose the DB as MCP tools
(`search_contracts`, `get_contract`, `reference_lookup`, `list_expiring`,
`upsert_contract`, `update_field`, `sync_jobs`, `stats`, `get_brand`). Register
it via `mcp-configs/ntxp-contracts.json`.

When the user asks about a contract's coefficient, cooperative fee, expiration,
allowable scope, the signed copy, or jobs/sales under it, prefer
`reference_lookup` / `get_contract` over re-reading spreadsheets — this DB is
the canonical store.

### Jobs / sales roll-up (JobTread)

The per-contract profile shows jobs done under the contract and total sales.
Pull those rows from the **JobTread** MCP, then cache them with `sync_jobs`
(MCP) or `POST /api/contracts/<id>/jobs` (web). The cache is what every other
tool then polls.

### Branding

Screens style themselves from the **most up-to-date brand skill** found in
Claude's settings at request time (`~/.claude/skills`, project `skills/`,
managed `/mnt/skills`, …), preferring an NTXP-specific brand skill. Update the
brand skill and every screen follows on next load — nothing is hard-coded.
