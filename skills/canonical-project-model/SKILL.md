---
name: canonical-project-model
description: Normalizes the OCR4 project-intake dossier into the Canonical Project Record - one CSI MasterFormat-organized, provenance-carrying source of truth - and renders an interlinked Excel workbook, an animated HTML command dashboard (KPI donuts, click-to-ITB budget bar with buyout/profit mode, activity stream, daily reports, critical-path plotter, editable look-ahead, health lights, approval-gated two-way sync), and the NTXP Plans Atlas: an offline, hyperlinked drawing-set viewer navigable by trade, spec, phase, or area, with callout links, drawing-text search, and staged markups and phase images. Auto-deploys the atlas to Construction Documents when a bid or project is confirmed and rebuilds when drawings change. Organizes; never prices or decides, except the approval-gated draft Project Ignition stage. Use for project records, dashboards, plan atlas, finding a trade or spec on the drawings.
---

# Canonical Project Model — the source-of-truth layer

The normalization node of the `construction-doc-pipeline`. It sits between the
verbatim **project-intake dossier** (which `mistral-ocr4` extracted) and the
reasoning tools, and produces the **Canonical Project Record (CPR)** — one stable,
machine-readable structure that every estimating and project-management tool pulls
from instead of re-parsing documents — then renders it into an **interlinked Excel
workbook** (a dashboard plus a sub-page per section) that an estimator, PM, or admin
can read while the data underneath stays tool-consumable.

**Two rules shape everything:**
> 1. **OCR4 extracts. project-intake gathers. this layer normalizes. downstream reasons.**
>    Map to MasterFormat, convert units, dedup entities, link references, carry
>    provenance. Never price, level bids, validate a low bid, judge compliance, score,
>    or pick a winner — that is `vendor-bid-leveling`, `rfp-analysis`,
>    `invoice-reconciliation`, `submittal-review`, and the estimating tools' job. A
>    value enters the model only if a document supports it.
> 2. **CSI MasterFormat is the only classification system.** Every trade, line item,
>    cost code, submittal, quick link, and critical-path item carries a two-digit
>    MasterFormat division (most recent version; divisions 01–32 are the primary
>    working range). The division is the **universal sort key** — documents, pages,
>    tables, and every workbook sheet are ordered by it. See
>    `resources/masterformat-divisions.json`.

## Why this layer exists

`project-intake` deliberately stops at verbatim extraction with provenance and defers
"cross-document dedup/normalization." Without this layer, every downstream tool
re-derives the same structure — slow, inconsistent, error-prone. This skill produces
that structure **once** and spreads it as a single workbook, so pricing, budgeting,
scheduling, buyout, and compliance all share the same facts.

## Inputs — what you read

The finished dossier at `projects/<slug>/` (never re-OCR): `handoff.json`,
`extracts/*.json` (products, schedules, contacts, scope-items, requirements — each
record already carries `_doc`, page, bbox), `extracts/product-tables.csv`, the raw
`_raw/<doc>.ocr.json` envelopes, and `project.json`. When the initial quantity takeoff
needs a conflict resolved or a sanity check, verify against the real drawings.

## The Canonical Project Record (data) → the workbook (deliverable)

A root `canonical-model.json` plus one file per section under `model/sections/`, each
conforming to a fixed schema in the plugin's `schemas/` folder. `build_workbook.py`
then renders the workbook. Sections / sheets:

