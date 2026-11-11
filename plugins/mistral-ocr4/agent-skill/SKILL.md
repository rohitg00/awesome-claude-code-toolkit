---
name: mistral-ocr4
description: Extract text, tables, layout, bounding boxes, and schema-defined fields from PDFs, scans, and images using the Mistral OCR4 + Document AI API. Use when a document must become structured data (construction RFPs/bids/invoices/submittals/drawings, contracts, forms, any PDF/scan). Extraction only - the calling model does all reasoning. Requires MISTRAL_API_KEY and sandbox network egress to api.mistral.ai.
---

# Mistral OCR4 — Document Extraction Skill

This skill turns documents into a structured **extraction envelope** by calling the
Mistral OCR4 + Document AI API from a bundled Python script. There is no local MCP
server here — the skill runs `scripts/mistral_ocr.py` inside the sandbox, which makes
plain HTTPS calls to `api.mistral.ai`.

**Boundary:** Mistral *extracts* (OCR, structured annotations, bounding boxes, file
handling, bulk batch). It does **not** review, compare, score, or decide — that
reasoning is yours. The `chat` passthrough exists for completeness; prefer `ocr` plus
your own analysis.

## Prerequisites (check first)

- `MISTRAL_API_KEY` must be set in the environment. If it isn't, stop and tell the user.
- The sandbox must allow outbound HTTPS to `api.mistral.ai`. On Anthropic Managed
  Agents, use an environment with `unrestricted` networking, or `limited` networking
  with `api.mistral.ai` in `allowed_hosts`. (The basic Messages-API code-execution
  container has **no internet** and cannot reach Mistral — this skill needs egress.)

Verify reachability once before real work:
```
python scripts/mistral_ocr.py models-list
```

## Core usage

Run the script with a subcommand; it prints raw Mistral JSON to stdout and exits
non-zero on error. Pick the smallest input mode that fits:

```bash
# Public URL — no upload needed
python scripts/mistral_ocr.py ocr --document-url "https://example.com/spec.pdf" --include-blocks

# Local file — upload once, then OCR by file_id (reuse the id across page ranges)
python scripts/mistral_ocr.py files-upload --path ./bid.pdf            # -> {"id": "file_..."}
python scripts/mistral_ocr.py ocr --file-id file_... --table-format markdown

# Image
python scripts/mistral_ocr.py ocr --image-url "https://example.com/drawing.png"
```

### Structured field extraction (annotations)

Pull fields directly instead of regexing the markdown. Pass a JSON schema; capture
*what* to extract, never *how to judge it*:

```bash
python scripts/mistral_ocr.py ocr --document-url "https://.../invoice.pdf" \
  --document-annotation-format '{"type":"json_schema","json_schema":{"name":"invoice","schema":{"type":"object","properties":{"invoice_no":{"type":"string"},"total":{"type":"number"},"line_items":{"type":"array","items":{"type":"object","properties":{"description":{"type":"string"},"qty":{"type":"number"},"unit_price":{"type":"number"},"amount":{"type":"number"}}}}}}}}'
```

## The extraction envelope (handoff contract)

`ocr` returns raw Mistral JSON. Treat it as a stable envelope and hand it to whatever
reasons over it:

- `pages[].index`, `pages[].markdown` — reading-order text per page.
- `pages[].blocks[]` — paragraph blocks with `bbox` + structural `label` (title,
  table, list, figure, header, footer, signature, …) when `--include-blocks` is set.
- `pages[].images[]` — extracted figures (base64 with `--include-image-base64`).
- `document_annotation` / per-block annotations — your schema's fields.
- `confidence` — when `--confidence-scores-granularity` is set; never silently trust
  low-confidence numeric cells.
- Preserve **provenance**: source path/URL, page ranges, model, schema used.

## All commands

`ocr`, `files-upload`, `files-list`, `files-get`, `files-url`, `files-delete`,
`batch-create`, `batch-get`, `batch-list`, `batch-cancel`, `models-list`,
`chat` (QnA passthrough — discouraged), `request` (generic passthrough to any
endpoint, so new Mistral features need no script change). Run any subcommand with
`-h` for its flags, and see `reference/api.md` for endpoint/field detail.

## Parallel processing

Extraction is embarrassingly parallel. For many documents or page ranges, launch
multiple `mistral_ocr.py` invocations concurrently (background shells / a small
driver script). For hundreds of documents, use `batch-create` instead of hand-rolled
fan-out and poll `batch-get`.

## Anti-patterns

- Asking Mistral to summarize, compare, or judge — use `ocr` and reason yourself.
- Re-uploading the same local file for each page range (upload once, reuse `file_id`).
- Hand-parsing markdown for fields a `--document-annotation-format` schema would extract.
- Editing extracted values before handoff; pass them through faithfully.
- Running in a no-egress sandbox and reporting a network error as a skill failure —
  it's a networking-config issue (see Prerequisites).

## Checklist

- [ ] `MISTRAL_API_KEY` set and `api.mistral.ai` reachable (`models-list` works).
- [ ] Input mode chosen deliberately (URL vs upload→file_id vs base64).
- [ ] `--include-blocks` / annotation schema used when structure or fields are needed.
- [ ] Multiple docs / page ranges run in parallel; bulk uses `batch-create`.
- [ ] Raw envelope handed off with provenance; reasoning kept separate.
