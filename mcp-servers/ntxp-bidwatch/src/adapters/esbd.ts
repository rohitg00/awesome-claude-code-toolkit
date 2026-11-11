import { getJson, matchesKeywords } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * Texas Electronic State Business Daily (ESBD) / TxSmartBuy.
 * Backed by the public NetSuite SuiteCommerce SearchAPI at
 * https://www.txsmartbuy.gov/api/items (no auth). Verified live.
 * The endpoint is undocumented, so the response shape may drift over time.
 */
const BASE = "https://www.txsmartbuy.gov";

interface EsbdItem {
  internalid?: number | string;
  displayname?: string;
  storedisplayname2?: string;
  custitem_item_status?: string;
  custitem_item_start_date?: string;
  custitem_item_end_date?: string;
  custitem_nigp_code?: string;
  custitem_vendor_supplier?: string;
  pagetitle?: string;
}

const STATUS: Record<string, string> = { Q: "quote", A: "awarded", O: "open", C: "closed" };

function mapItem(it: EsbdItem): Opportunity {
  const id = String(it.internalid ?? "");
  return {
    source: "esbd",
    id,
    title: it.displayname ?? it.storedisplayname2 ?? it.pagetitle ?? "(untitled)",
    agency: it.custitem_vendor_supplier || undefined,
    status: it.custitem_item_status ? STATUS[it.custitem_item_status] ?? it.custitem_item_status : undefined,
    postedDate: it.custitem_item_start_date || undefined,
    dueDate: it.custitem_item_end_date || undefined,
    url: id ? `${BASE}/esbd/${id}` : `${BASE}/esbd`,
    category: it.custitem_nigp_code || undefined,
  };
}

export const esbdAdapter: Adapter = {
  platform: "esbd",
  auth: "none",
  reliability: "verified",
  async search(params: SearchParams): Promise<Opportunity[]> {
    const limit = Math.min(params.limit ?? 25, 100);
    const url = new URL(`${BASE}/api/items`);
    url.searchParams.set("q", params.keywords ?? "");
    url.searchParams.set("commercecategoryurl", "/esbd");
    url.searchParams.set("fieldset", "details");
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", "0");
    url.searchParams.set("country", "US");
    url.searchParams.set("language", "en");
    const data = await getJson<{ items?: EsbdItem[] }>(url.toString());
    const out = (data.items ?? []).map(mapItem);
    return out.filter((o) => matchesKeywords(`${o.title} ${o.category ?? ""}`, params.keywords));
  },
  async getOpportunity(id: string): Promise<Opportunity | null> {
    const url = new URL(`${BASE}/api/items`);
    url.searchParams.set("internalid", id);
    url.searchParams.set("fieldset", "details");
    url.searchParams.set("country", "US");
    url.searchParams.set("language", "en");
    const data = await getJson<{ items?: EsbdItem[] }>(url.toString());
    const it = data.items?.[0];
    return it ? mapItem(it) : null;
  },
};
