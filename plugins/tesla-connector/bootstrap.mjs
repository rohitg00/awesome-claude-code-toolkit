#!/usr/bin/env node
/**
 * First-run bootstrap for the Tesla connector.
 *
 * The plugin's .mcp.json points here instead of at the server directly, so
 * the very first launch configures itself:
 *
 *   1. Locates the server source (repo layout, TESLA_SERVER_DIR, or config).
 *   2. Builds it if dist/ is missing (npm install + npm run build, once).
 *   3. Loads ~/.config/tesla-mcp/config.json — written by /tesla-connector:setup
 *      — and maps it onto the environment (real env vars win).
 *   4. No credentials anywhere? Falls back to TESLA_MOCK=1 demo mode and says
 *      so on stderr, so the tools work immediately and tell you how to link
 *      the real car.
 *   5. Starts the MCP server (default) or the dashboard bridge
 *      (`node bootstrap.mjs bridge`).
 *
 * All diagnostics go to stderr — stdout belongs to the MCP protocol.
 */

import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const log = (msg) => console.error(`[tesla-bootstrap] ${msg}`);
const PLUGIN_ROOT = dirname(fileURLToPath(import.meta.url));

export const CONFIG_DIR = process.env.TESLA_CONFIG_DIR || join(homedir(), ".config", "tesla-mcp");
export const CONFIG_PATH = process.env.TESLA_CONFIG_PATH || join(CONFIG_DIR, "config.json");

function readConfig() {
  try {
    return JSON.parse(readFileSync(CONFIG_PATH, "utf8"));
  } catch {
    return {};
  }
}

function findServerDir(config) {
  const candidates = [
    process.env.TESLA_SERVER_DIR,
    config.TESLA_SERVER_DIR,
    resolve(PLUGIN_ROOT, "..", "..", "mcp-servers", "tesla"), // repo layout
    join(PLUGIN_ROOT, "server"), // self-contained copy, if ever bundled
  ].filter(Boolean);
  for (const dir of candidates) {
    if (existsSync(join(dir, "package.json"))) return dir;
  }
  return null;
}

function ensureBuilt(serverDir) {
  const entry = join(serverDir, "dist", "index.js");
  if (existsSync(entry)) return entry;
  log(`first run: building the Tesla server in ${serverDir} (one time, ~30s)…`);
  for (const args of [["install", "--no-audit", "--no-fund"], ["run", "build"]]) {
    const r = spawnSync("npm", args, { cwd: serverDir, stdio: ["ignore", "inherit", "inherit"], shell: process.platform === "win32" });
    if (r.status !== 0) {
      log(`npm ${args.join(" ")} failed (${r.status}). Build manually: cd ${serverDir} && npm install && npm run build`);
      process.exit(1);
    }
  }
  if (!existsSync(entry)) {
    log("build finished but dist/index.js is missing — check the build output above.");
    process.exit(1);
  }
  log("build complete.");
  return entry;
}

const config = readConfig();
const serverDir = findServerDir(config);
if (!serverDir) {
  log(
    "Cannot find the Tesla server source. Set TESLA_SERVER_DIR to your clone of " +
      "awesome-claude-code-toolkit/mcp-servers/tesla, or run /tesla-connector:setup."
  );
  process.exit(1);
}
const entry = ensureBuilt(serverDir);

// Config file → environment; real env vars always win.
for (const [key, value] of Object.entries(config)) {
  if (key.startsWith("TESLA_") && process.env[key] === undefined && value != null && value !== "") {
    process.env[key] = String(value);
  }
}

// Keep the rotating token cache in the config dir, not the spawn cwd.
if (!process.env.TESLA_TOKEN_CACHE) {
  try { mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 }); } catch {}
  process.env.TESLA_TOKEN_CACHE = join(CONFIG_DIR, "tokens.json");
}

const hasAuth = process.env.TESLA_REFRESH_TOKEN || process.env.TESLA_ACCESS_TOKEN;
if (!hasAuth && process.env.TESLA_MOCK === undefined) {
  process.env.TESLA_MOCK = "1";
  log("no Tesla credentials found — starting in DEMO (mock) mode.");
  log("Link your real car with the /tesla-connector:setup command (writes " + CONFIG_PATH + ").");
}

const mode = process.argv[2] === "bridge" ? "bridge.js" : "index.js";
await import(pathToFileURL(join(serverDir, "dist", mode)).href);
