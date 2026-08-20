import { getText } from "../http.js";
import type { Adapter, SearchParams, SourceConfig } from "../types.js";

/**
 * Factory for portals whose listings are rendered client-side (JS/SPA), where a
 * plain HTTP fetch returns an app shell rather than the bid rows. We verify the
 * portal is reachable, then return a clear pointer instead of fabricating data.
 *
 * DemandStar (demandstar.com/browse-bids) and PlanetBids (per-agency portals,
 * cross-agency VendorLine search) both fall in this category.
 */
export function makeBrowserPortalAdapter(opts: {
  platform: string;
  portalUrl: (cfg: SourceConfig, params: SearchParams) => string;
  note?: string;
}): Adapter {
  return {
    platform: opts.platform,
    auth: "none",
    reliability: "requires-browser",
    async search(params: SearchParams, cfg: SourceConfig) {
      const portal = opts.portalUrl(cfg, params);
      await getText(portal); // confirm reachable; throws on network/HTTP error
      throw new Error(
        `${opts.platform} renders its bid list client-side, so results cannot be read over plain HTTP. ` +
          `Browse opportunities at: ${portal}${opts.note ? ` — ${opts.note}` : ""}`
      );
    },
  };
}

export const demandstarAdapter: Adapter = makeBrowserPortalAdapter({
  platform: "demandstar",
  portalUrl: (_cfg, p) =>
    `https://www.demandstar.com/browse-bids${p.keywords ? `?q=${encodeURIComponent(p.keywords)}` : ""}`,
  note: "DemandStar has no public API; account registration unlocks document downloads.",
});

export const planetbidsAdapter: Adapter = makeBrowserPortalAdapter({
  platform: "planetbids",
  portalUrl: (cfg) =>
    cfg.baseUrl ??
    "https://vendors.planetbids.com/", // override PLANETBIDS_BASE_URL with a specific agency portal
  note: "Set PLANETBIDS_BASE_URL to a specific agency portal; PlanetBids has no public API.",
});
