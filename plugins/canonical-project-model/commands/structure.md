# /canonical-project-model:structure

Normalize a project-intake dossier into the **Canonical Project Record (CPR)** and
render it as an **interlinked Excel workbook** — the single, reusable source of truth
every downstream estimating and project-management tool pulls from. Reasoning (reading
the dossier and mapping each domain to its section schema) runs as **parallel
section-normalizer agents**; deterministic scripts validate, assemble, and render.

Everything is classified and sorted by **CSI MasterFormat division** — the sole
classification system (see `resources/masterformat-divisions.json`).

## Usage

```
/canonical-project-model:structure <projects/<slug>  |  path/to/handoff.json>
```

If given a `handoff.json`, its `dossier_dir` is used. The dossier must already exist
(run `/project-intake:ingest` first). This step never re-OCRs.

## Steps

1. **Locate the dossier.** Read `projects/<slug>/handoff.json` and its
   `extracts/*.json`, `_raw/<doc>.ocr.json`, and `project.json`. These verbatim
   extracts (with provenance) are the input — extraction already happened.
2. **Reconcile the subcontractor directory first**, then **fan out one normalizer per
   section in parallel.** Launch a `section-normalizer` agent for each canonical section
   (project_identity, contacts, quick_links, scope, quantity_takeoff, estimate_sov,
   budget, trades, subcontractors, bid_log, submittal_log, critical_path, schedule,
   rfi_log, safety_plan, logistics_plan, requirements). Each reads the relevant extracts,
   tags every record with a MasterFormat division, normalizes units and entities,
   preserves verbatim text + provenance, and writes
   `projects/<slug>/model/sections/<section>.json` conforming to its schema.
   - **Summary QTO is the single source of truth.** Build it first from the OCR4 data,
     verify conflicts against the real drawings, sanity-check, and list in CSI order.
     Budget, bid-log, and submittal lines reference its `takeoff_id`s — they never
     restate a quantity.
3. **Record cross-document findings** in `model/sections/_meta.json` (`conflicts`,
   `normalization_log`, `needs_human_review`). Never silently resolve a disagreement.
4. **Assemble.** Run `scripts/assemble_model.py --dossier projects/<slug>`. It validates
   each section, stitches `canonical-model.json`, renders `project-record.md`, and emits
   `model-handoff.json`.
5. **Render the workbook.** Run `scripts/build_workbook.py --model
   projects/<slug>/model/canonical-model.json` (after `pip install -r requirements.txt`).
   It produces `<slug>.xlsx`: Dashboard + Project Bio, Contacts, Quick Links, Trades,
   Summary QTO, per-trade Budget pages (qty pulled live from the QTO, ITB button), ITB
   pages (QR to the NTXP site, print-ready), Submittal Register, Schedule, Critical
   Path, Bid Log, and an editable Budget Rollup — all sorted by MasterFormat division.
6. **(Optional) Render the HTML dashboard.** Run `scripts/build_dashboard_html.py
   --model projects/<slug>/model/canonical-model.json` for a self-contained, animated
   `<slug>.html` "at a glance" view (stdlib only). Charcoal/blue/gold/red visual
   system; the Excel workbook stays the working deliverable.

## Running the scripts directly

```bash
# plan only — which section files are present (no network, no deps)
python plugins/canonical-project-model/scripts/assemble_model.py --dossier projects/lincoln-clinic-ti --dry-run

# assemble, then render the workbook
python plugins/canonical-project-model/scripts/assemble_model.py --dossier projects/lincoln-clinic-ti --generated-at "$(date -u +%FT%TZ)"
python plugins/canonical-project-model/scripts/build_workbook.py --model projects/lincoln-clinic-ti/model/canonical-model.json
```

`assemble_model.py`: `--no-embed`, `--model-version N`. `build_workbook.py`: `--out`,
`--company` (default NTXP), `--website` (ITB QR target), `--dry-run`.

## Rules

- **MasterFormat only.** Every record gets a division; sort everything by it.
- **Normalize, never reason.** Map to MasterFormat, convert units, dedup entities, link
  references, carry provenance. Do **not** price, level bids, validate the low bid,
  judge compliance, or pick a winner — those are downstream skills.
- **Quantities live once** (the Summary QTO); everything else links to it.
- **Never invent values.** A price/quantity/date appears only if the documents support
  it; empty slots are left for the tools that fill them.
- **Conflicts surface, never resolve silently.** Verify QTO conflicts against drawings.
- **Idempotent.** Re-running updates the same `projects/<slug>/model/` and workbook.
- Always emit `model-handoff.json`, even on partial/failed assembly.
