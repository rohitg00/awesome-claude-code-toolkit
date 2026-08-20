#!/usr/bin/env node
/**
 * NTXP BidWatch MCP server.
 *
 * A single hub that unifies search across public procurement / bidding sources:
 * SAM.gov, HigherGov, BidBanana, Texas ESBD/TxSmartBuy, Bonfire (UT Dallas,
 * City of Lewisville), Jaggaer (UNT, Texas A&M), Ionwave (City of Denton),
 * OpenGov, DemandStar, and PlanetBids.
 *
 * Credential-gated sources read keys from the environment (see README).
 * Keyless sources (esbd, bonfire-backed) work out of the box.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { SOURCES, getSource, resolveConfig, isConfigured } from "./registry.js";
import type { Opportunity } from "./types.js";

function ok(data: unknown) {
  return { content: [{ type: "text" as const, text: typeof data === "string" ? data : JSON.stringify(data, null, 2) }] };
}
function fail(err: unknown) {
  const message = err instanceof Error ? err.message : String(err);
  return { isError: true, content: [{ type: "text" as const, text: `Error: ${message}` }] };
}

const server = new McpServer({ name: "ntxp-bidwatch", version: "0.1.0" });

server.tool(
  "bidwatch_list_sources",
  "List every configured BidWatch source with its platform, auth requirement, reliability, and whether it is ready to use right now.",
  {},
  async () => {
    const rows = SOURCES.map((s) => ({
      name: s.name,
      displayName: s.displayName,
      platform: s.adapter.platform,
      auth: s.adapter.auth,
      reliability: s.adapter.reliability,
      configured: isConfigured(s),
      envVars: s.env ? Object.values(s.env).filter(Boolean) : [],
      notes: s.notes,
    }));
    return ok(rows);
  }
);

server.tool(
  "bidwatch_search",
  "Search a single procurement source for opportunities. Use bidwatch_list_sources to see valid source names.",
  {
    source: z.string().describe("Source name, e.g. 'samgov', 'esbd', 'utd', 'denton-tx', 'lewisville-tx', 'bonfire'."),
    keywords: z.string().optional().describe("Free-text keywords to match."),
    state: z.string().optional().describe("Two-letter US state filter, where supported (e.g. 'TX')."),
    org: z.string().optional().describe("Organization subdomain/code for generic platforms (bonfire/ionwave/jaggaer)."),
    limit: z.number().int().min(1).max(100).optional().describe("Max results (default 25)."),
    verbose: z.boolean().optional().describe("Include each source's raw record."),
  },
  async ({ source, keywords, state, org, limit, verbose }) => {
    const def = getSource(source);
    if (!def) return fail(new Error(`Unknown source '${source}'. Call bidwatch_list_sources for valid names.`));
    try {
      const results = await def.adapter.search({ keywords, state, org, limit, verbose }, resolveConfig(def));
      return ok({ source: def.name, count: results.length, results });
    } catch (err) {
      return fail(err);
    }
  }
);

server.tool(
  "bidwatch_search_all",
  "Search across multiple sources at once and aggregate the results. Defaults to every source that is ready to use (no missing credentials). Sources that error are reported per-source rather than failing the whole call.",
  {
    keywords: z.string().optional().describe("Free-text keywords to match."),
    state: z.string().optional().describe("Two-letter US state filter, where supported."),
    sources: z.array(z.string()).optional().describe("Limit to these source names (default: all configured sources)."),
    limit_per_source: z.number().int().min(1).max(50).optional().describe("Max results per source (default 10)."),
  },
  async ({ keywords, state, sources, limit_per_source }) => {
    const limit = limit_per_source ?? 10;
    const targets = sources?.length
      ? SOURCES.filter((s) => sources.map((n) => n.toLowerCase()).includes(s.name))
      : SOURCES.filter(isConfigured);
    const settled = await Promise.allSettled(
      targets.map((def) => def.adapter.search({ keywords, state, limit }, resolveConfig(def)))
    );
    const results: Opportunity[] = [];
    const errors: { source: string; error: string }[] = [];
    settled.forEach((r, i) => {
      const name = targets[i].name;
      if (r.status === "fulfilled") results.push(...r.value);
      else errors.push({ source: name, error: r.reason instanceof Error ? r.reason.message : String(r.reason) });
    });
    return ok({
      searched: targets.map((t) => t.name),
      count: results.length,
      results,
      errors: errors.length ? errors : undefined,
    });
  }
);

server.tool(
  "bidwatch_get_opportunity",
  "Fetch a single opportunity by id from a source that supports detail lookups (currently 'esbd').",
  {
    source: z.string().describe("Source name."),
    id: z.string().describe("Opportunity id from a prior search result."),
  },
  async ({ source, id }) => {
    const def = getSource(source);
    if (!def) return fail(new Error(`Unknown source '${source}'.`));
    if (!def.adapter.getOpportunity) {
      return fail(new Error(`Source '${source}' does not support detail lookup. Use the opportunity's url instead.`));
    }
    try {
      const opp = await def.adapter.getOpportunity(id, resolveConfig(def));
      return opp ? ok(opp) : fail(new Error(`No opportunity ${id} found in '${source}'.`));
    } catch (err) {
      return fail(err);
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[ntxp-bidwatch] MCP server running on stdio");
}

main().catch((err) => {
  console.error("[ntxp-bidwatch] fatal:", err);
  process.exit(1);
});
