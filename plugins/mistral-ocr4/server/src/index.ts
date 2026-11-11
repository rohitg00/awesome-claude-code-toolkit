#!/usr/bin/env node
/**
 * mistral-ocr4-mcp
 *
 * A lean, tool-agnostic MCP access layer over Mistral OCR4 + Document AI.
 *
 * Design contract:
 *   - Mistral does EXTRACTION only (OCR, structured annotations, bbox, file
 *     handling, bulk batch). It never reviews, ranks, summarizes, or reasons.
 *   - The calling model (Claude, or another model wired in later) owns ALL
 *     reasoning. The QnA/chat passthrough exists for completeness but the skill
 *     instructs callers to keep reasoning on their side.
 *   - Every tool is a THIN wrapper over one endpoint. Nothing here duplicates
 *     filesystem, PDF, or reasoning tools that already exist elsewhere.
 *   - `mistral_request` is the escape hatch: any present/future Mistral endpoint
 *     is reachable with zero code change ("wide open and unlimited").
 *
 * Output of every tool is the raw Mistral JSON, so downstream pipeline tools
 * consume a stable, unopinionated extraction envelope. See HANDOFF in README.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { MistralClient, MistralError } from "./mistral.js";

const API_KEY = process.env.MISTRAL_API_KEY ?? "";
const BASE_URL = process.env.MISTRAL_BASE_URL || undefined;
const DEFAULT_OCR_MODEL = process.env.MISTRAL_OCR_MODEL || "mistral-ocr-latest";

// Construct lazily: the MCP server must complete initialize/tools-list without
// credentials, so we only build the client on first tool use (guard() ensures a
// key is present before any call site runs).
let _client: MistralClient | undefined;
function getClient(): MistralClient {
  if (!_client) {
    _client = new MistralClient({ apiKey: API_KEY, baseUrl: BASE_URL });
  }
  return _client;
}

type ToolResult = {
  content: { type: "text"; text: string }[];
  isError?: boolean;
};

function ok(data: unknown): ToolResult {
  const text =
    typeof data === "string" ? data : JSON.stringify(data, null, 2);
  return { content: [{ type: "text", text }] };
}

function fail(err: unknown): ToolResult {
  let text: string;
  if (err instanceof MistralError) {
    text = `Mistral API error (${err.status}): ${err.message}\n${JSON.stringify(
      err.body,
      null,
      2
    )}`;
  } else if (err instanceof Error) {
    text = `${err.name}: ${err.message}`;
  } else {
    text = `Unknown error: ${String(err)}`;
  }
  return { content: [{ type: "text", text }], isError: true };
}

/** Wrap a handler so a missing key fails clearly and errors never crash the server. */
function guard<T>(fn: (args: T) => Promise<ToolResult>) {
  return async (args: T): Promise<ToolResult> => {
    if (!API_KEY) {
      return fail(
        new Error(
          "MISTRAL_API_KEY is not set. Configure it in the MCP server env before calling extraction tools."
        )
      );
    }
    try {
      return await fn(args);
    } catch (err) {
      return fail(err);
    }
  };
}

const server = new McpServer({
  name: "mistral-ocr4",
  version: "1.0.0",
});

