import type { Adapter, SourceConfig } from "./types.js";
import { bonfireAdapter } from "./adapters/bonfire.js";
import { esbdAdapter } from "./adapters/esbd.js";
import { samgovAdapter } from "./adapters/samgov.js";
import { highergovAdapter } from "./adapters/highergov.js";
import { bidbananaAdapter } from "./adapters/bidbanana.js";
import { ionwaveAdapter } from "./adapters/ionwave.js";
import { jaggaerAdapter } from "./adapters/jaggaer.js";
import { opengovAdapter } from "./adapters/opengov.js";
import { demandstarAdapter, planetbidsAdapter } from "./adapters/browser-portal.js";

export interface SourceDef {
  name: string;
  displayName: string;
  adapter: Adapter;
  /** Static config baked into the named source (e.g. a Bonfire org). */
  fixed?: Partial<SourceConfig>;
  /** Env vars supplying credentials/endpoints for this source. */
  env?: {
    apiKey?: string;
    baseUrl?: string;
    clientId?: string;
    clientSecret?: string;
    tokenUrl?: string;
    searchPath?: string;
  };
  notes?: string;
}

export const SOURCES: SourceDef[] = [
  // ---- Federal / national ----
  {
    name: "samgov",
    displayName: "SAM.gov (US federal opportunities)",
    adapter: samgovAdapter,
    env: { apiKey: "SAM_GOV_API_KEY" },
    notes: "Free api.data.gov key. Daily call caps apply.",
  },
  {
    name: "highergov",
    displayName: "HigherGov (gov contracting intelligence)",
    adapter: highergovAdapter,
    env: { apiKey: "HIGHERGOV_API_KEY", baseUrl: "HIGHERGOV_BASE_URL" },
    notes: "Requires a paid HigherGov subscription + API key.",
  },
  {
    name: "bidbanana",
    displayName: "BidBanana by The Bid Lab",
    adapter: bidbananaAdapter,
    env: { apiKey: "BIDBANANA_API_KEY" },
    notes: "Paid SaaS; API key provisioned by The Bid Lab.",
  },
  {
    name: "opengov",
    displayName: "OpenGov Procurement (formerly ProcureNow)",
    adapter: opengovAdapter,
    env: {
      clientId: "OPENGOV_CLIENT_ID",
      clientSecret: "OPENGOV_CLIENT_SECRET",
      baseUrl: "OPENGOV_API_BASE",
      tokenUrl: "OPENGOV_TOKEN_URL",
      searchPath: "OPENGOV_SEARCH_PATH",
    },
    notes:
      "OAuth2 client-credentials from developer.opengov.com; API gateway at api.procurement.opengov.com/gateway. Exact search path is configurable (OPENGOV_SEARCH_PATH).",
  },

  // ---- Texas state ----
  {
    name: "esbd",
    displayName: "Texas Electronic State Business Daily / TxSmartBuy",
    adapter: esbdAdapter,
    notes: "Public NetSuite search index; no auth. Covers UTD/UNT/A&M formal solicitations too.",
  },
  { name: "txsmartbuy", displayName: "TxSmartBuy (alias of ESBD)", adapter: esbdAdapter },

  // ---- Texas universities ----
  {
    name: "utd",
    displayName: "UT Dallas (Bonfire)",
    adapter: bonfireAdapter,
    fixed: { org: "utdallas" },
  },
  {
    name: "unt",
    displayName: "University of North Texas System (Jaggaer)",
    adapter: jaggaerAdapter,
    fixed: { org: "UNTS" },
    notes: "Jaggaer is browser-rendered; use 'esbd' for a machine-readable feed.",
  },
  {
    name: "texas-am",
    displayName: "Texas A&M University System (Jaggaer)",
    adapter: jaggaerAdapter,
    fixed: { org: "TAMU" },
    notes: "Jaggaer is browser-rendered; use 'esbd' for a machine-readable feed.",
  },

  // ---- Texas cities ----
  {
    name: "denton-tx",
    displayName: "City of Denton, TX (Ionwave)",
    adapter: ionwaveAdapter,
    fixed: { org: "dentontx" },
  },
  {
    name: "lewisville-tx",
    displayName: "City of Lewisville, TX (Bonfire)",
    adapter: bonfireAdapter,
    fixed: { org: "cityoflewisville" },
  },

  // ---- Top platforms (generic; supply an org/endpoint) ----
  {
    name: "bonfire",
    displayName: "Bonfire (any agency — supply 'org')",
    adapter: bonfireAdapter,
    notes: "Generic Bonfire RSS; pass org=<subdomain>.",
  },
  {
    name: "ionwave",
    displayName: "Ionwave (any agency — supply 'org')",
    adapter: ionwaveAdapter,
    notes: "Generic Ionwave scrape; pass org=<subdomain>.",
  },
  { name: "demandstar", displayName: "DemandStar (browse portal)", adapter: demandstarAdapter },
  {
    name: "planetbids",
    displayName: "PlanetBids (browse portal)",
    adapter: planetbidsAdapter,
    env: { baseUrl: "PLANETBIDS_BASE_URL" },
  },
];

export function getSource(name: string): SourceDef | undefined {
  return SOURCES.find((s) => s.name === name.toLowerCase());
}

/** Resolve the runtime config for a source from its fixed values + environment. */
export function resolveConfig(def: SourceDef): SourceConfig {
  const e = def.env;
  return {
    apiKey: e?.apiKey ? process.env[e.apiKey] : undefined,
    baseUrl: e?.baseUrl ? process.env[e.baseUrl] : undefined,
    clientId: e?.clientId ? process.env[e.clientId] : undefined,
    clientSecret: e?.clientSecret ? process.env[e.clientSecret] : undefined,
    tokenUrl: e?.tokenUrl ? process.env[e.tokenUrl] : undefined,
    searchPath: e?.searchPath ? process.env[e.searchPath] : undefined,
    org: def.fixed?.org,
  };
}

/** True when a source can run now (no missing credentials). */
export function isConfigured(def: SourceDef): boolean {
  const cfg = resolveConfig(def);
  if (def.adapter.auth === "api-key" && !cfg.apiKey) return false;
  if (def.adapter.auth === "oauth" && (!cfg.clientId || !cfg.clientSecret)) return false;
  if (def.adapter.reliability === "requires-config" && !cfg.baseUrl) return false;
  return true;
}
