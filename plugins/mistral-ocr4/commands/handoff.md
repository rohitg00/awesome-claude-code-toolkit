# /mistral-ocr4:handoff

Describe and produce the **handoff seam** — the stable, unopinionated extraction
envelope that downstream NTXP pipeline tools (RFP, vendor, invoicing, submittal,
engineering, design) consume from this OCR4 layer. Use this when wiring a new
downstream tool, or to emit a clean envelope for one to pick up.

## The contract

`ocr_process` returns raw Mistral JSON. Downstream tools depend on these fields
and nothing about this layer's internals:

- `pages[].index` — 0-based page number.
- `pages[].markdown` — reading-order text for the page.
- `pages[].blocks[]` — paragraph blocks with `bbox` and structural `label`
  (title, table, list, figure, caption, equation, header, footer, signature, …)
  when `include_blocks: true`.
- `pages[].images[]` — extracted figures (base64 when `include_image_base64`).
- `document_annotation` / per-block annotations — schema-defined fields when a
  `*_annotation_format` was supplied.
- `confidence` — per page/word when requested.
- `usage_info` — pages processed.

Provenance to preserve alongside the envelope: source document id/path, the
`model` used, the page ranges processed, and any annotation schema sent.

## Steps

1. Run extraction per `/mistral-ocr4:ocr` (parallel; schema-driven if fields are
   known).
2. Pass the raw envelope through unchanged, tagged with provenance above.
3. Stop there. **Do not** rank, compare, score, or summarize — that is the
   downstream tool's / calling model's job. This layer's responsibility ends at
   faithful extraction.

## Rules

- Keep the envelope generic; never bake RFP/vendor/invoice-specific judgment
  into this layer.
- Extend reach via `mistral_request`, not by forking the contract.
- This seam is intentionally wide open and context-agnostic so new pipelines
  attach without changing the OCR4 server.
