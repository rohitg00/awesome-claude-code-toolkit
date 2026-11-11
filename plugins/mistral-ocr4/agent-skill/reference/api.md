# Mistral OCR4 + Document AI — endpoint reference

The bundled `scripts/mistral_ocr.py` wraps these. Base URL `https://api.mistral.ai`;
auth `Authorization: Bearer $MISTRAL_API_KEY`. Read this only when you need a field or
endpoint the SKILL.md examples don't cover.

## OCR — `POST /v1/ocr`  (command: `ocr`)

| Field | Notes |
| --- | --- |
| `model` | `mistral-ocr-latest` (default) or a newer `mistral-ocr-*` id from `models-list`. |
| `document` | `{type:"document_url", document_url}` (PDF/PPTX/DOCX URL or data URI), `{type:"image_url", image_url}` (PNG/JPEG/AVIF), or `{type:"file", file_id}`. |
| `pages` | array of 0-indexed page numbers (omit for all). |
| `include_image_base64` | return cropped figures as base64. |
| `image_limit`, `image_min_size` | cap count / min px of extracted images. |
| `table_format` | `null` \| `markdown` \| `html` (OCR4). |
| `extract_header`, `extract_footer` | extract page headers/footers (OCR4). |
| `include_blocks` | paragraph blocks with `bbox` + structural `label` (OCR4). |
| `confidence_scores_granularity` | `page` \| `word` (OCR4). |
| `bbox_annotation_format` | response_format JSON schema for per-region structured extraction. |
| `document_annotation_format` | response_format JSON schema for whole-document structured extraction. |

Response: `pages[]` (`index`, `markdown`, `blocks[]`, `images[]`), optional
`document_annotation`, optional `confidence`, and `usage_info`.

## Files API  (commands: `files-*`)

| Endpoint | Command |
| --- | --- |
| `POST /v1/files` (multipart, `purpose=ocr`) | `files-upload --path` |
| `GET /v1/files` | `files-list` |
| `GET /v1/files/{id}` | `files-get --file-id` |
| `GET /v1/files/{id}/url` | `files-url --file-id [--expiry hours]` |
| `DELETE /v1/files/{id}` | `files-delete --file-id` |

## Batch jobs  (commands: `batch-*`)

`POST /v1/batch/jobs` (`batch-create --payload`), `GET /v1/batch/jobs/{id}`
(`batch-get`), `GET /v1/batch/jobs` (`batch-list`),
`POST /v1/batch/jobs/{id}/cancel` (`batch-cancel`). Use for high-throughput bulk OCR.

## Discovery & passthroughs

- `GET /v1/models` (`models-list`) — discover the current OCR4 model id at runtime.
- `POST /v1/chat/completions` (`chat --payload`) — Document QnA passthrough. Exposed
  for completeness; reasoning belongs to the calling model.
- `request --method --path [--body JSON] [--query JSON]` — generic authenticated
  passthrough so any present/future Mistral endpoint works with no script change.

## Environment

| Var | Default | Purpose |
| --- | --- | --- |
| `MISTRAL_API_KEY` | _(required)_ | Bearer token. |
| `MISTRAL_BASE_URL` | `https://api.mistral.ai` | Override for proxy/self-host. |
| `MISTRAL_OCR_MODEL` | `mistral-ocr-latest` | Default OCR model id. |

The script honors `HTTPS_PROXY` and `SSL_CERT_FILE` from the environment automatically.
