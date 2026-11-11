/**
 * Token management. Exchanges the long-lived refresh token for short-lived
 * access tokens and caches them (plus any rotated refresh token) on disk so
 * restarts don't burn refresh cycles.
 */

import { readFileSync, writeFileSync } from "node:fs";
import type { TeslaConfig } from "./config.js";

interface CachedTokens {
  access_token?: string;
  refresh_token?: string;
  /** Epoch ms when the access token stops being trusted. */
  expires_at?: number;
}

export class TokenManager {
  private cache: CachedTokens = {};
  private refreshing?: Promise<string>;

  constructor(private readonly config: TeslaConfig) {
    this.cache = this.readCache();
    if (config.accessToken && !this.cache.access_token) {
      // Trust an env-provided access token for a conservative 20 minutes.
      this.cache = { access_token: config.accessToken, expires_at: Date.now() + 20 * 60_000 };
    }
  }

  private readCache(): CachedTokens {
    try {
      return JSON.parse(readFileSync(this.config.tokenCachePath, "utf8")) as CachedTokens;
    } catch {
      return {};
    }
  }

  private writeCache(): void {
    try {
      writeFileSync(this.config.tokenCachePath, JSON.stringify(this.cache, null, 2), { mode: 0o600 });
    } catch {
      // Read-only filesystem is fine; we just refresh more often.
    }
  }

  get currentRefreshToken(): string | undefined {
    return this.cache.refresh_token || this.config.refreshToken;
  }

  async getAccessToken(): Promise<string> {
    if (this.cache.access_token && (this.cache.expires_at ?? 0) > Date.now() + 60_000) {
      return this.cache.access_token;
    }
    // Collapse concurrent refreshes into one request.
    this.refreshing ??= this.refresh().finally(() => (this.refreshing = undefined));
    return this.refreshing;
  }

  private async refresh(): Promise<string> {
    const refreshToken = this.currentRefreshToken;
    if (!refreshToken) {
      throw new Error(
        "No Tesla credentials. Set TESLA_REFRESH_TOKEN (see README 'Getting your Tesla auth'), " +
          "or TESLA_ACCESS_TOKEN for a short session, or TESLA_MOCK=1 for demo mode."
      );
    }

    const body: Record<string, string> = {
      grant_type: "refresh_token",
      client_id: this.config.clientId,
      refresh_token: refreshToken,
    };
    if (this.config.mode === "owner") {
      body.scope = "openid email offline_access";
    } else if (this.config.clientSecret) {
      body.client_secret = this.config.clientSecret;
    }

    const res = await fetch(`${this.config.authBase}/oauth2/v3/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(
        `Tesla token refresh failed (${res.status}). ${text.slice(0, 300)} — ` +
          "your refresh token may be expired or revoked; re-run the auth flow in the README."
      );
    }
    const json = (await res.json()) as {
      access_token: string;
      refresh_token?: string;
      expires_in?: number;
    };

    this.cache = {
      access_token: json.access_token,
      // Tesla rotates refresh tokens on some flows; always keep the newest.
      refresh_token: json.refresh_token || refreshToken,
      expires_at: Date.now() + Math.max(60, (json.expires_in ?? 3600) - 120) * 1000,
    };
    this.writeCache();
    return json.access_token;
  }
}
