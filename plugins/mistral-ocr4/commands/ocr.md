# /mistral-ocr4:ocr

Extract text, tables, layout, and structured fields from one or more documents
with Mistral OCR4, then hand off the result. Extraction only — reasoning stays
with you, the calling model.

## Steps

1. **Resolve inputs.** Collect every target document (paths, URLs, or attached
   files). For each, pick the input mode:
   - Public URL → use `document_url` / `image_url`.
   - Local file → `files_upload` once, then OCR by `file_id`.
   - Small inline bytes → `document_base64` / `image_base64`.
2. **Decide the output shape.**
   - Need layout/regions? set `include_blocks: true`.
   - Need specific fields? supply a `document_annotation_format` (and/or
     `bbox_annotation_format`) JSON schema describing **what** to capture.
   - Need tables as data? set `table_format: "markdown"` or `"html"`.
3. **Run in parallel.** Issue all `ocr_process` calls in a single batch. For one
   large doc, split by `pages` ranges and run them concurrently. For hundreds of
   docs, use `batch_create` and poll `batch_get`.
4. **Hand off the envelope.** Return the raw `ocr_process` JSON faithfully
   (`pages[].markdown`, `pages[].blocks[]`, annotations, `confidence`). Add any
   of your own analysis clearly separated — never edit extracted values.
5. **Clean up** uploaded files with `files_delete` when they were one-shot.

## Output

The structured extraction envelope per document, ready for downstream
RFP/vendor/invoice/submittal/engineering tooling — plus your separate reasoning,
if asked.

## Rules

- Mistral never reasons. Don't route evaluation/summarization through
  `document_understanding` unless explicitly told to offload it.
- Upload a local file once; reuse its `file_id` across page ranges.
- Use `models_list` to discover the current OCR4 model id; don't guess.
- Use `mistral_request` for any endpoint without a dedicated tool.
