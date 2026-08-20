#!/usr/bin/env node
/**
 * SessionStart hook: one quiet line of context when the Tesla connector is
 * not yet linked to a real car, so Claude knows to offer /tesla-connector:setup.
 * Prints nothing once configured. Never blocks (always exits 0).
 */

try {
  const { readFileSync } = await import("node:fs");
  const { homedir } = await import("node:os");
  const { join } = await import("node:path");

  const configPath =
    process.env.TESLA_CONFIG_PATH || join(homedir(), ".config", "tesla-mcp", "config.json");

  let config = {};
  try {
    config = JSON.parse(readFileSync(configPath, "utf8"));
  } catch {}

  const linked =
    process.env.TESLA_REFRESH_TOKEN ||
    process.env.TESLA_ACCESS_TOKEN ||
    config.TESLA_REFRESH_TOKEN ||
    config.TESLA_MOCK === "1"; // explicitly chosen demo mode counts as configured

  if (!linked) {
    console.log(
      "Tesla connector: not linked to a real car yet — tools run in demo (mock) mode. " +
        "Offer /tesla-connector:setup when the user wants their actual Tesla."
    );
  }
} catch {
  // Never block session start.
}
process.exit(0);