| Section / Sheet | What it holds |
| --- | --- |
| **Dashboard** | project bio at a glance, nav links to every sheet, live project-total pulled from the rollup, review flags |
| `project_identity` → **Project Bio** | project #, important dates in order (prebid/questions deadline, job walk, RFP opening, NTXP sub bids due, bid review), bid-document list, JOC/IDIQ (UPB, coefficient, NTE) |
| `contacts` → **Contacts** | designated POC, owner PM, architect, engineers (by division), special inspections, AHJ/permitting, JOC/coop admin, assigned NTXP estimator |
| `quick_links` → **Quick Links** | document title · page · OCR4-screenshot URL, grouped by category (project info, phasing, A/E, finish/door/HVAC/light/electrical-gear schedules, arch demo, arch new walls) and a row per trade with cost-code sub-rows |
| `scope` | master scope register (CSI-coded) — the rows everything maps to |
| `quantity_takeoff` → **Summary QTO** | the **single source of truth** for quantities; every other sheet links here. Built from OCR4, conflicts verified against drawings, sanity-checked, in CSI order |
| `trades` → **Trades** | every trade with scope, in CSI order, one-sentence scope summary, hyperlink to its budget page, empty notes column |
| `budget` → **per-trade Budget pages** + **Budget Rollup** | each trade page: exclusions/clarifications (top), spec notes + PDF link with required products/systems/vendors/certs (middle), line items with qty **pulled live from the QTO** × unit cost = total (bottom), and an **ITB button**. Rollup: editable high-level budget, select a submitted bid or override, running project total |
| `submittal_log` → **Submittal Register** | likely submittals scanned from the QTO/specs: division, trade, product data / samples / shop drawings, est. manufacturer lead time |
| `critical_path` → **Critical Path** | ranked critical items with explanations + alternates that accelerate/de-risk |
| `schedule` → **Schedule** | the NTXP project schedule: milestones & key dates |
| `bid_log` → **Bid Log** | per-trade estimated budget + confidence score + variance range; below, the subs — invited / intends / responded, with their actual bid amounts |
| ITB pages | per-trade Invitation to Bid: dates, NTXP contact, project-document links, scope summary, "subs verify everything" note, QR code to the NTXP website; print-ready (Save-as-PDF) |
| `rfi_log`, `safety_plan`, `logistics_plan`, `requirements` | carried in the model for downstream tools |

Every record carries provenance (`source_doc`, page, bbox, confidence). The root also
carries `counts`, `confidence`, `normalization_log`, `conflicts`,
`needs_human_review`, and `next_consumers`.

## Normalization rules (what "structuring" means here)

- **Classify with MasterFormat only.** Tag every item with a two-digit division (and
  full section when known); map to a company cost code when evident. Sort everything
  by division.
- **Units.** Normalize `uom` to the canonical set (EA, LF, SF, SY, CY, TON, LS, HR…)
  and record the conversion in `normalization.actions`; keep the original in `as_written`.
- **Quantities live once.** The Summary QTO is the SSOT; budget/bid/submittal lines
  reference a `takeoff_id`, they never restate a number.
- **Entities.** Dedup companies/people into one `party_id`; reference it everywhere.
- **Verbatim + provenance.** Keep binding text word-for-word; carry confidence. Low
  confidence is flagged, never dropped.
- **Conflicts surface, never resolve.** Two documents disagreeing on a fact → both,
  with provenance, into `conflicts` / `needs_human_review`. Verify QTO conflicts
  against the drawings.
- **Never invent.** No price, quantity, date, or party that the documents don't support.

## Parallel processing (default to it)

Reconcile the **`subcontractors`** directory first so other sections reference parties
by `party_id`. Then launch one **section normalizer per remaining section concurrently**
— each reads the dossier and writes its own `model/sections/<section>.json`. The QTO is
normalized before budget/bid/submittal sections (they pull from it). **Assembly is the
single barrier:** `assemble_model.py` validates and stitches `canonical-model.json`;
`build_workbook.py` then renders the `.xlsx` (needs `openpyxl`; QR needs `segno`+`Pillow`,
else it degrades to a hyperlink); and `build_dashboard_html.py` (stdlib only) renders a
self-contained animated HTML dashboard — a read-only "at a glance" view in NTXP's
navy/platinum/blue/red visual system. The Excel workbook stays the working deliverable.

## The dashboard (v2) — what it renders

`build_dashboard_html.py` (stdlib-only, self-contained output) renders: manual **sync
pills** across the top (glow on hover) · five **donut KPI infographics** (thick bold
slices slide around the ring and bounce closed; glowing value in a smooth round
center) · a **segmented budget bar** by trade with dollar amounts above and the total
below — click a segment for that trade's budget justification and **exportable ITB**
(print / download); once `phase=project` it becomes the **Buyout Budget** with profit
in neon green · the **activity stream** (JobTread photos, OCR4 pdf snips) · five
translucent **daily-report date cards** with meeting/workplace-intelligence flag
banners linking to the JobTread report · **open submittals** and **open RFIs** beside
a scrollable vertical **critical-path plotter** · a **three-week look-ahead**
(last/this/next week) with click-to-edit cells, red critical path and blue deliveries.
**Health lights**: green = on track · yellow = the PM team should work this soon ·
red = priority focus. Donut/segment colors are a validated categorical palette
(dataviz six checks, dark surface) assigned to divisions in fixed order.

## The Plans Atlas — navigate the drawing set by concept

The drawing set as a linked web document, without altering the drawings. Adapted from
the Contractor OS "Interactive Drawing Atlas" (NTXP Forge audit, verdict ADAPT) with its
faults fixed: **deterministic extraction** (`build_atlas_data.py`, PyMuPDF optional,
read-only on sources, degrades to manifest-only), NTXP branding, NTXP paths, and links
emitted only when the target resolves.

