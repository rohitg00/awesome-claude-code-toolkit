/**
 * Shared MCP server construction — used by the stdio entry (index.ts) and by
 * the bridge's streamable-HTTP endpoint (/mcp), so the connector shows up
 * identically whether it's installed as a Desktop extension (.mcpb), a Claude
 * Code plugin, or a claude.ai remote connector.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { TeslaClient } from "./client.js";
import { TOOLS } from "./tools.js";

function ok(data: unknown) {
  return {
    content: [{ type: "text" as const, text: typeof data === "string" ? data : JSON.stringify(data, null, 2) }],
  };
}

function fail(err: unknown) {
  const message = err instanceof Error ? err.message : String(err);
  return { isError: true, content: [{ type: "text" as const, text: `Error: ${message}` }] };
}

export function buildMcpServer(client: TeslaClient): McpServer {
  const server = new McpServer({ name: "tesla", version: "0.1.0" });
  for (const tool of TOOLS) {
    server.tool(tool.name, tool.description, tool.schema, async (args: Record<string, unknown>) => {
      try {
        return ok(await tool.handler(client, args ?? {}));
      } catch (err) {
        return fail(err);
      }
    });
  }
  return server;
}