// ---------------------------------------------------------------------------
// OCR + structured annotations (the core extraction tool)
// ---------------------------------------------------------------------------
server.tool(
  "ocr_process",
  "Run Mistral OCR4 on a document or image and return structured extraction " +
    "(markdown text, blocks, tables, bounding boxes, per-region/document " +
    "annotations, confidence). This is EXTRACTION ONLY - do not ask it to " +
    "reason about the content. Provide exactly one input source: `document_url` " +
    "(PDF/PPTX/DOCX URL), `image_url` (PNG/JPEG/AVIF URL), `file_id` (from " +
    "files_upload), `document_base64`/`image_base64`, or a fully-formed " +
    "`document` object for advanced cases.",
  {
    model: z
      .string()
      .optional()
      .describe(
        `OCR model id. Defaults to "${DEFAULT_OCR_MODEL}". Use models_list to discover OCR4/newer ids.`
      ),
    document_url: z.string().optional().describe("URL of a PDF/PPTX/DOCX to OCR."),
    image_url: z.string().optional().describe("URL of a PNG/JPEG/AVIF to OCR."),
    file_id: z
      .string()
      .optional()
      .describe("Mistral file id (from files_upload) to OCR."),
    document_base64: z
      .string()
      .optional()
      .describe("Base64-encoded document (data URI or raw base64)."),
    image_base64: z
      .string()
      .optional()
      .describe("Base64-encoded image (data URI or raw base64)."),
    document: z
      .record(z.any())
      .optional()
      .describe(
        "Fully-formed Mistral `document` object. If provided, the convenience " +
          "*_url/*_base64/file_id fields are ignored."
      ),
    pages: z
      .array(z.number().int())
      .optional()
      .describe("Specific 0-indexed pages to process (omit for all)."),
    include_image_base64: z
      .boolean()
      .optional()
      .describe("Return cropped images as base64 in the response."),
    image_limit: z.number().int().optional().describe("Max images to extract."),
    image_min_size: z
      .number()
      .int()
      .optional()
      .describe("Minimum height/width (px) for an extracted image."),
    table_format: z
      .enum(["null", "markdown", "html"])
      .optional()
      .describe("How tables are serialized (OCR4)."),
    extract_header: z.boolean().optional().describe("Extract page headers (OCR4)."),
    extract_footer: z.boolean().optional().describe("Extract page footers (OCR4)."),
    include_blocks: z
      .boolean()
      .optional()
      .describe("Return paragraph-level blocks with bboxes + labels (OCR4)."),
    confidence_scores_granularity: z
      .enum(["page", "word"])
      .optional()
      .describe("Granularity of confidence scores (OCR4)."),
    bbox_annotation_format: z
      .record(z.any())
      .optional()
      .describe(
        "JSON-schema (response_format style) for per-region structured " +
          "extraction. Pure extraction - define WHAT fields to pull, not how to judge them."
      ),
    document_annotation_format: z
      .record(z.any())
      .optional()
      .describe(
        "JSON-schema (response_format style) for whole-document structured extraction."
      ),
  },
  guard(async (a) => {
    let document = a.document;
    if (!document) {
      if (a.document_url) document = { type: "document_url", document_url: a.document_url };
      else if (a.image_url) document = { type: "image_url", image_url: a.image_url };
      else if (a.file_id) document = { type: "file", file_id: a.file_id };
      else if (a.document_base64)
        document = { type: "document_url", document_url: a.document_base64 };
      else if (a.image_base64)
        document = { type: "image_url", image_url: a.image_base64 };
    }
    if (!document) {
      throw new Error(
        "No input. Provide one of: document_url, image_url, file_id, document_base64, image_base64, or document."
      );
    }
    const payload: Record<string, unknown> = {
      model: a.model ?? DEFAULT_OCR_MODEL,
      document,
    };
    const opt: (keyof typeof a)[] = [
      "pages",
      "include_image_base64",
      "image_limit",
      "image_min_size",
      "table_format",
      "extract_header",
      "extract_footer",
      "include_blocks",
      "confidence_scores_granularity",
      "bbox_annotation_format",
      "document_annotation_format",
    ];
    for (const k of opt) if (a[k] !== undefined) payload[k] = a[k];
    return ok(await getClient().ocr(payload));
  })
);

// ---------------------------------------------------------------------------
// Files API (read + write)
// ---------------------------------------------------------------------------
server.tool(
  "files_upload",
  "Upload a local file to Mistral storage so it can be OCR'd by file_id " +
    "(use for files too large for inline base64, or to avoid re-uploading). " +
    "Returns the file object including its id.",
  {
    path: z.string().describe("Absolute path to the local file to upload."),
    purpose: z
      .string()
      .optional()
      .describe('Upload purpose. Defaults to "ocr".'),
  },
  guard(async (a) => ok(await getClient().uploadFile(a.path, a.purpose ?? "ocr")))
);

server.tool(
  "files_get_signed_url",
  "Get a temporary signed download URL for an uploaded file id (e.g. to pass " +
    "as document_url to ocr_process, or to retrieve batch output files).",
  {
    file_id: z.string().describe("The Mistral file id."),
    expiry: z
      .number()
      .int()
      .optional()
      .describe("Expiry in hours (optional)."),
  },
  guard(async (a) => ok(await getClient().getSignedUrl(a.file_id, a.expiry)))
);

server.tool(
  "files_list",
  "List files stored in your Mistral account (read).",
  {
    page: z.number().int().optional().describe("Page number."),
    page_size: z.number().int().optional().describe("Items per page."),
    purpose: z.string().optional().describe("Filter by purpose, e.g. ocr."),
  },
  guard(async (a) =>
    ok(
      await getClient().listFiles({
        page: a.page,
        page_size: a.page_size,
        purpose: a.purpose,
      })
    )
  )
);

