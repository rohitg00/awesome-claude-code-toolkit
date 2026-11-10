# NTXP Contacts Database

One **master, de-duplicated contacts database** for all NTXP tools. Consolidates
contact exports from multiple systems into a single SQLite file that any tool
can query, update independently, and keep in sync with external CRMs.

- **Single source of truth** — one DB: embedded SQLite (`~/.ntxp/contacts.db`)
  for local/CLI use, or a cloud **PostgreSQL** canonical store (set `NTXP_DB_URL`)
  that the web UI and sync services share. Same engine, same schema, same CLI.
- **Idempotent imports** — re-running a source import never duplicates; changed
  rows update in place, unchanged rows are skipped.
- **De-duplication with provenance** — people/orgs are matched across sources;
  every canonical record traces back to its raw source rows.
- **Three access layers** over one core library: Python API, `ntxp` CLI, and an
  MCP server so Claude-based NTXP tools can query it directly.
- **Bi-directional CRM sync** — pluggable adapters (REST or MCP-mediated) with
  field-level last-write-wins and a `master_wins` allowlist.

> **Privacy:** this directory ships **code only**. Real contact data (the source
> files and the built `.db`) is gitignored and never committed.

## Install

```bash
pip install -e contacts-db                       # core
pip install -e "contacts-db[mcp,ocr,postgres,dev]"  # + MCP, OCR, Postgres, tests
```

## Backends: local SQLite vs. cloud PostgreSQL

The store is **dual-target**. By default it uses an embedded SQLite file. Point
it at Postgres by setting `NTXP_DB_URL` (precedence: a `postgres://` value passed
to `--db` or the API > `NTXP_DB_URL` > SQLite via `NTXP_DB_PATH`/default):

```bash
export NTXP_DB_URL='postgresql://ntxp:••••@db.internal:5432/ntxp_contacts'
ntxp init         # applies the Postgres schema (0001_init.postgres.sql)
ntxp stats
```

Everything else is identical — imports, dedup, FTS search, prune, and sync all
run unchanged. Under the hood the repository is authored in the SQLite idiom and
a thin translator rewrites it for Postgres (placeholders, `datetime('now')`,
`GROUP_CONCAT`→`string_agg`, identity-key `RETURNING`), and full-text search uses
a generated `tsvector` + GIN index in place of FTS5.

**Deploying the cloud canonical DB (Hostinger VPS):** provision PostgreSQL on the
existing VPS (near-zero marginal cost, private, reliable), create a database and
a least-privilege role, then run `ntxp init` once with `NTXP_DB_URL` set to that
DSN. The web UI and the sync services read/write the same database. Keep the DSN
in the NTXP secrets vault — never commit it.

> Run the Postgres-backend tests against a reachable instance with
> `NTXP_TEST_PG_URL=<dsn> pytest tests/test_postgres.py` (they're skipped
> otherwise).

## Quick start

```bash
ntxp init                                   # create DB + run migrations
ntxp import all --all /path/to/source/files # load every spreadsheet source
ntxp stats                                  # entity counts + per-source provenance
ntxp query "Vaden"                          # full-text search
ntxp export --format csv --out contacts.csv
ntxp prune --source tips --keep-states TX,OK --dry-run   # preview a regional cleanup
ntxp prune --source tips --keep-states TX,OK             # tombstone members outside TX/OK (reversible)
```

### Sources & loaders

| Source key | File | Loader |
|---|---|---|
| `tips` | TIPS member export (`.xlsx`) | `loaders/tips.py` |
| `buildingconnectd` | BuildingConnected bid invites (`.xlsx`) | `loaders/buildingconnectd.py` |
| `approved_subs` | Approved subcontractors (`.xls`) | `loaders/approved_subs.py` |
| `luncheon` | Event registrants (`.xls`) | `loaders/luncheon.py` |
| `cjp_pdf` | Certified JOC Professional holders (scanned PDF) | `loaders/cjp_pdf.py` |

### CJP scanned PDF (OCR)

The CJP holders file is a scanned image with no text layer, so it is extracted,
OCR'd, and **quarantined for review** before touching canonical tables:

```bash
ntxp extract-cjp All_CJP_Holders.pdf cjp.jsonl   # writes page images to OCR
# OCR the images -> write {full_name,company,...,confidence} JSONL rows
ntxp import cjp_pdf cjp.jsonl                     # routes rows into staging
ntxp staging list                                 # review
ntxp staging promote --all-above 0.9              # promote high-confidence rows
```

## Architecture

