---
name: mistral-ocr4
description: Seamless tool-call and handoff to the Mistral OCR4 + Document AI MCP for extracting text, tables, bounding boxes, and structured fields from construction, RFP, vendor, invoice, submittal, and engineering documents - extraction only, with all reasoning kept on the calling model
---

# Mistral OCR4 — extraction layer & handoff

This skill is the thin, wide-open path to **Mistral OCR4 + Document AI** via the
`mistral-ocr4` MCP server. It exists to do one job extremely well: turn a
document (PDF, image, scan, drawing, spreadsheet export) into a clean, structured
**extraction envelope** and hand that off — fast, in parallel, with no fuss.

**The one rule that shapes everything:**
> **Mistral extracts. The calling model reasons.**
> OCR4 pulls text, tables, layout, bounding boxes, and schema-defined fields off
> the page. It does **not** evaluate, compare, score, summarize, or decide.
> Comparing bids, flagging an out-of-scope submittal, reconciling an invoice —
> that is the calling model's job (Claude today, or whatever model a downstream
> pipeline tool wires in tomorrow).

## When this skill fires

Reach for it whenever a document needs to become data — usually signalled by
ordinary conversational wording, not a tool name:

- "read / parse / pull / grab / scrape / digitize / OCR this PDF / scan / drawing"
- "what does this spec / submittal / RFP / addendum say"
- "get the line items / quantities / unit prices off this quote / invoice"
- "extract the bid schedule / door schedule / equipment list"
- a document path/URL appears and the user clearly wants its contents as data

The plugin's `UserPromptSubmit` hook (`detect-document-intent.js`) surfaces these
as a hint; you still decide. Don't fire for prompts that are purely about
reasoning over data already in context.

## Tool map (pick the smallest tool that does the job)

| Need | Tool |
| --- | --- |
| OCR a doc/image and get structured output | `ocr_process` |
| Pull specific fields by schema | `ocr_process` + `bbox_annotation_format` / `document_annotation_format` |
| File too big for inline base64, or reused often | `files_upload` → use returned `file_id` |
| Turn a `file_id` into a URL | `files_get_signed_url` |
| Manage stored files | `files_list`, `files_retrieve`, `files_delete` |
| Hundreds/thousands of docs | `batch_create` → `batch_get` (poll) → `batch_cancel` |
| Find the current OCR4 model id | `models_list` |
| An endpoint with no dedicated tool / a brand-new one | `mistral_request` |
| Offload understanding to Mistral (rare, discouraged) | `document_understanding` |

### Choosing the input mode (be decisive — agentic independence)

- **Public URL** available → pass `document_url` / `image_url` directly. No upload.
- **Local file** → `files_upload` once, then `ocr_process` with `file_id`.
  Reuse the `file_id` across page-range calls instead of re-uploading.
- **Small inline bytes** → `document_base64` / `image_base64`.
- **Model id** → default `mistral-ocr-latest`. If a task needs OCR4-only
  features (blocks/bboxes/headers/footers/confidence) and the default ever
  lacks them, call `models_list` and pick the newest `mistral-ocr-*` id rather
  than guessing.

## The handoff seam (the stable contract)

`ocr_process` returns **raw Mistral JSON**. Treat it as a generic envelope and
hand it off unchanged so downstream tools never depend on this skill's internals:

- `pages[].markdown` — reading-order text per page.
- `pages[].blocks[]` — paragraph blocks with `bbox` + structural `label`
  (title, table, list, figure, caption, equation, header, footer, signature, …)
  when `include_blocks: true`.
- `pages[].images[]` — extracted figures (base64 when `include_image_base64`).
- `document_annotation` / per-block `bbox` annotations — structured fields when
  you supplied a `*_annotation_format` schema.
- `confidence` — per page or per word when `confidence_scores_granularity` is set.
- `usage_info` — pages processed.

When you hand results to the user or another tool, pass the extraction through
faithfully. Add your own reasoning **alongside** it, clearly separated — never
mutate the extracted values to "fix" them.

## Parallel processing (default to it)

OCR is embarrassingly parallel and the server never serializes — so fan out:

- **Many documents** → issue multiple `ocr_process` calls in one batch of tool
  calls rather than one-at-a-time.
- **One large document** → split by `pages` ranges and run the ranges
  concurrently, then stitch by page index.
- **Bulk / overnight scale** (hundreds+) → use `batch_create` instead of
  hand-rolling fan-out; poll `batch_get`.
- Keep each call independent; don't thread state between them.

## Structured extraction (annotations)

Use `*_annotation_format` to pull fields directly instead of regexing markdown.
Define **what to capture**, never **how to judge it**:

- **Invoice / quote**: vendor, invoice_no, date, terms, line_items[{description,
  qty, unit, unit_price, amount}], subtotal, tax, total.
- **RFP / solicitation**: solicitation_no, due_date, scope_items[], required
  submittals[], evaluation_criteria[] (as written), addenda[].
- **Submittal**: spec_section, product, manufacturer, model_no, status_stamp.
- **Door/equipment/finish schedule**: rows of the schedule table as records.
- **Engineering/design drawings**: title_block{sheet_no, title, rev, date,
  scale}, general_notes[], callouts[].

Capture verbatim. Leave "does this comply / is this the low bid / is this in
scope" to the calling model.

## Boundaries — stay lean, don't duplicate

- **No reasoning in Mistral.** Don't route evaluation/comparison/summarization
  through `document_understanding` unless explicitly told to offload it.
- **Don't reinvent file I/O.** Reading local bytes for upload is fine; browsing,
  searching, or writing project files is the filesystem tools' job.
- **Don't pre-process images** here (deskew, crop, enhance) — OCR4 handles
  layout; a dedicated image tool handles editing if ever needed.
- **Don't hardcode** what `models_list` / `mistral_request` can discover.

## Anti-patterns

- Calling `ocr_process` sequentially across a stack of files (fan out instead).
- Re-uploading the same local file for each page range (upload once, reuse `file_id`).
- Asking Mistral to "summarize" or "tell me if this bid is compliant."
- Hand-parsing markdown for fields a `*_annotation_format` schema would extract.
- Editing extracted values before handoff.

## Checklist

- [ ] Input mode chosen deliberately (URL vs file_id vs base64).
- [ ] Multiple docs / page ranges issued in parallel.
- [ ] `include_blocks` / annotation schema set when structure or fields are needed.
- [ ] Extraction handed off as the raw envelope; reasoning kept separate.
- [ ] No reasoning offloaded to Mistral unless explicitly requested.
- [ ] Used `mistral_request` (not a workaround) for any uncovered endpoint.
