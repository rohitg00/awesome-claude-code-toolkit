import { getJson } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * SAM.gov "Get Opportunities" public API (GSA).
 * https://api.sam.gov/opportunities/v2/search — requires an api.data.gov key.
 * Date range (postedFrom/postedTo, MM/dd/yyyy) is mandatory and capped at 1 year.
 */
function mmddyyyy(d: Date): string {
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}/${d.getFullYear()}`;
}

interface SamRecord {
  noticeId?: string;
  title?: string;
  fullParentPathName?: string;
  postedDate?: string;
  responseDeadLine?: string;
  type?: string;
  uiLink?: string;
  naicsCode?: string;
  description?: string;
}

export const samgovAdapter: Adapter = {
  platform: "samgov",
  auth: "api-key",
  reliability: "requires-key",
  configEnv: ["SAM_GOV_API_KEY"],
  async search(params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]> {
    if (!cfg.apiKey) throw new Error("SAM.gov requires SAM_GOV_API_KEY (free key from api.data.gov).");
    const to = new Date();
    const from = new Date();
    from.setFullYear(to.getFullYear() - 1);
    const url = new URL("https://api.sam.gov/opportunities/v2/search");
    url.searchParams.set("api_key", cfg.apiKey);
    url.searchParams.set("postedFrom", mmddyyyy(from));
    url.searchParams.set("postedTo", mmddyyyy(to));
    url.searchParams.set("limit", String(Math.min(params.limit ?? 25, 1000)));
    url.searchParams.set("offset", "0");
    if (params.keywords) url.searchParams.set("title", params.keywords);
    if (params.state) url.searchParams.set("state", params.state);
    const data = await getJson<{ opportunitiesData?: SamRecord[] }>(url.toString());
    return (data.opportunitiesData ?? []).map((r) => ({
      source: "samgov",
      id: r.noticeId ?? "",
      title: r.title ?? "(untitled)",
      agency: r.fullParentPathName,
      status: r.type,
      postedDate: r.postedDate,
      dueDate: r.responseDeadLine,
      url: r.uiLink,
      description: r.description,
      naics: r.naicsCode,
      raw: params.verbose ? r : undefined,
    }));
  },
};