```
ntxp_contacts/
  config.py            thresholds, source-trust ranking, master-wins fields
  normalize.py         phones (E.164), emails, zips, dates, names, org names
  model.py             CanonicalRecord dataclasses
  db/                  connection (WAL/FK), repository (all SQL), migrations
  resolve/             blocking + weighted scoring + reversible merges
  loaders/             one per source + the idempotent import pipeline
  sync/                CrmAdapter interface, engine, adapters (REST + MCP)
  cli.py               the `ntxp` command
  mcp_server.py        FastMCP tools (search/get/upsert/export/sync)
```

### How dedup works

Normalize → block → score → decide. Email (when valid) is a deterministic merge
key; otherwise candidates are blocked by last name / shared org and scored on
`0.45*name + 0.30*org + 0.20*phone + 0.05*state`. Scores `>= 0.85` auto-merge;
`0.65–0.85` are flagged for review (`ntxp dedup review`); merges are reversible
(tombstones, never hard-deletes).

### Sync

`ntxp sync push --system quo --dry-run` prints a plan with no writes. REST
adapters run headless; MCP-only CRMs (e.g. Lightfield) are driven by an agent
through the MCP server's `sync_plan` / `record_sync_result` tools. Conflict
policy is field-level last-write-wins with a configurable `master_wins`
allowlist so NTXP-curated fields are never clobbered.

### Delta reconciliation (Lightfield-canonical hub)

**Lightfield is the canonical first source** (`config.CANONICAL_SOURCE`): every
system reconciles back to it. Adapters ship for **Lightfield, JobTread,
QuickBooks, BuildingConnected** (and Quo). The agent pulls records from a system
(via its MCP/REST tool), dumps them to JSON, then:

```bash
ntxp reconcile --system jobtread pulled.json            # read-only delta plan
ntxp reconcile --system jobtread pulled.json --apply    # enrich canonical DB
```

or, over MCP, the `reconcile_plan` / `reconcile_apply` tools. The plan classifies
each record as **create / link / update / conflict / unchanged** and lists the
exact fields that disagree with canonical. It's **change-only**: a record whose
remote payload hash already matches the stored link is skipped. `apply` writes
**only to the local canonical store** — never to the remote CRM — linking
`external_ids` and recording provenance. Applied pulls are tagged
`pull:<system>` in the change-log, so they **fan out** to the *other* systems'
push plans but never **echo** back to the system they came from. Field conflicts
are surfaced for review; lower-ranked systems never overwrite a Lightfield value
(`config.SYSTEM_PRECEDENCE`).

### Nightly Google Workspace sweep (collection)

The nightly agent casts a wide net across **all** NTXP Workspace users and
platforms — Gmail, Google Contacts, Calendar, Drive, People — and hands the raw
results to the collectors, which do **deterministic extraction only** (no
inference spent qualifying). Each person is tagged with the *channel* it came
from and the data point's **own date**, so a Gmail signature or a saved Google
Contact grades as closest/newest and a years-old calendar event grades as far/old.

```bash
ntxp sweep bundle.json            # extract + dedup into canonical, then qualify
```

`bundle.json` buckets raw objects by channel:
`{"gmail":[…], "gcontacts":[…], "calendar":[…], "drive":[…], "people":[…]}`
(also the `workspace_sweep` MCP tool). Collection writes only locally; new/changed
contacts fan out to the connectors on the next `ntxp sync push`.

**Full nightly pipeline:** `sweep` (collect) → `reconcile` each CRM pull
(Lightfield-canonical) → `qualify` (grade + exposure gate) → `sync push` (fan out
only exposed/graded deltas). Each stage is change-only.

### Qualification & grading (JEV)

`ntxp qualify` grades every contact on four axes — **source** trust
(`SYSTEM_PRECEDENCE`), **recency** (age of the freshest observation), **corroboration**
(how many independent sources agree), and **distance-from-person** (self/CRM near,
event lists mid, OCR scans far) — into a probability grade `[0,1]` and an A/B/C/D
band stored in `contact_grade`. Nothing is dropped: outdated or weak contacts keep
every reference but are flagged `is_exposed = 0` / `is_synced = 0`, so the UI hides
them and the push planner skips them. Run it after imports/reconciliation (e.g. in
the nightly job); also available as the `qualify_contacts` / `get_grade` MCP tools.

```bash
ntxp qualify            # grade + set the exposure/sync gate
ntxp qualify --plan     # compute and report without writing
```

### Connector middle-layer (Zapier-style)

Users connect their accounts through a **whitelisted** layer (Zapier is the broker
— its MCP is available) and their contacts flow into the canonical store via the
normal dedup pipeline. No account secrets touch this repo.

```bash
ntxp connector-import --service hubspot contacts.json   # allowlist-gated
```

See [docs/CONNECTORS.md](docs/CONNECTORS.md).

### Mini model council (near-zero cost)

