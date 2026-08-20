---
name: canonical-project-model
description: Normalizes the verbatim project-intake dossier (which Mistral OCR4 produced) into the Canonical Project Record - one reusable, CSI MasterFormat-organized, provenance-carrying source of truth - and renders it as an interlinked Excel workbook plus a self-contained animated HTML command dashboard (donut KPI infographics, click-to-ITB segmented budget bar with buyout/profit mode, activity stream, daily-report cards with intelligence flags, critical-path plotter, editable three-week look-ahead, health lights, one-way connector sync with approval-gated two-way suggestions) in NTXP's navy/platinum/blue brand system. MasterFormat division is the sole classification and universal sort key. It organizes and structures; it never prices, levels, or decides.
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
