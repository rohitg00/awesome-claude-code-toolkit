import { getText } from "../http.js";
import type { Adapter, Opportunity, SearchParams, SourceConfig } from "../types.js";

/**
 * Jaggaer / SciQuest public sourcing events ("PublicEvent" router).
 * https://bids.sciquest.com/apps/Router/PublicEvent?CustomerOrg={org}
 * Used by UNT System (org=UNTS) and Texas A&M (org=TAMU), among others.
 *
 * The open-for-bid table is rendered client-side (the Jaggaer "phx" SPA), so a
 * plain HTTP fetch cannot read the event rows. We confirm the portal is live
 * and return a clear pointer rather than fabricating results. For a machine
 * -readable feed of these Texas institutions, use the `esbd` source (they
 * cross-post formal solicitations to the Texas ESBD).
 */
export const jaggaerAdapter: Adapter = {
  platform: "jaggaer",
  auth: "none",
  reliability: "requires-browser",
  async search(_params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]> {
    const org = _params.org ?? cfg.org;
    if (!org) throw new Error("Jaggaer requires an organization code (param 'org', e.g. 'UNTS' or 'TAMU').");
    const portal = `https://bids.sciquest.com/apps/Router/PublicEvent?CustomerOrg=${encodeURIComponent(org)}`;
    // Confirm the portal resolves so we fail loudly if the org code is wrong.
    await getText(`${portal}&tab=PHX_NAV_SourcingOpenForBid`);
    throw new Error(
      `Jaggaer/SciQuest renders its event list client-side, so opportunities for '${org}' cannot be read over plain HTTP. ` +
        `View open bids at: ${portal}&tab=PHX_NAV_SourcingOpenForBid . ` +
        `For a machine-readable feed of this Texas institution's formal solicitations, query the 'esbd' source instead.`
    );
  },
};