For contact decisions (which value / which match / which class), `ntxp council`
routes via **JEV** (free, deterministic) and escalates to the **cheapest
available** cheap LLM judge (DeepSeek/Grok/OpenAI, key-gated, env-overridable) only
when uncertain, then weighted-votes with provenance. Runs for free with no keys.
See [docs/COUNCIL.md](docs/COUNCIL.md).

### Live view (hosted app + Google Sheet mirror)

`ntxp serve-http` also serves the **live contacts app** at `/` (real Google Workspace sign-in; NTXP document-engine styling; filters,
proximity, inline edit, labels, reports → PDF/Word, CSV) backed by `/api/*`. A read-only **Google Sheet mirror** (`sheets/`) pulls the same
API with domain OAuth. Production target: Hostinger VPS + **Supabase** Postgres — see [deploy/README.md](deploy/README.md),
[docs/LIVE_VIEW.md](docs/LIVE_VIEW.md) and [sheets/README.md](sheets/README.md). Audit the UI with `python tools/ui_audit.py <url> <out>`.

### Cloud MCP (stateless, OAuth-gated) + auto-hooks

A stateless, cloud-hostable **streamable-HTTP MCP** gives any tool/skill/workflow
live contact access. Install the plugin and it registers the remote MCP
(`remote/plugin.mcp.json`) — zero setup beyond OAuth.

```bash
NTXP_DB_URL='postgresql://…' NTXP_MCP_AUTH=google ntxp serve-http --port 8080
# endpoint: POST /mcp (Bearer Google Workspace token) · GET /health is open
```

Auth modes (`NTXP_MCP_AUTH`): `google` (verify a Workspace token, require
`ntxpllc.com`), `static` (`NTXP_MCP_TOKEN`), `none` (dev). The
`hooks/contact_context.py` **UserPromptSubmit hook** auto-injects contact cards,
blue hotlinks, live **Maps** location links, and alternate-info previews whenever
a message mentions a known contact; `locate_address` returns map links on demand.

### One-way iOS / iPhone contact sync (CardDAV)

A **read-only CardDAV** collection gives a new hire company contacts on day one —
one-way, nothing writes back, and only **exposed** contacts are emitted (the
grader's gate). Served at `/carddav` by `ntxp serve-http` (token-gated); add it on
iOS as a CardDAV account. Offline/one-time: `ntxp vcard-export --out contacts.vcf`.

### Tool-agnostic context hooks (blue hotlinks)

Any NTXP tool can inject live contact context as **blue hyperlink hotlinks**:

```bash
ntxp context "Vaden"          # context card (+ blue-link HTML) for the best match
ntxp hotlink notes.txt        # wrap known contacts/orgs/emails/phones in blue links
```

(also the `contact_context` / `hotlink_text` MCP tools). `hotlink_text` scans a
string and wraps every recognized email, phone, multi-word name, and company name
in `<a style="color:#2f6fd0">…</a>` pointing at the contacts page filtered to that
entity (`?focus=contact:<id>`), so clicking a hotlink opens the filtered list.
Matching is conservative (emails/phones exact; names multi-word only) to avoid
false positives. Base URL via `NTXP_CONTACTS_URL`.

### Enrichment, photos & LinkedIn (candidate-based)

`ntxp enrich` backfills missing primary fields (phone/email/address/website),
resolves **profile photos**, and **cross-references LinkedIn** through one
JEV-graded candidate pipeline — nothing overwrites canonical data without
confirmation.

```bash
ntxp enrich detect                      # contacts missing primary fields
ntxp enrich generate                    # run resolvers -> store graded candidates
ntxp enrich candidates --field photo    # review (highest grade first)
ntxp enrich confirm <cand_id>           # apply one candidate to the contact
ntxp enrich linkedin --contact-id 42 --url https://linkedin.com/in/… --photo https://…
```

Built-in resolvers are deterministic/offline (Gravatar + Libravatar photos,
company-website and public-entity-directory derivation, LinkedIn search
candidates). Heavy OSINT tools (holehe, maigret, GHunt) run **out-of-band** via
the agent and feed candidates into `enrich generate --extra`. Photo priority:
saved contacts / public-entity domains / confirmed LinkedIn highest. LinkedIn is
**never scraped** in code — the agent confirms a match and `confirm_linkedin`
saves the field and promotes the profile photo. See
[docs/ENRICHMENT.md](docs/ENRICHMENT.md) for the full tool evaluation.

## Configuration

| Env var | Purpose | Default |
|---|---|---|
| `NTXP_DB_PATH` | SQLite DB file location | `~/.ntxp/contacts.db` |
| `NTXP_DB_URL` | PostgreSQL DSN (cloud canonical store); overrides SQLite | _(unset)_ |

## Tests

```bash
pytest contacts-db/tests
```