- **Section**: `plans_atlas` (schema `plans-atlas.schema.json`) — sheets (number, title,
  discipline, revision, scale, text-layer check), the callout-link graph (`5/A-501`
  detail/section/schedule bubbles, `09 51 13` spec references — each with provenance and
  confidence), the concept index, and a renders ledger. Sorted, like everything, by CSI
  division.
- **Viewer** (`build_atlas_html.py`, stdlib-only, fully offline): concept rail
  (**TRADES / SPECS / PHASES / AREAS**) so a user lands on any trade, spec section,
  phase, or area in a few clicks; discipline tabs + sheet grid; pan/zoom sheet viewer
  with glowing callout hotspots and Back-stack navigation; punctuation-insensitive
  search across sheet numbers, titles, concepts, and drawing text (`FD2` finds `FD-2`;
  sheets without a text layer are marked not searchable, never faked).
- **Hyperlinks everywhere**: division chips → trade budget pages and Summary QTO rows
  (quantities still live once, in the QTO); spec references → the per-section PDFs that
  `specs-skill` cuts; sheets ↔ details ↔ schedules; the atlas ↔ the command dashboard.
- **Live generation stays owned by the generating skills.** "Stage markup" and "Stage
  phase image" queue requests for `ntxp-pdf-markups-and-redlines` (rendered markups,
  scope overlays, takeoff exhibits) and `construction-scope-visualizer` /
  `4d-bim-visualization` (photorealistic phase-of-scope images). Requests follow the
  same approval-gated flow as all two-way suggestions; finished renders land back in
  the atlas `renders` ledger with provenance and appear on the sheet's panel.
- **Gate**: if a pack inventory reports the drawing set blocked (duplicates, unreadable
  sheets), record it in `source_set.pack_qa` and surface it in `needs_review` instead
  of building a confident-looking atlas over a broken set.

### Automatic deployment & as-needed updating

The atlas is not an on-request deliverable — it **deploys itself** as part of the
project record, through `scripts/deploy_atlas.py` (idempotent orchestrator:
discover plans → extract → assemble → render → file → record state).

**Fire it automatically, without being asked, when:**
1. **A bid is confirmed** (NTXP is bidding the job) — during initial knowledge-base
   creation and review, while the records, plans, specs, and dossier are being
   assessed, run the deployment with `--event bid_confirmed`. The atlas is created as
   part of the Canonical Project Record and **filed under the project's Construction
   Documents folder** (resolve the exact folder with `ntxp-folder-system` when filing
   to Drive; locally the script auto-detects or creates `Construction Documents/` and
   writes `Construction Documents/Plans Atlas/plans-atlas.html`).
2. **A project is confirmed** (awarded; `phase` flips estimate → project) — rerun with
   `--event project_confirmed` so the atlas reflects the conformed set and the record
   links shift from bid pages to buyout/budget pages.
3. **The drawing set changes** — addenda, ASIs, revised or conformed sheets landing in
   the Construction Documents folder. The deployer keeps a SHA-256 manifest of the
   drawing PDFs in `model/.atlas-state.json`; any difference triggers a rebuild
   (`--event addendum`), identical sets exit "up to date" without rebuilding. Never
   rebuild for cosmetic reasons; never skip a rebuild when a sheet changed.

**Placement rule:** the rendered atlas (plus its README and any non-inlined assets)
lives in `<project>/Construction Documents/Plans Atlas/`; the data (`plans_atlas`
section, word sidecar, state file) lives in `<project>/model/` with the rest of the
Canonical Project Record. The atlas ships beside the drawings it indexes, so whoever
opens the const docs folder finds the navigable set first.

**Boundaries unchanged:** deployment is one-way creation of record + deliverable.
Staged markups/phase images inside the atlas remain approval-gated; the deployer never
writes to external systems, never modifies source PDFs, and reports — calmly — what it
built, skipped, or is waiting on (`no_drawings` is a normal state for a brand-new bid,
not an error).

## Phase 1 receiver — drawings processed during the Estimating review (automatic)

