#!/usr/bin/env node
/**
 * DeepRFP MCP custom connector.
 *
 * Exposes DeepRFP's AI procurement capabilities — RFP/tender analysis,
 * proposal drafting, questionnaire automation, compliance matrices, and
 * proposal review — as Model Context Protocol tools.
 *
 * DeepRFP does not publish an official public API. The HTTP layer is fully
 * configurable so this connector can target whatever endpoint your DeepRFP
 * account exposes (or a compatible proxy). Configure it with:
 *
 *   DEEPRFP_API_KEY        (required) bearer token for the DeepRFP account
 *   DEEPRFP_API_BASE_URL   (optional) defaults to https://api.deeprfp.com/v1
 *   DEEPRFP_TIMEOUT_MS     (optional) request timeout, defaults to 120000
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_KEY = process.env.DEEPRFP_API_KEY;
const BASE_URL = (process.env.DEEPRFP_API_BASE_URL ?? "https://api.deeprfp.com/v1").replace(/\/+$/, "");
const TIMEOUT_MS = Number(process.env.DEEPRFP_TIMEOUT_MS ?? 120_000);

if (!API_KEY) {
  console.error(
    "[deeprfp] DEEPRFP_API_KEY is not set. The server will start but every tool call will fail until it is provided."
  );
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
}

async function deeprfpRequest(path: string, opts: RequestOptions = {}): Promise<unknown> {
  if (!API_KEY) {
    throw new Error("DEEPRFP_API_KEY is not configured. Set it in the MCP server env before calling tools.");
  }

  const url = new URL(`${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`);
  for (const [key, value] of Object.entries(opts.query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      method: opts.method ?? "GET",
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        Accept: "application/json",
        ...(opts.body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      signal: controller.signal,
    });

    const text = await res.text();
    let parsed: unknown = text;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch {
      /* leave as raw text */
    }

    if (!res.ok) {
      throw new Error(`DeepRFP API ${res.status} ${res.statusText}: ${typeof parsed === "string" ? parsed : JSON.stringify(parsed)}`);
    }
    return parsed;
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error(`DeepRFP request timed out after ${TIMEOUT_MS}ms (${path}).`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

function ok(data: unknown) {
  return {
    content: [{ type: "text" as const, text: typeof data === "string" ? data : JSON.stringify(data, null, 2) }],
  };
}

function fail(err: unknown) {
  const message = err instanceof Error ? err.message : String(err);
  return {
    isError: true,
    content: [{ type: "text" as const, text: `Error: ${message}` }],
  };
}

const server = new McpServer({
  name: "deeprfp",
  version: "0.1.0",
});

// ---------------------------------------------------------------------------
// Projects — an RFP/tender workspace holding documents and generated content.
// ---------------------------------------------------------------------------

server.tool(
  "deeprfp_list_projects",
  "List RFP/tender projects in the DeepRFP account, optionally filtered by status.",
  {
    status: z.enum(["active", "archived", "won", "lost", "all"]).optional().describe("Filter by project status."),
    limit: z.number().int().min(1).max(100).optional().describe("Max projects to return (default 25)."),
  },
  async ({ status, limit }) => {
    try {
      return ok(await deeprfpRequest("/projects", { query: { status, limit } }));
    } catch (err) {
      return fail(err);
    }
  }
);

server.tool(
  "deeprfp_get_project",
  "Retrieve a single RFP/tender project, including its documents and generated artifacts.",
  {
    project_id: z.string().describe("The DeepRFP project identifier."),
  },
  async ({ project_id }) => {
    try {
      return ok(await deeprfpRequest(`/projects/${encodeURIComponent(project_id)}`));
    } catch (err) {
      return fail(err);
    }
  }
);

server.tool(
  "deeprfp_create_project",
  "Create a new RFP/tender project to work on a specific opportunity.",
  {
    name: z.string().describe("Project name, e.g. the tender title."),
    buyer: z.string().optional().describe("Issuing authority / buyer organization."),
    deadline: z.string().optional().describe("Submission deadline (ISO 8601 date)."),
    rfp_text: z.string().optional().describe("Full RFP/tender text to attach to the project."),
    rfp_url: z.string().url().optional().describe("URL of the published tender document."),
  },
  async (args) => {
    try {
      return ok(await deeprfpRequest("/projects", { method: "POST", body: args }));
    } catch (err) {
      return fail(err);
    }
  }
);

// ---------------------------------------------------------------------------
// Analyzer agent — summarize a tender and produce a bid/no-bid recommendation.
// ---------------------------------------------------------------------------

server.tool(
  "deeprfp_analyze_rfp",
  "Run DeepRFP's analyzer agent on a tender to extract requirements, key dates, evaluation criteria, and a bid/no-bid recommendation. Provide rfp_text, rfp_url, or a project_id.",
  {
    project_id: z.string().optional().describe("Analyze the RFP already attached to this project."),
    rfp_text: z.string().optional().describe("Raw RFP/tender text to analyze."),
    rfp_url: z.string().url().optional().describe("URL of the tender document to analyze."),
    focus: z
      .array(z.enum(["requirements", "deadlines", "evaluation_criteria", "risks", "bid_recommendation"]))
      .optional()
      .describe("Aspects to emphasize in the analysis."),
  },
  async (args) => {
    if (!args.project_id && !args.rfp_text && !args.rfp_url) {
      return fail(new Error("Provide one of project_id, rfp_text, or rfp_url."));
    }
    try {
      return ok(await deeprfpRequest("/agents/analyze", { method: "POST", body: args }));
    } catch (err) {
      return fail(err);
    }
  }
);

// ---------------------------------------------------------------------------
// Drafting agent — generate proposal response sections.
// ---------------------------------------------------------------------------

server.tool(
  "deeprfp_draft_response",
  "Generate a proposal response draft for an RFP using DeepRFP's writer agent, grounded in your content library.",
  {
    project_id: z.string().optional().describe("Project providing RFP context and content library."),
    prompt: z.string().describe("What to draft, e.g. 'executive summary' or 'technical approach for requirement 3.2'."),
    section: z.string().optional().describe("Named proposal section to target."),
    tone: z.enum(["formal", "persuasive", "concise", "technical"]).optional().describe("Writing tone."),
    language: z.string().optional().describe("Output language (DeepRFP supports 28 languages), e.g. 'en', 'fr', 'es'."),
    word_limit: z.number().int().positive().optional().describe("Approximate word limit for the draft."),
  },
  async (args) => {
    try {
      return ok(await deeprfpRequest("/agents/draft", { method: "POST", body: args }));
    } catch (err) {
      return fail(err);
    }
  }
);

// ---------------------------------------------------------------------------
// Questionnaire agent — auto-fill bid forms / RFQ questions.
// ---------------------------------------------------------------------------

server.tool(
  "deeprfp_answer_questionnaire",
  "Auto-fill questionnaire-style bid/RFQ questions from your content library using DeepRFP's questionnaire agent.",
  {
    project_id: z.string().optional().describe("Project providing the content library for answers."),
    questions: z.array(z.string()).min(1).describe("List of questions to answer."),
    language: z.string().optional().describe("Answer language, e.g. 'en', 'de'."),
    max_words_per_answer: z.number().int().positive().optional().describe("Word cap per answer."),
  },
  async (args) => {
    try {
      return ok(await deeprfpRequest("/agents/questionnaire", { method: "POST", body: args }));
    } catch (err) {
      return fail(err);
    }
  }
);

// ---------------------------------------------------------------------------
// Compliance matrix generation.
// ---------------------------------------------------------------------------

server.tool(
  "deeprfp_generate_compliance_matrix",
  "Generate a compliance matrix mapping tender requirements to responses/evidence using DeepRFP. Provide rfp_text or a project_id.",
  {
    project_id: z.string().optional().describe("Project whose RFP requirements to map."),
    rfp_text: z.string().optional().describe("Raw RFP/tender text to extract requirements from."),
    include_status: z.boolean().optional().describe("Include a compliant/partial/non-compliant status column."),
  },
  async (args) => {
    if (!args.project_id && !args.rfp_text) {
      return fail(new Error("Provide either project_id or rfp_text."));
    }
    try {
      return ok(await deeprfpRequest("/agents/compliance-matrix", { method: "POST", body: args }));
    } catch (err) {
      return fail(err);
    }
  }
);

// ---------------------------------------------------------------------------
// Review agent — color review / improve an existing draft.
// ---------------------------------------------------------------------------

server.tool(
  "deeprfp_review_proposal",
  "Run a review (e.g. red-team / color review) on proposal text to surface gaps, weaknesses, and improvement suggestions.",
  {
    project_id: z.string().optional().describe("Project context for evaluation criteria."),
    text: z.string().describe("Proposal text to review."),
    review_type: z.enum(["pink", "red", "gold", "compliance", "clarity"]).optional().describe("Type of review pass."),
    rewrite: z.boolean().optional().describe("If true, return an improved rewrite alongside the critique."),
  },
  async (args) => {
    try {
      return ok(await deeprfpRequest("/agents/review", { method: "POST", body: args }));
    } catch (err) {
      return fail(err);
    }
  }
);

// ---------------------------------------------------------------------------
// Content library search.
// ---------------------------------------------------------------------------

server.tool(
  "deeprfp_search_library",
  "Search your DeepRFP content library (past proposals, boilerplate, answers) for reusable material.",
  {
    query: z.string().describe("Search query."),
    limit: z.number().int().min(1).max(50).optional().describe("Max results (default 10)."),
  },
  async ({ query, limit }) => {
    try {
      return ok(await deeprfpRequest("/library/search", { query: { q: query, limit } }));
    } catch (err) {
      return fail(err);
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[deeprfp] MCP server running on stdio");
}

main().catch((err) => {
  console.error("[deeprfp] fatal:", err);
  process.exit(1);
});
