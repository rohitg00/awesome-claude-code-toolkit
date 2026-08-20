/**
 * Tesla REST client shared by the MCP server and the HTTP bridge.
 *
 * Works against either API surface:
 *  - Fleet API (official): vehicles are addressed by VIN; 2021+ vehicles need
 *    signed commands, which we route through TESLA_COMMAND_PROXY_URL when set.
 *  - Owner API (legacy/app-style): vehicles are addressed by numeric id.
 */

import type { TeslaConfig } from "./config.js";
import { TokenManager } from "./auth.js";
import { MOCK_VEHICLE, mockCommand, mockVehicleData } from "./mock.js";

export interface VehicleSummary {
  id_s: string;
  vin: string;
  display_name: string;
  state: string;
  [key: string]: unknown;
}

export class TeslaApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body?: string
  ) {
    super(message);
  }
}

const DATA_ENDPOINTS = [
  "charge_state",
  "climate_state",
  "drive_state",
  "location_data",
  "gui_settings",
  "vehicle_config",
  "vehicle_state",
];

export class TeslaClient {
  private tokens: TokenManager;
  private vehicleCache?: { at: number; vehicles: VehicleSummary[] };

  constructor(public readonly config: TeslaConfig) {
    this.tokens = new TokenManager(config);
  }

  /** VIN for Fleet API paths, numeric id for Owner API paths. */
  private tag(v: VehicleSummary): string {
    return this.config.mode === "fleet" ? v.vin : v.id_s;
  }