When the NTXP Estimating Phase 1 skill finishes reading a bid, it stages
`handoffs/atlas-request.json` (`atlas_bridge.py send`). This skill's `scripts/phase1_receiver.py`
takes it from there with no questions: it **seeds** the project identity, scope and trades sections
of the Canonical Project Record from the KB (never over a section a person or tool edited), **deploys**
the atlas and the Project Ignition blueprint (`kb_initial_review`), **interlinks** the KB with the
drawings (`scripts/interlink.py`: sheet numbers, source page, spec sections, divisions, text mentions),
and writes `atlas/atlas-response.json`, `plans_atlas.json`, `interlinks.json` and `atlas-chunks.json`
into the KB for every later step. Claude Code hooks (`hooks/hooks.json`, or
`hooks/scripts/install_hooks.py` for a plain folder) start the receiver when a request appears and
report pending or stale requests at session start. Detail: `reference/phase1-receiver.md`.

```bash
python scripts/phase1_receiver.py receive --request <kb>/handoffs/atlas-request.json
python scripts/phase1_receiver.py status  --request <kb>/handoffs/atlas-request.json
```

Viewer deep links: `plans-atlas.html#sheet=<sheet_id>` opens that sheet.

## Scope index, Index Legend and the live viewer

Every deploy also indexes the set and links it. Detail: `reference/scope-index-and-viewer.md`.

- **Scope index** (`scripts/scope_index.py` → `sections/scope_index.json`): the **Project Index**
  (title, address, owner, architect, MEP and other engineers, page index with detail labels and
  titles, general and sheet notes per page, rooms with SF where printed, millwork elevations, trades);
  **Clarifications and Exclusions** (scheduling, exclusions, owner-required vendors, owner allowances,
  pricing and alternates, phasing, each with its page and related trades); every **schedule** as a
  cropped image plus a recreated table; and a **scope index per CSI division** (door, HVAC,
  electrical, plumbing, millwork and the rest).
- **Honest by construction:** nothing is invented. Values not printed are `null`; duct, pipe, conduit
  and wire sizes are tag counts, not measured lengths; measured quantities come only from the takeoff.
- **Index Legend** (`scripts/build_atlas_pdf.py`): placed **in front of the first drawing** of every
  linked set, in NTXP Document Engine style, and copied to the knowledge base (`<kb>/atlas/`) and the
  Drive Knowledge Base folder. Links target **named destinations**, so they survive re-issue and can
  be opened as `set.pdf#nameddest=sheet:A-101`.
- **Viewer** (`scripts/atlas_shell.py`): persistent navy header, swipeable page strip, a left drawer
  (trades, spec numbers, areas, phases) and a right drawer with the selection's bottom level (trade
  scope summary, takeoffs, schedules, spec chapter). Drawings and pop-up cards are shown as drawn.
- **Overlays, export, print:** NTXP PDF markup colours and schema 3.0 manifests
  (`model/atlas/markups/*.json`); animated layers for markups, schedules, notes, rooms and door
  marks; export PNG, JSON or PDF (`scripts/atlas_live.py serve`); print the open sheet.

```bash
python scripts/scope_index.py build --model <project>/model
python scripts/build_atlas_pdf.py --pdf set.pdf --model <project>/model --out "set - Plans Atlas.pdf"
python scripts/atlas_live.py serve --project <project>        # live viewer with PDF export
```

## Project Ignition — Jev platform (blueprint, magic, processing)

When a bid is confirmed and the atlas has deployed, run **Project Ignition**
(`scripts/ignition.py`, full rules in `reference/project-ignition.md`):

1. **Blueprint (deterministic, free):** `ignition.py blueprint` (or
   `deploy_atlas.py --ignite`) builds division packets, a CPM skeleton and typed work
   orders under `model/ignition/`.
2. **Magic:** **Astra** (`gpt-6-astra`) and **Opus** (`claude-opus-5-5`) each answer
   the work order independently; **Compass** supplies cited public $/SF rows. Never
   route these to Ledger (DeepSeek) or Mason (GLM): they hold owner, bid and
   pricing content.
3. **Jev processing:** `ignition.py process` compares the two PERT sets, rolls up CPM,
   decides unit prices, dates confidence and sanity-checks $/SF. Every judgment is a
   typed enum in `jev-judgments.jsonl`.
4. **ITB pages:** `ignition.py itb --pdf` writes 8.5 x 11 packages per division. No
   prices ever appear on ITB pages.

Everything is a **draft for PM approval**. A JOC contract unit price is never
overridden; a missing gross SF or benchmark is reported, never guessed.

## Cross-platform deployment (Claude, ChatGPT, Grok)

The rules live once, in the model-agnostic contract `AGENTS.md`. Every platform
follows it, and the platform adapters add mechanics only:

- **Claude** (`claude/SKILL.md`): Claude Code plugin or `~/.claude/skills`
  install, claude.ai/Cowork skill upload, Claude API tool use with a cached
  system prompt.
