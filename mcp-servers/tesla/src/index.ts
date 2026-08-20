#!/usr/bin/env node
/**
 * Tesla connector MCP server (stdio).
 *
 * Exposes the entire tool registry — every Fleet/Owner API data endpoint and
 * remote command, plus the convenience tools (find my Tesla, drop a pin,
 * navigate-to-car, lock/unlock) — to any MCP client: Claude Code, Claude
 * Desktop, ChatGPT (via MCP connectors), or anything else that speaks MCP.
 * (For MCP over HTTP — claude.ai custom connectors — run the bridge and use
 * its /mcp endpoint.)
 *
 * Credentials come from the environment or ~/.config/tesla-mcp/config.json:
 *   TESLA_REFRESH_TOKEN  — app-style refresh token (owner mode), or
 *   TESLA_CLIENT_ID/SECRET + TESLA_REFRESH_TOKEN — Fleet API mode
 *   TESLA_MOCK=1         — demo mode, no credentials needed
 */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { applyConfigFile, loadConfig } from "./config.js";
import { TeslaClient } from "./client.js";
import { buildMcpServer } from "./mcp.js";
import { TOOLS } from "./tools.js";

applyConfigFile();
const config = loadConfig();
const client = new TeslaClient(config);
const server = buildMcpServer(client);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error(
  `[tesla-mcp] ready — ${TOOLS.length} tools, mode=${config.mock ? "MOCK" : config.mode}, base=${config.apiBase}`
);
