import { getJson, postForm } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * OpenGov Procurement (formerly ProcureNow).
 *
 * The public vendor portal (https://procurement.opengov.com/portal/<slug>) is a
 * Cloudflare-protected React SPA with no clean anonymous JSON. The supported
 * path is the official API gateway:
 *
 *   API base:  https://api.procurement.opengov.com/gateway
 *   Auth:      OAuth2 client-credentials (register an app at developer.opengov.com)
 *
 * Exact endpoint paths/scopes live behind the logged-in developer docs, so the
 * token URL and search path are configurable. Defaults are sensible starting
 * points — confirm them against your OpenGov developer account.
 *
 *   OPENGOV_CLIENT_ID, OPENGOV_CLIENT_SECRET   (required)
 *   OPENGOV_TOKEN_URL      default https://auth.opengov.com/oauth/token
 *   OPENGOV_API_BASE       default https://api.procurement.opengov.com/gateway
 *   OPENGOV_SEARCH_PATH    default /procurement/v1/projects
 *   OPENGOV_AUDIENCE       default https://api.procurement.opengov.com
 */
const DEFAULT_TOKEN_URL = "https://auth.opengov.com/oauth/token";
const DEFAULT_API_BASE = "https://api.procurement.opengov.com/gateway";
const DEFAULT_SEARCH_PATH = "/procurement/v1/projects";
const DEFAULT_AUDIENCE = "https://api.procurement.opengov.com";

let cachedToken: { token: string; expiresAt: number } | null = null;

function pick(obj: Record<string, unknown>, keys: string[]): string | undefined {
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === "string" && v) return v;
    if (typeof v === "number") return String(v);
  }
  return undefined;
}

function firstArray(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) return data as Record<string, unknown>[];
  if (data && typeof data === "object") {
    for (const v of Object.values(data as Record<string, unknown>)) {
      if (Array.isArray(v) && v.length && typeof v[0] === "object") return v as Record<string, unknown>[];
    }
  }
  return [];
}

async function getToken(cfg: SourceConfig): Promise<string> {
  const now = Date.now();
  if (cachedToken && cachedToken.expiresAt > now + 60_000) return cachedToken.token;
  const tokenUrl = cfg.tokenUrl ?? DEFAULT_TOKEN_URL;
  const audience = process.env.OPENGOV_AUDIENCE ?? DEFAULT_AUDIENCE;
  const resp = await postForm<{ access_token?: string; expires_in?: number }>(tokenUrl, {
    grant_type: "client_credentials",
    client_id: cfg.clientId!,
    client_secret: cfg.clientSecret!,
    audience,
  });
  if (!resp.access_token) throw new Error(`OpenGov token endpoint returned no access_token (${tokenUrl}).`);
  cachedToken = { token: resp.access_token, expiresAt: now + (resp.expires_in ?? 3600) * 1000 };
  return cachedToken.token;
}

export const opengovAdapter: Adapter = {
  platform: "opengov",
  auth: "oauth",
  reliability: "requires-key",
  configEnv: ["OPENGOV_CLIENT_ID", "OPENGOV_CLIENT_SECRET", "OPENGOV_API_BASE", "OPENGOV_SEARCH_PATH"],
  async search(params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]> {
    if (!cfg.clientId || !cfg.clientSecret) {
      throw new Error(
        "OpenGov requires OPENGOV_CLIENT_ID and OPENGOV_CLIENT_SECRET (OAuth2 client-credentials from developer.opengov.com)."
      );
    }
    const token = await getToken(cfg);
    const base = (cfg.baseUrl ?? DEFAULT_API_BASE).replace(/\/+$/, "");
    const path = cfg.searchPath ?? DEFAULT_SEARCH_PATH;
    const url = new URL(`${base}${path.startsWith("/") ? path : `/${path}`}`);
    if (params.keywords) url.searchParams.set("q", params.keywords);
    url.searchParams.set("limit", String(Math.min(params.limit ?? 25, 100)));
    const data = await getJson(url.toString(), { Authorization: `Bearer ${token}` });
    return firstArray(data).map((r) => ({
      source: "opengov",
      id: pick(r, ["id", "uuid", "projectId", "number"]) ?? "",
      title: pick(r, ["title", "name", "projectName", "subject"]) ?? "(untitled)",
      agency: pick(r, ["agency", "government", "organization", "departmentName", "buyer"]),
      status: pick(r, ["status", "stage", "state"]),
      postedDate: pick(r, ["postedDate", "releaseDate", "openDate", "published"]),
      dueDate: pick(r, ["dueDate", "closeDate", "submissionDeadline", "deadline"]),
      url: pick(r, ["url", "portalUrl", "publicUrl", "link"]),
      description: pick(r, ["description", "summary"]),
      raw: params.verbose ? r : undefined,
    }));
  },
};
