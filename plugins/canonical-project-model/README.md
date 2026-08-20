# canonical-project-model

The **normalization layer** of the `construction-doc-intelligence` pipeline. It takes
the verbatim **project dossier** that `project-intake` built (from Mistral OCR4
extraction) and turns it into the **Canonical Project Record (CPR)** — one reusable,
CSI MasterFormat-organized, provenance-carrying source of truth — then renders it as
an **interlinked Excel workbook** that an estimator/PM/admin can read while the data
underneath stays machine-consumable for every downstream tool.

```
mistral-ocr4 (extraction)
      │
      ▼
project-intake  ──▶  projects/<slug>/  (verbatim dossier, with provenance)
      │
      ▼
canonical-project-model (this plugin)  ──▶  projects/<slug>/model/canonical-model.json  +  <slug>.xlsx
      │
      ▼
estimating · bid-leveling · scheduling · buyout · RFI/submittal · safety · logistics  (consumers PULL from the CPR)
```

- **OCR4 extracts. project-intake gathers. this plugin normalizes. downstream reasons.**
  This layer maps to MasterFormat, converts units, dedups entities, links references,
  and carries provenance. It **never** prices, levels bids, validates a low bid,
  judges compliance, or picks a winner — that reasoning belongs to the domain skills.
- **CSI MasterFormat is the only classification system.** Every trade, line item, cost
  code, submittal, quick link, and critical-path item carries a two-digit MasterFormat
  division (most recent version; 01–32 primary), and it is the **universal sort key**
  for documents, pages, tables, and every workbook sheet. See
  `resources/masterformat-divisions.json`.

## What it produces

```
projects/<slug>/model/
  canonical-model.json      # THE source of truth (schema: schemas/canonical-model.schema.json)
  sections/                 # one schema-conforming file per section (project_identity, contacts,
                            #   quick_links, scope, quantity_takeoff, estimate_sov, budget, trades,
                            #   subcontractors, bid_log, submittal_log, critical_path, schedule,
                            #   rfi_log, safety_plan, logistics_plan, requirements) + _meta.json
  project-record.md         # human-readable projection
  model-handoff.json        # downstream contract (schema: schemas/model-handoff.schema.json)
<slug>.xlsx                 # the interlinked workbook (primary working deliverable)
<slug>.html                # self-contained animated dashboard (read-only "at a glance" view)
```

### The workbook (sheets, all sorted by MasterFormat division)

- **Dashboard** — project bio at a glance, nav links to every sheet, a live project
  total pulled from the rollup, and a Needs-Human-Review panel.
- **Project Bio** — project #, important dates in order (prebid/questions deadline, job
  walk, RFP opening, NTXP sub bids due, bid review), bid-document list, JOC/IDIQ block.
- **Contacts** — designated POC, owner PM, architect, engineers (by division), special
  inspections, AHJ/permitting, JOC/coop admin, assigned NTXP estimator.
- **Quick Links** — document title · page · OCR4-screenshot URL, grouped by category and
  by trade/cost-code.
- **Trades** — every trade in CSI order, one-sentence scope summary, link to its budget
  page, empty notes column.
- **Summary QTO** — the **single source of truth** for quantities; every other sheet
  links here. Built from OCR4, conflicts verified against the drawings, sanity-checked.
- **Budget pages (one per trade)** — exclusions/clarifications (top), spec notes + PDF
  link with required products/systems/vendors/certs (middle), line items with quantity
  **pulled live from the QTO** × unit cost = total (bottom), and an **ITB button**.
- **ITB pages (one per trade)** — NTXP-branded Invitation to Bid: dates, NTXP contact,
  project-document links, scope summary, "subcontractors verify everything" note, a QR
  code to the NTXP website; print-ready so "download PDF" = File ▶ Save as PDF.
- **Submittal Register** — likely submittals scanned from the QTO/specs with estimated
  manufacturer lead times (the long-lead feed for the critical path).
- **Schedule** — the NTXP project schedule: milestones & key dates.
- **Critical Path** — ranked critical items with explanations + accelerate/de-risk alternates.
- **Bid Log** — per-trade estimated budget + confidence + variance; below, the subs
  (invited / intends / responded) with their actual bid amounts.
