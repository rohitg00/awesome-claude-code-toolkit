# /project-intake:ingest

Ingest a set of project documents into a named dossier and hand off to the
construction-doc-intelligence orchestrator. Extraction runs on Mistral OCR4 via the
`mistral-ocr4` skill; this command only orchestrates, names, gathers, and hands off.

## Usage

```
/project-intake:ingest <folder | path1 path2 url ...> [--project "Title"]
```

## Steps

1. **Resolve the project title** (for the folder name), in order: an explicit
   `--project`, else extract it from the first document's title block / RFP cover
   (the `schemas/identity.schema.json` annotation), else fall back to the file/folder
   name. Slugify → `projects/<slug>/`. Re-running the same set updates the same folder.
2. **Extract in parallel.** For each document call the `mistral-ocr4` client with
   `--include-blocks --table-format markdown` and `schemas/dossier.schema.json` as the
   `--document-annotation-format`, so one pass returns text, tables (block-level with
   bbox), and structured products / schedules / contacts / scope / requirements. Local
   files are uploaded once (`files-upload`) then OCR'd by `file_id`. For hundreds of
   docs, switch to `batch-create`.
3. **Build the dossier.** `scripts/build_dossier.py` writes:
   `project.json`, `_raw/<docid>.ocr.json` (unmodified envelopes), `extracts/products.json`,
   `extracts/schedules.json`, `extracts/contacts.json`, `extracts/scope-items.json`,
   `extracts/requirements.json`, `extracts/product-tables.csv`, and `index.md` — every
   record tagged with provenance (`_doc`, page, bbox).
4. **Emit the handoff.** Write `projects/<slug>/handoff.json` (see
   `schemas/handoff.schema.json`) with status, project identity, document inventory,
   extract paths, counts, and `next_step: construction-doc-pipeline:review`. The plugin
   hook announces completion so the orchestrator can pick it up automatically.

## Running the builder directly

```bash
# Dry run (no API key, prints the plan)
python plugins/project-intake/scripts/build_dossier.py --inputs ./bid.pdf "https://.../rfp.pdf" --dry-run

# Real run (needs MISTRAL_API_KEY)
python plugins/project-intake/scripts/build_dossier.py --inputs ./docs/*.pdf --project "Lincoln Reroof" --model mistral-ocr-4
```

## Rules

- Mistral extracts; the orchestrator/skills reason. This command never compares,
  scores, or decides — it gathers and hands off.
- Don't re-implement OCR — it reuses the `mistral-ocr4` client.
- Cross-doc dedup/normalization of products/contacts is the orchestrator's job, not
  intake's; intake preserves everything verbatim with provenance.
- Always produce `handoff.json`, even on partial/failed extraction (status reflects it).
