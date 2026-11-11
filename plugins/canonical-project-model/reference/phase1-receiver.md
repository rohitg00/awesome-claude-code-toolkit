# Phase 1 drawing handoff: the Plans Atlas receiver

**Purpose:** when the NTXP Estimating Phase 1 skill finishes reading a bid's documents, the
drawings are processed into the Plans Atlas automatically, the results are saved inside the
project KB for every later step, and every KB fact is linked to the sheet it belongs to.
No one has to remember to run anything.

```
 Estimating Phase 1                         Plans Atlas (this skill)
 ------------------                         ------------------------
 build_kb.py / paginate_drawings.py
        |  (hook, or Stage 5b)
        v
 atlas_bridge.py send  --request-->  phase1_receiver.py receive
   handoffs/atlas-request.json         1 seed CPR sections from the KB
                                       2 deploy_atlas.py (--ignite)
                                       3 interlink.py  KB <-> sheets
        <--response--                  4 atlas/atlas-response.json
 atlas_bridge.py receive
   kb_index.jsonl (+ atlas_sheet / atlas_division / atlas_spec)
   lifecycle.json, handoff.json (atlas + phase2_readiness.atlas), CHANGELOG.md, atlas/STATUS.md
```

## What gets saved (all under `<kb>/atlas/`, folder 1.3 Intake & Dossier)

- **`atlas-response.json`**: status, sheet and link counts, viewer path, review items.
- **`plans_atlas.json`**: the full atlas section (sheets, callout links, trade/spec/phase/area index).
- **`interlinks.json`**: sheet to KB facts, division to sheets to KB, spec section to sheets to KB,
  a back-reference map by KB chunk id, unmatched sheets and title conflicts (listed, never resolved).
- **`atlas-chunks.json`**: read natively by `build_kb_index.py`, so searches find drawings and a
  later index rebuild never drops them. Record kinds: `sheet` (trades, spec sections, phases, areas,
  scale, OCR and review flags), `sheet_text` (printed words per sheet, capped), `division`, `spec`,
  `trade`, `area`, `phase`, `ignition` (draft status and $/SF verdict) and `atlas_status` (counts,
  search coverage, review items). Each record carries a `text` field for search. Kinds beyond
  sheet, division and spec need a mapping in `build_kb_index.py` before they are indexed.
- **`STATUS.md`**: one-page human summary. **`project/`**: the CPR (`model/`) and the viewer under
  `Construction Documents/Plans Atlas/plans-atlas.html`, plus the Project Ignition blueprint and
  work orders in `model/ignition/`.

## Interlinking rules (each link records `via` and `confidence`)

- **sheet_number 0.95**: normalized sheet number equal (A-101 = A101 = A1.01).
- **sheet_field 0.90**: a KB note or schedule row names the sheet.
- **trade_sheets 0.85**: the curated trade lists the sheet.
- **spec_section 0.80**: the KB spec section is cited on the sheet in the atlas.
- **doc_page 0.70**: same source document and page.
- **text_mention 0.60**: a real atlas sheet number appears in the record text.
- **division 0.40**: same CSI division, capped at six sheets.

KB extracts are never edited. Anything that does not match is reported: a sheet in the KB index
but not in the drawing PDFs is flagged as a possibly incomplete set.

## Seeding the Canonical Project Record

The receiver writes `project_identity`, `scope` and `trades` sections from the KB so the atlas and
Project Ignition start informed (title, owner, location, stated gross SF, dates, scope items by
division, the curated trade list). A section is written only when it is missing or still exactly as
seeded; if a person or another tool edited it, it is **kept** and reported.

## Hooks (Claude Code)

- **PostToolUse**: when `atlas-request.json` is written or named, start the receiver in the
  background (lock-protected, logged to `atlas/hook.log`).
- **SessionStart**: report requests that are pending or stale.
- Plugin installs get `hooks/hooks.json` automatically. For a plain folder:
  `python hooks/scripts/install_hooks.py --settings .claude/settings.json` (idempotent, `--remove` undoes it).
- `NTXP_PHASE1_HOOKS=off` disables; `NTXP_HOOK_SYNC=1` runs in the foreground.

## No hooks? (ChatGPT, Grok, plain API)

The same flow runs from the skills' steps: Estimating Stage 5b calls `atlas_bridge.py send`, which
runs this receiver. Without code execution, follow AGENTS.md section 4.

## Commands

```
python scripts/phase1_receiver.py receive --request <kb>/handoffs/atlas-request.json [--force]
python scripts/phase1_receiver.py status  --request <...>
python scripts/phase1_receiver.py selftest          # synthetic KB + drawings, end to end
python scripts/interlink.py selftest
```

## Limits

- Needs PyMuPDF (as `deploy_atlas.py` does). Drawings that exist only as a URL must be downloaded;
  the request lists them as unresolved and they are not in the atlas.
- The viewer is not yet annotated with KB facts; KB facts point at sheets (anchor
  `plans-atlas.html#sheet=<id>`), and the sheet side is in `interlinks.json`.
- Interlinks are computed on the Plans Atlas side (`interlink.py`); the Estimating bridge only ingests them.
