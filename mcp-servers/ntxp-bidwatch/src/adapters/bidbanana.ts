import { postJson } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * BidBanana by The Bid Lab — bidbanana.thebidlab.com.
 * POST /api/v1/search with { api_key, keywords, state, max_results }.
 * Key is per-account and permission-scoped (provisioned by The Bid Lab).
 */
function pick(obj: Record<string, unknown>, keys: string[]): string | undefined {
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === "string" && v) return v;
    if (typeof v === "number") return String(v);
  }
  return undefined;
}

export const bidbananaAdapter: Adapter = {
  platform: "bidbanana",
  auth: "api-key",
  reliability: "requires-key",
  configEnv: ["BIDBANANA_API_KEY"],
  async search(params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]> {
    if (!cfg.apiKey) throw new Error("BidBanana requires BIDBANANA_API_KEY (provisioned by The Bid Lab).");
    const body: Record<string, unknown> = {
      api_key: cfg.apiKey,
      keywords: params.keywords ?? "",
      max_results: Math.min(params.limit ?? 25, 100),
    };
    if (params.state) body.state = params.state;
    const data = await postJson<{ results?: Record<string, unknown>[]; data?: Record<string, unknown>[] }>(
      "https://bidbanana.thebidlab.com/api/v1/search",
      body
    );
    const rows = data.results ?? data.data ?? [];
    return rows.map((r) => ({
      source: "bidbanana",
      id: pick(r, ["id", "bid_id", "uuid"]) ?? "",
      title: pick(r, ["title", "name", "bid_title"]) ?? "(untitled)",
      agency: pick(r, ["agency", "organization", "buyer", "entity"]),
      status: pick(r, ["status"]),
      postedDate: pick(r, ["posted_date", "published", "date_posted"]),
      dueDate: pick(r, ["due_date", "close_date", "deadline"]),
      url: pick(r, ["url", "link", "source_url"]),
      description: pick(r, ["description", "summary"]),
      category: pick(r, ["state"]),
      raw: params.verbose ? r : undefined,
    }));
  },
};