server.tool(
  "files_retrieve",
  "Retrieve metadata for one stored file by id (read).",
  { file_id: z.string().describe("The Mistral file id.") },
  guard(async (a) => ok(await getClient().retrieveFile(a.file_id)))
);

server.tool(
  "files_delete",
  "Delete a stored file by id (write). Use to clean up after extraction.",
  { file_id: z.string().describe("The Mistral file id.") },
  guard(async (a) => ok(await getClient().deleteFile(a.file_id)))
);

// ---------------------------------------------------------------------------
// Batch jobs (bulk / parallel OCR at scale)
// ---------------------------------------------------------------------------
server.tool(
  "batch_create",
  "Create a batch job for bulk OCR (high-throughput, many documents). Provide " +
    "the batch payload (input_files, endpoint, model, etc.) per the Mistral " +
    "Batch API. For a handful of docs, prefer parallel ocr_process calls instead.",
  { payload: z.record(z.any()).describe("Batch job creation payload.") },
  guard(async (a) => ok(await getClient().createBatch(a.payload)))
);

server.tool(
  "batch_get",
  "Get the status/result of a batch job by id (read).",
  { job_id: z.string().describe("The batch job id.") },
  guard(async (a) => ok(await getClient().getBatch(a.job_id)))
);

server.tool(
  "batch_list",
  "List batch jobs (read).",
  {
    page: z.number().int().optional().describe("Page number."),
    page_size: z.number().int().optional().describe("Items per page."),
    status: z.string().optional().describe("Filter by status."),
  },
  guard(async (a) =>
    ok(
      await getClient().listBatches({
        page: a.page,
        page_size: a.page_size,
        status: a.status,
      })
    )
  )
);

server.tool(
  "batch_cancel",
  "Cancel a running batch job by id (write).",
  { job_id: z.string().describe("The batch job id.") },
  guard(async (a) => ok(await getClient().cancelBatch(a.job_id)))
);

// ---------------------------------------------------------------------------
// Discovery
// ---------------------------------------------------------------------------
server.tool(
  "models_list",
  "List available Mistral models (read). Use to discover the current OCR4 / " +
    "newest OCR model id at runtime instead of hardcoding it.",
  {},
  guard(async () => ok(await getClient().listModels()))
);

// ---------------------------------------------------------------------------
// Document QnA / understanding passthrough
// (exposed for completeness - reasoning belongs to the calling model)
// ---------------------------------------------------------------------------
server.tool(
  "document_understanding",
  "Raw passthrough to Mistral chat completions with a document attached " +
    "(Document QnA). EXPOSED FOR COMPLETENESS - by design, reasoning stays " +
    "with the calling model, so prefer ocr_process + your own analysis. Use " +
    "only when explicitly instructed to offload understanding to Mistral. " +
    "Provide the full chat payload (model, messages with document_url content).",
  { payload: z.record(z.any()).describe("Chat completions payload.") },
  guard(async (a) => ok(await getClient().chat(a.payload)))
);

// ---------------------------------------------------------------------------
// Generic passthrough - the tool-agnostic escape hatch
// ---------------------------------------------------------------------------
server.tool(
  "mistral_request",
  "Tool-agnostic authenticated passthrough to ANY Mistral API endpoint. Use " +
    "for endpoints not covered by a dedicated tool, or new endpoints added by " +
    "Mistral after this server shipped. Auth is handled for you.",
  {
    method: z
      .enum(["GET", "POST", "PUT", "PATCH", "DELETE"])
      .describe("HTTP method."),
    path: z
      .string()
      .describe('API path, e.g. "/v1/ocr" or a full https URL.'),
    body: z
      .record(z.any())
      .optional()
      .describe("JSON request body (for non-GET)."),
    query: z
      .record(z.any())
      .optional()
      .describe("Query string parameters."),
  },
  guard(async (a) =>
    ok(await getClient().request(a.method, a.path, { body: a.body, query: a.query }))
  )
);

// ---------------------------------------------------------------------------
// Transport + graceful shutdown
// ---------------------------------------------------------------------------
async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // Log to stderr only - stdout is the MCP channel.
  console.error("mistral-ocr4 MCP server ready (stdio).");
}

for (const sig of ["SIGINT", "SIGTERM"] as const) {
  process.on(sig, () => {
    void server.close().finally(() => process.exit(0));
  });
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