  private async request<T>(path: string, init?: RequestInit & { base?: string }): Promise<T> {
    const token = await this.tokens.getAccessToken();
    const res = await fetch(`${init?.base ?? this.config.apiBase}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });
    const text = await res.text();
    if (!res.ok) {
      throw new TeslaApiError(
        `Tesla API ${res.status} on ${path}: ${text.slice(0, 300)}`,
        res.status,
        text
      );
    }
    if (!text) return undefined as T;
    const json = JSON.parse(text) as { response?: T };
    return (json.response ?? (json as unknown)) as T;
  }

  async listVehicles(): Promise<VehicleSummary[]> {
    if (this.config.mock) return [MOCK_VEHICLE as unknown as VehicleSummary];
    if (this.vehicleCache && Date.now() - this.vehicleCache.at < 30_000) {
      return this.vehicleCache.vehicles;
    }
    const vehicles = await this.request<VehicleSummary[]>("/api/1/vehicles");
    this.vehicleCache = { at: Date.now(), vehicles };
    return vehicles;
  }

  /** Resolve a VIN, numeric id, or display name to a vehicle; default from config or the only car. */
  async resolveVehicle(idOrVin?: string): Promise<VehicleSummary> {
    const wanted = idOrVin || this.config.defaultVehicle;
    const vehicles = await this.listVehicles();
    if (!vehicles.length) throw new Error("No vehicles on this Tesla account.");
    if (!wanted) {
      if (vehicles.length > 1) {
        throw new Error(
          `Account has ${vehicles.length} vehicles; pass 'vehicle' (VIN or id) or set TESLA_VIN. ` +
            `Choices: ${vehicles.map((v) => `${v.display_name} (${v.vin})`).join(", ")}`
        );
      }
      return vehicles[0];
    }
    const needle = wanted.toLowerCase();
    const match = vehicles.find(
      (v) =>
        v.vin?.toLowerCase() === needle ||
        v.id_s === wanted ||
        String(v.id ?? "") === wanted ||
        v.display_name?.toLowerCase() === needle
    );
    if (!match) {
      throw new Error(
        `No vehicle matching '${wanted}'. Available: ${vehicles.map((v) => `${v.display_name} (${v.vin})`).join(", ")}`
      );
    }
    return match;
  }

  /** Wake the car and poll until it reports online (or timeout). */
  async wakeUp(idOrVin?: string, timeoutMs = 60_000): Promise<VehicleSummary> {
    const v = await this.resolveVehicle(idOrVin);
    if (this.config.mock) return v;
    let latest = await this.request<VehicleSummary>(`/api/1/vehicles/${this.tag(v)}/wake_up`, {
      method: "POST",
    });
    const deadline = Date.now() + timeoutMs;
    while (latest.state !== "online" && Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 3000));
      this.vehicleCache = undefined;
      latest = await this.resolveVehicle(v.vin);
    }
    if (latest.state !== "online") {
      throw new Error(`Vehicle '${v.display_name}' did not wake within ${timeoutMs / 1000}s (state: ${latest.state}).`);
    }
    return latest;
  }

  /**
   * Full (or filtered) vehicle state. `endpoints` narrows the payload;
   * location_data is required on recent firmware for GPS coordinates.
   */
  async vehicleData(idOrVin?: string, endpoints?: string[], autoWake = false): Promise<Record<string, unknown>> {
    if (this.config.mock) return mockVehicleData();
    const v = await this.resolveVehicle(idOrVin);
    const query = `?endpoints=${encodeURIComponent((endpoints?.length ? endpoints : DATA_ENDPOINTS).join(";"))}`;
    try {
      return await this.request<Record<string, unknown>>(
        `/api/1/vehicles/${this.tag(v)}/vehicle_data${query}`
      );
    } catch (err) {
      if (autoWake && err instanceof TeslaApiError && err.status === 408) {
        await this.wakeUp(v.vin);
        return this.request<Record<string, unknown>>(`/api/1/vehicles/${this.tag(v)}/vehicle_data${query}`);
      }
      throw err;
    }
  }

  /**
   * Send a vehicle command. Wakes a sleeping car once and retries. When a
   * command proxy is configured, commands go through it (signed protocol).
   */
  async command(
    name: string,
    idOrVin?: string,
    body: Record<string, unknown> = {},
    autoWake = true
  ): Promise<{ result: boolean; reason: string }> {
    if (this.config.mock) return mockCommand(name, body);
    const v = await this.resolveVehicle(idOrVin);
    const run = () =>
      this.request<{ result: boolean; reason: string }>(
        `/api/1/vehicles/${this.tag(v)}/command/${name}`,
        {
          method: "POST",
          body: JSON.stringify(body),
          base: this.config.commandProxyUrl,
        }
      );
    try {
      const out = await run();
      if (out && out.result === false) {
        throw new Error(`Command '${name}' rejected by vehicle: ${out.reason || "unknown reason"}`);
      }
      return out;
    } catch (err) {
      if (autoWake && err instanceof TeslaApiError && err.status === 408) {
        await this.wakeUp(v.vin);
        return run();
      }
      if (err instanceof TeslaApiError && err.status === 403 && this.config.mode === "fleet" && !this.config.commandProxyUrl) {
        throw new Error(
          `Command '${name}' returned 403. 2021+ vehicles require Tesla's signed command protocol on the Fleet API — ` +
            "run the tesla-http-proxy and set TESLA_COMMAND_PROXY_URL (see README 'Signed commands')."
        );
      }
      throw err;
    }
  }

  async nearbyChargingSites(idOrVin?: string): Promise<Record<string, unknown>> {
    if (this.config.mock) {
      return {
        superchargers: [
          { name: "Frisco, TX - Preston Rd", distance_miles: 1.8, available_stalls: 10, total_stalls: 12 },
          { name: "Plano, TX - Dallas North Tollway", distance_miles: 6.2, available_stalls: 7, total_stalls: 16 },
        ],
        destination_charging: [],
      };
    }
    const v = await this.resolveVehicle(idOrVin);
    return this.request(`/api/1/vehicles/${this.tag(v)}/nearby_charging_sites`);
  }

  async simpleGet(path: string, idOrVin?: string, mockValue?: unknown): Promise<unknown> {
    if (this.config.mock) return mockValue ?? { mock: true };
    const v = await this.resolveVehicle(idOrVin);
    return this.request(`/api/1/vehicles/${this.tag(v)}${path}`);
  }
}
