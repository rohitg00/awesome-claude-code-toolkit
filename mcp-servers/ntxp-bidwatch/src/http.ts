const DEFAULT_TIMEOUT_MS = Number(process.env.BIDWATCH_TIMEOUT_MS ?? 30_000);
const USER_AGENT =
  process.env.BIDWATCH_USER_AGENT ??
  "Mozilla/5.0 (compatible; ntxp-bidwatch-mcp/0.1; +https://github.com/)";

interface FetchOpts {
  method?: "GET" | "POST";
  headers?: Record<string, string>;
  body?: string;
  timeoutMs?: number;
}

async function request(url: string, opts: FetchOpts = {}): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), opts.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  try {
    return await fetch(url, {
      method: opts.method ?? "GET",
      headers: { "User-Agent": USER_AGENT, ...opts.headers },
      body: opts.body,
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error(`Request to ${url} timed out after ${opts.timeoutMs ?? DEFAULT_TIMEOUT_MS}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function getText(url: string, headers?: Record<string, string>): Promise<string> {
  const res = await request(url, { headers });
  if (!res.ok) throw new Error(`GET ${url} -> ${res.status} ${res.statusText}`);
  return res.text();
}

export async function getJson<T = unknown>(url: string, headers?: Record<string, string>): Promise<T> {
  const res = await request(url, { headers: { Accept: "application/json", ...headers } });
  const text = await res.text();
  if (!res.ok) throw new Error(`GET ${url} -> ${res.status} ${res.statusText}: ${text.slice(0, 300)}`);
  return JSON.parse(text) as T;
}

export async function postJson<T = unknown>(
  url: string,
  body: unknown,
  headers?: Record<string, string>
): Promise<T> {
  const res = await request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json", ...headers },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`POST ${url} -> ${res.status} ${res.statusText}: ${text.slice(0, 300)}`);
  return JSON.parse(text) as T;
}

export async function postForm<T = unknown>(
  url: string,
  form: Record<string, string>,
  headers?: Record<string, string>
): Promise<T> {
  const res = await request(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json", ...headers },
    body: new URLSearchParams(form).toString(),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`POST ${url} -> ${res.status} ${res.statusText}: ${text.slice(0, 300)}`);
  return JSON.parse(text) as T;
}

/** Case-insensitive keyword filter over a record's text fields. */
export function matchesKeywords(haystack: string, keywords?: string): boolean {
  if (!keywords) return true;
  const terms = keywords.toLowerCase().split(/\s+/).filter(Boolean);
  const hay = haystack.toLowerCase();
  return terms.every((t) => hay.includes(t));
}
