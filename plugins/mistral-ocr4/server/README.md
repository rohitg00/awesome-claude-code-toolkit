# mistral-ocr4-mcp

A **lean, tool-agnostic MCP server** that exposes the full **Mistral OCR4 +
Document AI** surface as an extraction layer. It is the single, wide-open path
NTXP's current and future document tools use to reach Mistral.

> **Boundary:** Mistral does **extraction only** — OCR, structured annotations,
> bounding boxes, file handling, bulk batch. It never reviews, ranks,
> summarizes, or reasons. All reasoning stays with the calling model (Claude, or
> another model wired in later). The `document_understanding` tool is a raw QnA
> passthrough exposed for completeness, not the place reasoning should happen.

## Setup

```bash
npm install
npm run build        # -> dist/index.js
export MISTRAL_API_KEY=sk-...   # required
node dist/index.js   # stdio MCP server
```

Optional env:

| Var | Default | Purpose |
| --- | --- | --- |
| `MISTRAL_API_KEY` | _(required)_ | Bearer token for the Mistral API. |
| `MISTRAL_BASE_URL` | `https://api.mistral.ai` | Override for self-hosted / proxy. |
| `MISTRAL_OCR_MODEL` | `mistral-ocr-latest` | Default OCR model id. |

Register it with the bundled `../.mcp.json` (plugin install) or the repo-level
`mcp-configs/mistral-ocr4.json`.

## Tools

| Tool | Endpoint | R/W | What it does |
| --- | --- | --- | --- |
| `ocr_process` | `POST /v1/ocr` | W | Core OCR4 extraction: markdown, blocks, tables, bboxes, per-region & whole-document annotations, confidence. |
| `files_upload` | `POST /v1/files` | W | Upload a local file → `file_id`. |
| `files_get_signed_url` | `GET /v1/files/{id}/url` | R | Temporary signed download URL. |
| `files_list` | `GET /v1/files` | R | List stored files. |
| `files_retrieve` | `GET /v1/files/{id}` | R | File metadata. |
| `files_delete` | `DELETE /v1/files/{id}` | W | Delete a stored file. |
| `batch_create` | `POST /v1/batch/jobs` | W | Bulk OCR job. |
| `batch_get` | `GET /v1/batch/jobs/{id}` | R | Batch status/result. |
| `batch_list` | `GET /v1/batch/jobs` | R | List batch jobs. |
| `batch_cancel` | `POST /v1/batch/jobs/{id}/cancel` | W | Cancel a batch. |
| `models_list` | `GET /v1/models` | R | Discover OCR model ids at runtime. |
| `document_understanding` | `POST /v1/chat/completions` | W | Document QnA passthrough (reasoning offload — discouraged). |
| `mistral_request` | _any path_ | R/W | Generic authenticated passthrough — any present/future endpoint, zero code change. |

## The handoff seam (extraction envelope)

Every tool returns **raw Mistral JSON**. Downstream pipeline tools should treat
the `ocr_process` response as a stable, unopinionated envelope:

- `pages[].markdown` — reading-order text per page.
- `pages[].blocks[]` — paragraph-level blocks with `bbox` + structural `label`
  (title, table, list, figure, header, footer, signature, …) when
  `include_blocks: true`.
- `pages[].images[]` — extracted figures (base64 when `include_image_base64`).
- `*_annotation` — structured fields when a `*_annotation_format` schema is sent.
- per-page / per-word `confidence` when requested.
- `usage_info` — pages processed.

This envelope is intentionally generic so RFP / vendor / invoice / submittal /
engineering tools can be layered on later **without changing this server**. Keep
extraction here; keep judgment in the calling model.

## Design notes

- Thin by design — no retries/backoff loops, no batching in code, no response
  interpretation. The agent fans out concurrent `ocr_process` calls for
  parallelism; this server never serializes.
- `mistral_request` guarantees full coverage; the named tools are ergonomic
  shortcuts over the most-used endpoints.
- stdout is the MCP channel; all logs go to stderr.
