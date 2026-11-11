/** A normalized procurement opportunity, common across every source. */
export interface Opportunity {
  source: string;
  id: string;
  title: string;
  agency?: string;
  status?: string;
  postedDate?: string;
  dueDate?: string;
  url?: string;
  description?: string;
  naics?: string;
  /** NIGP / UNSPSC / PSC or other classification code. */
  category?: string;
  /** Original record, included only when the caller asks for verbose output. */
  raw?: unknown;
}

export type Reliability =
  | "verified" // tested against the live endpoint, stable response shape
  | "best-effort" // works but depends on undocumented HTML/JSON that may drift
  | "requires-key" // documented API that needs a credential to exercise
  | "requires-browser" // data is rendered client-side; plain HTTP cannot read it
  | "requires-config"; // generic adapter that needs a base URL/endpoint supplied

export type AuthKind = "none" | "api-key" | "oauth";

export interface SearchParams {
  keywords?: string;
  /** Two-letter US state filter, where the source supports it. */
  state?: string;
  status?: string;
  limit?: number;
  /** Per-source override, e.g. a Bonfire/Ionwave organization subdomain. */
  org?: string;
  verbose?: boolean;
}

/** Runtime configuration resolved from environment variables. */
export interface SourceConfig {
  apiKey?: string;
  baseUrl?: string;
  org?: string;
  /** OAuth2 client-credentials (e.g. OpenGov Procurement). */
  clientId?: string;
  clientSecret?: string;
  tokenUrl?: string;
  /** Resource path appended to baseUrl for search, where the contract is configurable. */
  searchPath?: string;
}

export interface Adapter {
  platform: string;
  auth: AuthKind;
  reliability: Reliability;
  /** Env var names this adapter reads, surfaced by list_sources. */
  configEnv?: string[];
  search(params: SearchParams, cfg: SourceConfig): Promise<Opportunity[]>;
  getOpportunity?(id: string, cfg: SourceConfig): Promise<Opportunity | null>;
}
