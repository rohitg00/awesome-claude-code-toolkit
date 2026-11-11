/**
 * Thin authenticated client for the Mistral platform API.
 *
 * Deliberately minimal: it does auth, JSON/multipart transport, and error
 * shaping - nothing else. No retries-with-backoff loops, no batching, no
 * response interpretation. Parallelism is left entirely to the caller (the
 * agent fans out concurrent tool calls); this client never serializes.
 *
 * Mistral is an EXTRACTION engine here. This module intentionally contains no
 * reasoning, summarization, or document-evaluation logic.
 */

import { readFile } from "node:fs/promises";
import { basename } from "node:path";

const DEFAULT_BASE_URL = "https://api.mistral.ai";

export class MistralError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "MistralError";
    this.status = status;
    this.body = body;
  }
}

export interface MistralClientOptions {
  apiKey: string;
  baseUrl?: string;
}

export class MistralClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;

  constructor(opts: MistralClientOptions) {
    if (!opts.apiKey) {
      throw new Error("MISTRAL_API_KEY is not set");
    }
    this.apiKey = opts.apiKey;
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
  }

  private url(path: string): string {
    return path.startsWith("http")
      ? path
      : `${this.baseUrl}/${path.replace(/^\/+/, "")}`;
  }

  private authHeaders(extra: Record<string, string> = {}): Record<string, string> {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      Accept: "application/json",
      ...extra,
    };
  }

  private async parse(res: Response): Promise<unknown> {
    const text = await res.text();
    let body: unknown = text;
    if (text) {
      try {
        body = JSON.parse(text);
      } catch {
        body = text;
      }
    }
    if (!res.ok) {
      const message =
        typeof body === "object" && body !== null && "message" in body
          ? String((body as Record<string, unknown>).message)
          : `Mistral API error ${res.status} ${res.statusText}`;
      throw new MistralError(res.status, message, body);
    }
    return body;
  }

  /**
   * Generic JSON request - the foundation every typed method (and the
   * `mistral_request` passthrough tool) is built on. Any present or future
   * Mistral endpoint is reachable through this with zero code change.
   */
  async request(
    method: string,
    path: string,
    options: { body?: unknown; query?: Record<string, unknown> } = {}
  ): Promise<unknown> {
    let url = this.url(path);
    if (options.query) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(options.query)) {
        if (v === undefined || v === null) continue;
        qs.append(k, String(v));
      }
      const q = qs.toString();
      if (q) url += (url.includes("?") ? "&" : "?") + q;
    }

    const hasBody = options.body !== undefined && method.toUpperCase() !== "GET";
    const res = await fetch(url, {
      method: method.toUpperCase(),
      headers: this.authHeaders(
        hasBody ? { "Content-Type": "application/json" } : {}
      ),
      body: hasBody ? JSON.stringify(options.body) : undefined,
    });
    return this.parse(res);
  }

  // --- OCR + structured annotations (one endpoint covers all of it) ---------
  async ocr(payload: Record<string, unknown>): Promise<unknown> {
    return this.request("POST", "/v1/ocr", { body: payload });
  }

  // --- Files API (read + write) ---------------------------------------------
  /** Upload a local file. Uses multipart/form-data per the Files API. */
  async uploadFile(filePath: string, purpose = "ocr"): Promise<unknown> {
    const data = await readFile(filePath);
    const form = new FormData();
    form.append("purpose", purpose);
    // Node's global Blob accepts a Uint8Array; copy into a fresh array to
    // satisfy the BlobPart typing across Node versions.
    const blob = new Blob([new Uint8Array(data)]);
    form.append("file", blob, basename(filePath));

    const res = await fetch(this.url("/v1/files"), {
      method: "POST",
      headers: this.authHeaders(),
      body: form,
    });
    return this.parse(res);
  }

  async listFiles(query: Record<string, unknown> = {}): Promise<unknown> {
    return this.request("GET", "/v1/files", { query });
  }

  async retrieveFile(fileId: string): Promise<unknown> {
    return this.request("GET", `/v1/files/${encodeURIComponent(fileId)}`);
  }

  async deleteFile(fileId: string): Promise<unknown> {
    return this.request("DELETE", `/v1/files/${encodeURIComponent(fileId)}`);
  }

  async getSignedUrl(fileId: string, expiry?: number): Promise<unknown> {
    return this.request("GET", `/v1/files/${encodeURIComponent(fileId)}/url`, {
      query: expiry === undefined ? {} : { expiry },
    });
  }

  // --- Batch jobs (bulk parallel OCR) ---------------------------------------
  async createBatch(payload: Record<string, unknown>): Promise<unknown> {
    return this.request("POST", "/v1/batch/jobs", { body: payload });
  }

  async getBatch(jobId: string): Promise<unknown> {
    return this.request("GET", `/v1/batch/jobs/${encodeURIComponent(jobId)}`);
  }

  async listBatches(query: Record<string, unknown> = {}): Promise<unknown> {
    return this.request("GET", "/v1/batch/jobs", { query });
  }

  async cancelBatch(jobId: string): Promise<unknown> {
    return this.request(
      "POST",
      `/v1/batch/jobs/${encodeURIComponent(jobId)}/cancel`
    );
  }

  // --- Discovery -------------------------------------------------------------
  async listModels(): Promise<unknown> {
    return this.request("GET", "/v1/models");
  }

  // --- Document QnA / understanding passthrough (chat over a document) -------
  async chat(payload: Record<string, unknown>): Promise<unknown> {
    return this.request("POST", "/v1/chat/completions", { body: payload });
  }
}
