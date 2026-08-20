# NTXP Master Contracts Database

One **adaptable, modular master contracts database** for all NTXP tools.
Every contract NTXP works under — a **Job Order Contract**, a **Cooperative
Contract**, or a **Master Subcontract Agreement** — lives as one entry in a
single SQLite file that any tool can poll for reference data, and that
employees edit through a browser dashboard.

- **Single source of truth** — one SQLite DB (`~/.ntxp/contracts.db` by default).
- **Pollable by other tools** — Python API, `ntxp-contracts` CLI, and an MCP
  server so Claude-based NTXP tools read coefficient, fee, expiration, scope,
  the signed PDF link, owner-entity contact info, and jobs/sales directly.
- **Adaptable / modular** — query/display fields are columns; anything extra
  lives in a JSON `attrs` bag, so the schema stays stable as needs grow.
- **Idempotent imports** — re-importing a CSV log never duplicates.
- **Zero third-party deps in the core** (stdlib `sqlite3` + `http.server`);
  `mcp` is an optional extra only for the MCP server.

> **Privacy:** this directory ships **code only**. Real contract data, the
> built `.db`, and signed PDFs are gitignored and never committed.

## Each entry tracks

Contract title · contract / RFP # · type · location · estimated budget · owner
entity · recipient (**defaults to NTXP LLC**) · award date · duration ·
expiration date · coefficient multiplier · cooperative fee · allowable scope
terms (electrical, trade work, GC, professional services, painting, …) · notes
· **live link to the signed PDF** · **executed flag** (unexecuted copies are
flagged everywhere).

## Install

```bash
pip install -e contracts-db                 # core (no third-party deps)
pip install -e "contracts-db[mcp,dev]"      # + MCP server, tests
ntxp-contracts init                         # create DB + run migrations
```

## The employee dashboard

```bash
ntxp-contracts serve-web                    # http://127.0.0.1:8787/
```

- **Click any cell to edit — it saves instantly.** No popups, no dialogs, no
  jargon. Stays on the same page.
- The log shows the fields that matter at a glance: **contract #**, title, type,
  owner, **coefficient**, **co-op fee**, **expiration** (color-coded when
  expiring/expired), scope, signed-PDF link, and the **executed / unexecuted**
  flag (one click to toggle).
- **Multiple users can edit at once without conflict.** Every save is a
  single-field `PATCH` carrying the row revision: different cells never collide,
  and the page polls for teammates' saves and merges them in without disturbing
  the cell you're in. (WAL-mode SQLite handles concurrent writes.)
- **Print** and **Download PDF** buttons both export the log on **Letter
  (8.5 × 11)** via a dedicated print stylesheet.
- **Click a contract number** to open its **profile screen** (below).

### Contract profile screen

Clean, responsive, on-brand. Profiles the contract and its **owner entity**:
website, customer-service and accounting lines with **click-to-call / click-to-
text**, and a **downloadable contact file (.vcf)** — plus an **Add expiration
to calendar (.ics)** link. It searches our system for **jobs done under that
contract** and rolls them up into a **total-sales** figure and job list.

## CLI

```bash
ntxp-contracts add "Statewide JOC" --number RFP-2024-77 --type "Job Order Contract" --owner "TIPS USA"
ntxp-contracts import contract-log.csv      # idempotent; forgiving headers
ntxp-contracts list                         # or: list --json
ntxp-contracts query "electrical"           # full-text search
ntxp-contracts show 1                        # full profile incl. jobs/sales
ntxp-contracts stats
ntxp-contracts brand                         # the brand resolved from settings
```

## Use from Claude tools (MCP)

```bash
ntxp-contracts mcp-serve                     # stdio; register via mcp-configs/ntxp-contracts.json
```

Tools: `search_contracts`, `get_contract`, **`reference_lookup`** (lean
key/value poll for other tools), `list_expiring`, `upsert_contract`,
`update_field`, `sync_jobs`, `stats`, `get_brand`.

## Branding — resolved live from Claude's settings

Every screen styles itself from the **most up-to-date brand skill** found in
Claude's settings *at request time*, so updating the brand skill updates every
screen on next load — nothing is hard-coded. `branding.py` scans, in order:

1. `$CLAUDE_CONFIG_DIR/skills`
2. `~/.claude/skills`
3. `~/.config/claude/skills`
4. `<repo>/skills`
5. `~/.claude/plugins/**/skills`
6. `/mnt/skills` (+ `/mnt/skills/examples`)

A skill qualifies if its name/description mention brand identity; an
**NTXP-specific** brand skill outranks a generic one, and among equals the most
recently modified `SKILL.md` wins. It parses labelled hex colors and the
heading/body fonts. If nothing is found, documented NTXP defaults keep the UI
on-brand. Override the search root with `NTXP_BRANDING_PATH`.

## Jobs / sales (JobTread)

The profile's job list + total sales come from a local `jobs` cache. Pull rows
from the **JobTread** MCP, then cache them with the `sync_jobs` MCP tool or
`POST /api/contracts/<id>/jobs`. Ingestion is MCP-mediated (the same pattern as
the contacts CRM sync) so this package stays decoupled from any JobTread client,
and the cache is what every other tool polls — fast and offline-capable.

## CSV import format

Headers are matched case-insensitively against aliases, so a spreadsheet export
loads without edits. A title column is required; everything else is optional:

```
Contract Title, Contract / RFP #, Type of Contract, Owner Entity, Location,
Estimated Budget, Award Date, Duration, Expiration Date, Coefficient,
Cooperative Fee, Allowable Scope Terms, Notes, PDF Link, Executed
```

## Architecture

```
ntxp_contracts/
  config.py            DB path, defaults (recipient=NTXP LLC), type & scope vocab, web knobs
  model.py             Contract / OwnerEntity / Job dataclasses (+ attrs JSON bag)
  normalize.py         money / date / phone / website / contract-number normalization
  branding.py          live brand-skill resolver (scans Claude settings each call)
  jobs.py              MCP-mediated JobTread jobs ingestion into the local cache
  importer.py          idempotent CSV importer with provenance
  contactfile.py       vCard (.vcf) + iCalendar (.ics) builders for the profile
  db/                  connection (WAL/FK), migrations, repository (all SQL)
  web/                 stdlib HTTP server + dashboard & profile (static HTML/JS/CSS)
  cli.py               the `ntxp-contracts` command
  mcp_server.py        FastMCP tools (poll/update/sync/brand)
```

### How concurrent editing stays conflict-light

Editors `PATCH` one field at a time through `Repository.update_field` — the
single chokepoint. Two people editing **different** cells never collide. For the
**same** cell, an optional `expected_rev` enables optimistic locking: a stale
write returns `409` plus the fresh row so the UI reconciles just that cell
without losing the editor's other work. Every save appends a field-level
`change_log` row (who/when/old/new), which also drives the dashboard's live
polling.

## Tests

```bash
pytest contracts-db/tests
```
