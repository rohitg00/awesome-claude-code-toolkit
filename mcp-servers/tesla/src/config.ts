/**
 * Environment-driven configuration. Everything is overridable so the server
 * stays portable: laptop, home server, Raspberry Pi, or a cloud VM.
 */

import { mkdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export type AuthMode = "owner" | "fleet";
export type Region = "na" | "eu" | "cn";

/**
 * Map ~/.config/tesla-mcp/config.json onto the environment (real env vars
 * win), default the token cache into that directory, and fall back to mock
 * mode when no credentials exist anywhere. Called by every entry point
 * (MCP server, bridge, CLI) so a token written once by the setup flow works
 * everywhere with zero env editing.
 */
export function applyConfigFile(env: NodeJS.ProcessEnv = process.env): string {
  const dir = env.TESLA_CONFIG_DIR || join(homedir(), ".config", "tesla-mcp");
  const path = env.TESLA_CONFIG_PATH || join(dir, "config.json");
  try {
    const cfg = JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
    for (const [key, value] of Object.entries(cfg)) {
      if (key.startsWith("TESLA_") && env[key] === undefined && value != null && value !== "") {
        env[key] = String(value);
      }
    }
  } catch {
    // No config file yet — env-only operation is fine.
  }
  if (!env.TESLA_TOKEN_CACHE) {
    try {
      mkdirSync(dir, { recursive: true, mode: 0o700 });
      env.TESLA_TOKEN_CACHE = join(dir, "tokens.json");
    } catch {
      // Fall back to the default cwd-relative cache.
    }
  }
  if (!env.TESLA_REFRESH_TOKEN && !env.TESLA_ACCESS_TOKEN && env.TESLA_MOCK === undefined) {
    env.TESLA_MOCK = "1";
    console.error(
      `[tesla] no credentials found — running in DEMO (mock) mode. Link your car: see README ('Getting your Tesla auth') or write ${path}.`
    );
  }
  return path;
}

export interface TeslaConfig {
  /** "fleet" = official Fleet API (developer app). "owner" = legacy Owner API (app-style refresh token). */
  mode: AuthMode;
  region: Region;
  /** REST base for vehicle endpoints. */
  apiBase: string;
  /** OAuth token endpoint base. */
  authBase: string;
  clientId: string;
  clientSecret?: string;
  refreshToken?: string;
  /** Optional pre-issued access token (skips refresh until it expires). */
  accessToken?: string;
  /**
   * Optional Tesla vehicle-command HTTP proxy (github.com/teslamotors/vehicle-command).
   * 2021+ vehicles require signed commands on the Fleet API; point this at your
   * running tesla-http-proxy and commands are routed through it automatically.
   */
  commandProxyUrl?: string;
  /** Default vehicle when a tool call doesn't name one (VIN or numeric id). */
  defaultVehicle?: string;
  /** Where rotated tokens are cached between runs. */
  tokenCachePath: string;
  /** Demo mode: canned data, no network, no credentials needed. */
  mock: boolean;
}

const FLEET_BASES: Record<Region, string> = {
  na: "https://fleet-api.prd.na.vn.cloud.tesla.com",
  eu: "https://fleet-api.prd.eu.vn.cloud.tesla.com",
  cn: "https://fleet-api.prd.cn.vn.cloud.tesla.cn",
};

const OWNER_BASE = "https://owner-api.teslamotors.com";
const AUTH_BASE = "https://auth.tesla.com";
const AUTH_BASE_CN = "https://auth.tesla.cn";

export function loadConfig(env: NodeJS.ProcessEnv = process.env): TeslaConfig {
  const region = (env.TESLA_REGION || "na").toLowerCase() as Region;
  const explicitMode = env.TESLA_AUTH_MODE?.toLowerCase();
  const mode: AuthMode =
    explicitMode === "owner" || explicitMode === "fleet"
      ? explicitMode
      : env.TESLA_CLIENT_ID
        ? "fleet"
        : "owner";

  const apiBase =
    env.TESLA_API_BASE ||
    (mode === "fleet" ? FLEET_BASES[region] || FLEET_BASES.na : OWNER_BASE);

  return {
    mode,
    region,
    apiBase: apiBase.replace(/\/+$/, ""),
    authBase: (env.TESLA_AUTH_BASE || (region === "cn" ? AUTH_BASE_CN : AUTH_BASE)).replace(/\/+$/, ""),
    clientId: env.TESLA_CLIENT_ID || "ownerapi",
    clientSecret: env.TESLA_CLIENT_SECRET || undefined,
    refreshToken: env.TESLA_REFRESH_TOKEN || undefined,
    accessToken: env.TESLA_ACCESS_TOKEN || undefined,
    commandProxyUrl: env.TESLA_COMMAND_PROXY_URL?.replace(/\/+$/, "") || undefined,
    defaultVehicle: env.TESLA_VIN || env.TESLA_VEHICLE_ID || undefined,
    tokenCachePath: env.TESLA_TOKEN_CACHE || ".tesla-tokens.json",
    mock: env.TESLA_MOCK === "1" || env.TESLA_MOCK === "true",
  };
}
