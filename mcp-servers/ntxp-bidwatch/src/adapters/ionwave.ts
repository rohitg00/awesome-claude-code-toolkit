import { parse } from "node-html-parser";
import { getText, matchesKeywords } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * Ionwave eBid (Euna) public sourcing-events list.
 * https://{org}.ionwave.net/SourcingEvents.aspx?SourceType=1
 * ASP.NET WebForms renders the grid server-side, so it is scrapeable.
 * Verified host: dentontx.ionwave.net. Selectors are best-effort.
 */
export const ionwaveAdapter: Adapter = {
  platform: "ionwave",
  auth: "none",
  reliability: "best-effort",
  async search(params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]> {
    const org = params.org ?? cfg.org;
    if (!org) throw new Error("Ionwave requires an organization subdomain (param 'org', e.g. 'dentontx').");
    const base = `https://${org}.ionwave.net`;
    const html = await getText(`${base}/SourcingEvents.aspx?SourceType=1`);
    const root = parse(html);
    const out: Opportunity[] = [];
    for (const row of root.querySelectorAll("tr")) {
      const link = row.querySelector('a[href*="SourcingEvents.aspx"]');
      if (!link) continue;
      const cells = row.querySelectorAll("td").map((c) => c.text.trim()).filter(Boolean);
      const title = link.text.trim();
      if (!title) continue;
      const href = link.getAttribute("href") ?? "";
      const id = href.match(/SourcingEventId=(\d+)/i)?.[1] ?? title;
      out.push({
        source: `ionwave:${org}`,
        id,
        title,
        agency: org,
        status: "open",
        dueDate: cells.find((c) => /\d{1,2}\/\d{1,2}\/\d{2,4}/.test(c)),
        url: href.startsWith("http") ? href : `${base}/${href.replace(/^\//, "")}`,
        description: cells.join(" | "),
      });
    }
    if (out.length === 0) {
      throw new Error(
        `No events parsed from ${base}/SourcingEvents.aspx?SourceType=1. The grid layout may have changed — open the portal in a browser to verify.`
      );
    }
    return out
      .filter((o) => matchesKeywords(`${o.title} ${o.description ?? ""}`, params.keywords))
      .slice(0, params.limit ?? 50);
  },
};