- **Budget Rollup** — editable high-level budget: estimate (from the trade pages),
  select a submitted bid or set a manual override, with a running project total.

Every record carries provenance (`source_doc`, page, bbox, confidence); low-confidence
values, unresolved conflicts, and invalid sections land in
`model-handoff.json.needs_human_review` and on the Dashboard.

## How it works

1. **Reasoning is parallel.** The `model-orchestrator` agent fans out one
   `section-normalizer` subagent per section; the subcontractor directory is reconciled
   first (so others reference parties by `party_id`) and the QTO before the sections that
   pull from it. Each writes one schema-conforming file under `model/sections/`.
2. **Assembly is deterministic.** `scripts/assemble_model.py` (stdlib-only, no network)
   validates each section and stitches `canonical-model.json` + `project-record.md` +
   `model-handoff.json`.
3. **The workbook renders deterministically.** `scripts/build_workbook.py` draws the
   `.xlsx` from the model — cross-sheet hyperlinks for nav, live formulas pulling
   quantities from the QTO into the budget pages, the editable rollup, and the ITB/QR.

## Run it

```bash
# 1) assemble the model (after the normalizer agents wrote model/sections/*.json)
python scripts/assemble_model.py --dossier projects/lincoln-clinic-ti --generated-at "$(date -u +%FT%TZ)"

# 2) render the workbook (needs openpyxl; QR needs segno + Pillow)
pip install -r requirements.txt
python scripts/build_workbook.py --model projects/lincoln-clinic-ti/model/canonical-model.json

# plan only (no dependencies):
python scripts/build_workbook.py --model .../canonical-model.json --dry-run

# 3) render the animated HTML dashboard (stdlib only — no dependencies)
python scripts/build_dashboard_html.py --model projects/lincoln-clinic-ti/model/canonical-model.json
```

### The HTML dashboard (`build_dashboard_html.py`)

A self-contained `<slug>.html` (no external requests — safe to email or host) rendered
from the same model: manual **sync pills** (one-way into the knowledge base, last five
days first; the Propose-Updates dialog stages the agent's suggestions for an
**approved** two-way sync) · five **donut KPI infographics** (slices slide around the
ring and bounce closed; glowing center values) · a **segmented budget bar** — click a
segment for that trade's budget justification and **exportable ITB** (print/download);
flips to the **Buyout Budget with neon-green profit** once `phase=project` · the
**activity stream** (JobTread photos, OCR4 pdf snips) · five translucent
**daily-report cards** with intelligence-flag banners · **open submittals/RFIs** beside
a scrollable **critical-path plotter** · a **three-week look-ahead** with click-to-edit
cells (red critical path, blue deliveries). Green/yellow/red **health lights** per
section; copy stays constructive (customers may see the screen). Navy-black 3D-gradient (faint interlinked-star field)
visual system (blue interactive/data, platinum hairlines+values, red risk); categorical chart
palette validated with the dataviz six checks. Honors `prefers-reduced-motion`,
degrades with JS off; `--fragment` embeds. The workbook remains the working
deliverable; this is the wall screen.

`build_workbook.py` flags: `--out` (xlsx path), `--company` (branding, default NTXP),
`--website` (URL the ITB QR points to, default the NTXP site), `--dry-run`.

## Dependencies

`assemble_model.py` and `build_dashboard_html.py` are **stdlib-only**. Only
`build_workbook.py` needs **openpyxl**; the ITB **QR code** uses **segno + Pillow**
when present and falls back to a plain hyperlink when not. See `requirements.txt`.
(True macro buttons require a `.xlsm` template; the ITB "button" is a styled hyperlink
to a print-ready ITB sheet — Save-as-PDF.)

## Boundaries

Normalize and organize — never reason. No bid leveling, low-bid validation, pricing,
compliance calls, scoring, or award recommendations here; those are
`vendor-bid-leveling`, `rfp-analysis`, `invoice-reconciliation`, `submittal-review`,
and the estimating tools that consume this record. Never invent a value the documents
don't support. Never re-OCR — extraction is `mistral-ocr4`'s job.
