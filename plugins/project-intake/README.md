# project-intake

The ingestion front door of the **construction-doc-intelligence** pipeline. It takes
a set of project documents, runs **Mistral OCR4** across them, writes a structured
**project dossier** into a folder auto-named after the project, and emits a
**handoff.json** that hands control to the orchestrator for the next step.

Separation of concerns (dependencies point downward only):

```
project-intake (this plugin)  ── uses ──▶  mistral-ocr4 skill/MCP   (extraction)
        │  writes
        ▼
projects/<slug>/  (dossier + handoff.json)  ── consumed by ──▶  construction-doc-intelligence (orchestrator)
```

- The **mistral-ocr4 skill** is reusable capability (how to call OCR4). This plugin
  *uses* it — `scripts/build_dossier.py` shells out to its client; no OCR code is
  duplicated here.
- This **plugin** owns the workflow side effects: folder naming, the dossier, and the
  handoff.
- The **orchestrator** only knows `handoff.json` — it never reaches into intake.

## What it produces

```
projects/<slug>/
  project.json              # title, number, owner, location, identity source, doc inventory
  _raw/<docid>.ocr.json     # raw OCR envelopes, unmodified (the handoff seam)
  extracts/
    products.json           # every specified product (with provenance)
    schedules.json          # finish / equipment / door / … schedules as rows
    contacts.json           # owner, A/E, GC, subs, suppliers
    scope-items.json
    requirements.json       # verbatim binding requirements with page refs
    product-tables.csv      # every table block (markdown + page + bbox)
  index.md                  # human-readable dossier summary
  handoff.json              # the orchestrator contract (schemas/handoff.schema.json)
```

Every record carries provenance (`_doc`, page, bbox) so downstream tools can cite and
verify, and low-confidence regions/failed docs land in `handoff.json.needs_human_review`.

## Run it

```bash
# Plan only — no API key, no calls
python scripts/build_dossier.py --inputs ./bid.pdf "https://host/rfp.pdf" --dry-run

# Real run — needs MISTRAL_API_KEY in the environment
python scripts/build_dossier.py --inputs ./docs/*.pdf --project "Lincoln Reroof" --model mistral-ocr-4
```

Key flags: `--inputs` (paths and/or URLs), `--project` (explicit title; otherwise
extracted from the title block / RFP cover, then filename), `--out` (default
`projects`), `--model`, `--client` (path to the mistral-ocr4 `mistral_ocr.py`),
`--next-step`, `--created-at`, `--dry-run`.

## How the handoff is automatic

- **Artifact (always):** `handoff.json` is the source of truth the orchestrator reads.
- **Hook (chat sessions):** `hooks/announce-handoff.js` fires after a real build and
  injects a note telling the orchestrator to proceed with `next_step`.
- **Subagent return (agent loop):** the `intake-agent` returns the handoff object so a
  calling orchestrator routes onward with no file polling.

## Boundaries

Intake **gathers and hands off** — it never compares, ranks, scores, or decides.
Cross-document dedup/normalization of products and contacts is the orchestrator's job.
Mistral extracts; the calling model reasons.

> Networking: real runs need egress to `api.mistral.ai` and a valid `MISTRAL_API_KEY`
> (same requirement as the mistral-ocr4 skill).
