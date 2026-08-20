#!/usr/bin/env node
/**
 * Direct CLI over the same tool registry — the third surface after MCP and
 * HTTP. Lets the prepackaged Agent Skill (and any shell) invoke tools without
 * an MCP client:
 *
 *   node dist/cli.js list
 *   node dist/cli.js tesla_find_my_tesla
 *   node dist/cli.js tesla_set_charge_limit '{"percent":90}'
 *
 * Output is JSON on stdout; diagnostics on stderr. Exit 0 on success.
 * Credentials resolve exactly like the other surfaces: env vars, then
 * ~/.config/tesla-mcp/config.json, then demo mock mode.
 */

import { z } from "zod";
import { applyConfigFile, loadConfig } from "./config.js";
import { TeslaClient } from "./client.js";
import { TOOLS, getTool } from "./tools.js";

const [, , name, argsJson] = process.argv;

if (!name || name === "list" || name === "--list" || name === "--help" || name === "-h") {
  console.log("Usage: tesla-cli <tool_name> ['{\"json\":\"args\"}']\n");
  for (const t of TOOLS) {
    const params = Object.keys(t.schema).join(", ");
    console.log(`  ${t.name}${params ? `  (${params})` : ""}`);
    console.log(`      ${t.description}`);
  }
  process.exit(name ? 0 : 1);
}

const tool = getTool(name);
if (!tool) {
  console.error(`Unknown tool '${name}'. Run 'tesla-cli list' for all ${TOOLS.length} tools.`);
  process.exit(1);
}

let args: Record<string, unknown>;
try {
  args = argsJson ? (JSON.parse(argsJson) as Record<string, unknown>) : {};
} catch {
  console.error(`Second argument must be a JSON object, got: ${argsJson}`);
  process.exit(1);
}

applyConfigFile();
const client = new TeslaClient(loadConfig());

try {
  const parsed = z.object(tool.schema).parse(args);
  const result = await tool.handler(client, parsed);
  console.log(JSON.stringify(result, null, 2));
} catch (err) {
  if (err instanceof z.ZodError) {
    console.error(`Invalid arguments for ${tool.name}:`);
    for (const issue of err.issues) console.error(`  ${issue.path.join(".") || "(root)"}: ${issue.message}`);
  } else {
    console.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
  }
  process.exit(1);
}
