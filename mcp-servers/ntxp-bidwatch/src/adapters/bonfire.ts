import { XMLParser } from "fast-xml-parser";
import { getText, matchesKeywords } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * Bonfire (Euna Procurement) public opportunity RSS feed.
 * Every Bonfire agency exposes: https://{org}.bonfirehub.com/opportunities/rss
 * Verified against utdallas.bonfirehub.com and cityoflewisville.bonfirehub.com.
 */
const parser = new XMLParser({ ignoreAttributes: false, trimValues: true });

function parseItem(item: Record<string, unknown>, org: string): Opportunity {
  const rawTitle = String(item.title ?? "");
  const rawDesc = String(item.description ?? "");
  const link = String(item.link ?? "");
  const refMatch = rawTitle.match(/Reference #:\s*([^.]+)\.\s*Name:\s*(.+)$/i);
  const ref = refMatch?.[1]?.trim();
  const name = refMatch?.[2]?.trim() ?? rawTitle;
  const closes = rawDesc.match(/closes\s+([A-Za-z]{3}\s+\d{1,2},\s*\d{4}[^.]*)/i)?.[1]?.trim();
  const id = link.match(/opportunities\/(\d+)/)?.[1] ?? ref ?? link;
  return {
    source: `bonfire:${org}`,
    id,
    title: name,
    agency: org,
    status: "open",
    postedDate: item.pubDate ? String(item.pubDate).trim() : undefined,
    dueDate: closes,
    url: link,
    description: rawDesc.replace(/^Description:\s*/i, "").trim(),
    category: ref,
  };
}

export const bonfireAdapter: Adapter = {
  platform: "bonfire",
  auth: "none",
  reliability: "verified",
  async search(params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]> {
    const org = params.org ?? cfg.org;
    if (!org) throw new Error("Bonfire requires an organization subdomain (param 'org', e.g. 'utdallas').");
    const xml = await getText(`https://${org}.bonfirehub.com/opportunities/rss`);
    const doc = parser.parse(xml) as { rss?: { channel?: { item?: unknown } } };
    const rawItems = doc.rss?.channel?.item;
    const items = Array.isArray(rawItems) ? rawItems : rawItems ? [rawItems] : [];
    const out = items.map((it) => parseItem(it as Record<string, unknown>, org));
    const filtered = out.filter((o) => matchesKeywords(`${o.title} ${o.description ?? ""}`, params.keywords));
    return filtered.slice(0, params.limit ?? 50);
  },
};