- **ChatGPT** (`chatgpt/gpt-instructions.md`, `agents/openai.yaml`): Custom GPT
  or Project instructions within the 8,000-character limit, Code Interpreter
  runs, Codex via `AGENTS.md`, and the API.
- **Grok** (`grok/grok-instructions.md`): Grok Projects and the xAI API, with
  web/X search kept out of project facts, a tone override to customer-safe
  language, long-context loading, and Grok Imagine for staged phase images.

Shared assets: `tools/functions.json` (function-tool schema; OpenAI and xAI
format, with Anthropic `input_schema` conversion), `scripts/run_tool.py`
(executes any platform's tool call through the same deterministic scripts),
`scripts/platform_pack.py` (builds each platform's upload set; ChatGPT and Grok
get 13 flat files under the 20-file Knowledge limit, plus a `setup` command
that restores the folder layout inside the sandbox), and `config/defaults.yaml`.
A model that cannot execute code hand-builds the atlas data per `AGENTS.md`
section 4 and says the viewer still needs a render pass.

## Data connectors & sync policy

- **One-way in, always.** Every connector (JobTread, OCR4 docs, schedule, contacts, workspace intelligence — summarized emails and meeting minutes land in the activity stream and knowledge base with provenance)
  syncs INTO the knowledge base. Prioritize the most recent **five days** of data,
  then backfill quickly. The canonical model is the **single source of truth**.
- **Two-way only by approval.** After inbound sync and tool updates finish, present
  the agent's reasoned conclusions in the dashboard GUI (**Propose updates**):
  suggested meetings to resolve items, schedule changes to protect the critical path,
  budget adjustments, change-order candidates for scope that appears unbudgeted,
  constraint solutions, and alternative specs/products/suppliers. Nothing writes
  outward until the user approves.
- **If declined**, ask once whether a narrower sync is wanted (schedule / documents /
  contacts only). If not, leave the dashboard and knowledge base **correct and
  authoritative even when external tools do not align**.
- **Voice**: senior PM helping the newer team members — calm, assertive, specific,
  supportive. Explain circumstances so people relax and feel supported; never add
  stress. **Never make blunt negative statements about the project's success** — a
  customer may be reading. Use constructive framing ("the item to watch this week"),
  and encode urgency in the red/yellow/green lights, not in alarming language.
- **Parsing council (exception path).** When user input is vague or disengaged, or
  a draft doesn't read industry-grade, or OCR confidence is low on binding values,
  convene the limited model council per `reference/model-council.md`: Gemini for
  vision/Google-OCR second passes, GPT (Luna) for bulk microtasks and the findings
  report, Claude to adjudicate intent and write the model. Default remains
  single-model; every convening names its trigger and logs to `normalization_log`.

## Cross-references

- `mistral-ocr4` — extraction layer (upstream of intake).
- `project-intake` (plugin) — builds the dossier this skill consumes.
- `construction-doc-pipeline` — the orchestration spine; this is its normalization node.
- `rfp-analysis`, `vendor-bid-leveling`, `invoice-reconciliation`, `submittal-review`
  — downstream reasoning tools that PULL from the canonical sections / workbook.
- `lean-pm-judgment` — applied downstream, not here.

## Anti-patterns

- Using any classification other than CSI MasterFormat, or leaving a division blank.
- Re-OCR'ing documents the dossier already extracted.
- Reasoning in this layer: leveling bids, validating the low bid, judging compliance,
  pricing, scoring, recommending an award.
- Restating a quantity instead of linking to the QTO SSOT.
- Inventing a value the documents don't support; dropping provenance.
- Leaving cross-document disagreements silently resolved instead of in `conflicts`.
- Duplicating contacts across sections instead of referencing a `party_id`.

## Checklist

- [ ] Consumed the existing dossier; no re-OCR.
- [ ] Everything classified by CSI MasterFormat division and sorted by it.
- [ ] Subcontractor directory deduped; sections reference parties by `party_id`.
- [ ] Summary QTO built (OCR4 + drawing verification) as the single source of truth;
      budget/bid/submittal lines link to its `takeoff_id`s.
- [ ] Verbatim text + provenance + confidence on every record; conflicts surfaced.
- [ ] Sections normalized in parallel; `assemble_model.py` then `build_workbook.py` run.
- [ ] `canonical-model.json`, `project-record.md`, `model-handoff.json`, and the
      `.xlsx` workbook written with accurate status and counts.
- [ ] No reasoning performed here — structure handed to the downstream tools.
