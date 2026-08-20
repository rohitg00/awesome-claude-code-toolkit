import { getJson } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * HigherGov external API (subscriber-gated).
 * https://www.highergov.com/api-external/opportunity/ — api_key query param.
 * Field names are mapped defensively since the schema is behind a paywall.
 */
function pick(obj: Record<string, unknown>, keys: string[]): string | undefined {
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === "string" && v) return v;
    if (typeof v === "number") return String(v);
  }
  return undefined;
}

export const highergovAdapter: Adapter = {
  platform: "highergov",
  auth: "api-key",
  reliability: "requires-key",
  configEnv: ["HIGHERGOV_API_KEY", "HIGHERGOV_BASE_URL"],
  async search(params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]> {
    if (!cfg.apiKey) throw new Error("HigherGov requires HIGHERGOV_API_KEY (from your HigherGov subscription).");
    const base = (cfg.baseUrl ?? "https://www.highergov.com/api-external").replace(/\/+$/, "");
    const url = new URL(`${base}/opportunity/`);
    url.searchParams.set("api_key", cfg.apiKey);
    if (params.keywords) url.searchParams.set("search", params.keywords);
    url.searchParams.set("page_size", String(Math.min(params.limit ?? 25, 100)));
    const data = await getJson<{ results?: Record<string, unknown>[] }>(url.toString());
    return (data.results ?? []).map((r) => ({
      source: "highergov",
      id: pick(r, ["id", "opportunity_id", "source_id", "uuid"]) ?? "",
      title: pick(r, ["title", "name", "opportunity_title"]) ?? "(untitled)",
      agency: pick(r, ["agency", "agency_name", "department"]),
      status: pick(r, ["status", "opportunity_status"]),
      postedDate: pick(r, ["posted_date", "post_date", "published_date"]),
      dueDate: pick(r, ["due_date", "response_date", "close_date"]),
      url: pick(r, ["url", "source_url", "link"]),
      description: pick(r, ["description", "summary"]),
      naics: pick(r, ["naics_code", "naics"]),
      raw: params.verbose ? r : undefined,
    }));
  },
};
