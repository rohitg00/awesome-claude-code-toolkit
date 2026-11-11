/**
 * The full tool registry. One declarative list consumed by BOTH surfaces:
 *  - src/index.ts registers every entry as an MCP tool (stdio)
 *  - src/bridge.ts exposes every entry at POST /api/tools/:name (dashboard,
 *    Siri Shortcuts, ChatGPT Actions)
 *
 * Covers the complete Fleet/Owner API vehicle surface: state endpoints,
 * every remote command, plus high-level convenience tools (find my Tesla,
 * drop a pin, navigate-to-car, composite status).
 */

import { z } from "zod";
import { TeslaClient, TeslaApiError } from "./client.js";

export interface ToolDef {
  name: string;
  description: string;
  schema: Record<string, z.ZodTypeAny>;
  handler: (client: TeslaClient, args: Record<string, any>) => Promise<unknown>;
}

const vehicle = z
  .string()
  .optional()
  .describe("VIN, numeric vehicle id, or display name. Optional when the account has one car or TESLA_VIN is set.");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function mapLinks(lat: number, lon: number) {
  const ll = `${lat},${lon}`;
  return {
    apple_maps: `https://maps.apple.com/?ll=${ll}&q=My%20Tesla`,
    google_maps: `https://www.google.com/maps/search/?api=1&query=${ll}`,
    apple_maps_directions: `https://maps.apple.com/?daddr=${ll}&dirflg=d`,
    apple_maps_walking: `https://maps.apple.com/?daddr=${ll}&dirflg=w`,
    google_maps_directions: `https://www.google.com/maps/dir/?api=1&destination=${ll}`,
    geo_uri: `geo:${ll}`,
  };
}

function headingToCompass(heading: number): string {
  const dirs = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"];
  return dirs[Math.round(((heading % 360) / 45)) % 8];
}

async function reverseGeocode(lat: number, lon: number, mock: boolean): Promise<string | undefined> {
  if (mock) return "Preston Rd & Main St parking lot, Frisco, TX 75034";
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=18`,
      { headers: { "User-Agent": "tesla-mcp-server/0.1 (locate-my-car)" }, signal: AbortSignal.timeout(5000) }
    );
    if (!res.ok) return undefined;
    const json = (await res.json()) as { display_name?: string };
    return json.display_name;
  } catch {
    return undefined; // Address is a nicety; coordinates are the contract.
  }
}

interface LocatedVehicle {
  vehicle: string;
  vin: string;
  latitude: number;
  longitude: number;
  heading: number;
  compass: string;
  address?: string;
  links: ReturnType<typeof mapLinks>;
  speak: string;
}

async function locate(client: TeslaClient, idOrVin: string | undefined, wantAddress: boolean): Promise<LocatedVehicle> {
  const v = await client.resolveVehicle(idOrVin);
  const data = await client.vehicleData(v.vin, ["drive_state", "location_data"], true);
  const drive = (data.drive_state ?? {}) as Record<string, any>;
  const lat = Number(drive.latitude ?? drive.active_route_latitude);
  const lon = Number(drive.longitude ?? drive.active_route_longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    throw new Error(
      "Vehicle returned no GPS coordinates. On the Fleet API make sure your app has the 'vehicle_location' scope and the car is awake."
    );
  }
  const heading = Number(drive.heading ?? 0);
  const compass = headingToCompass(heading);
  const address = wantAddress ? await reverseGeocode(lat, lon, client.config.mock) : undefined;
  const name = String(data.display_name ?? v.display_name ?? "your Tesla");
  return {
    vehicle: name,
    vin: v.vin,
    latitude: lat,
    longitude: lon,
    heading,
    compass,
    address,
    links: mapLinks(lat, lon),
    speak: address
      ? `${name} is parked facing ${compass} near ${address}.`
      : `${name} is parked facing ${compass} at ${lat.toFixed(5)}, ${lon.toFixed(5)}.`,
  };
}

/** Compact snapshot used by the dashboard, tesla_status, and Siri summaries. */
export async function statusSnapshot(client: TeslaClient, idOrVin?: string, wake = false) {
  const v = await client.resolveVehicle(idOrVin);
  let data: Record<string, any>;
  try {
    data = await client.vehicleData(v.vin, undefined, wake);
  } catch (err) {
    if (err instanceof TeslaApiError && err.status === 408) {
      return {
        vehicle: v.display_name, vin: v.vin, state: v.state, asleep: true,
        hint: "Vehicle is asleep. Call tesla_wake_up (or pass wake=true) for live data.",
      };
    }
    throw err;
  }
  const cs = (data.charge_state ?? {}) as Record<string, any>;
  const cl = (data.climate_state ?? {}) as Record<string, any>;
  const vs = (data.vehicle_state ?? {}) as Record<string, any>;
  const ds = (data.drive_state ?? {}) as Record<string, any>;
  const cToF = (c: unknown) => (typeof c === "number" ? Math.round((c * 9) / 5 + 32) : null);
  return {
    vehicle: String(data.display_name ?? v.display_name),
    vin: v.vin,
    state: v.state,
    asleep: false,
    battery: {
      level_percent: cs.battery_level ?? null,
      range_miles: cs.battery_range ?? null,
      charge_limit_percent: cs.charge_limit_soc ?? null,
      charging_state: cs.charging_state ?? null,
      minutes_to_full: cs.minutes_to_full_charge ?? null,
      charge_amps: cs.charge_amps ?? null,
      charge_port_open: cs.charge_port_door_open ?? null,
    },
    climate: {
      inside_c: cl.inside_temp ?? null,
      inside_f: cToF(cl.inside_temp),
      outside_c: cl.outside_temp ?? null,
      outside_f: cToF(cl.outside_temp),
      is_climate_on: cl.is_climate_on ?? null,
      driver_setting_c: cl.driver_temp_setting ?? null,
    },
    security: {
      locked: vs.locked ?? null,
      sentry_mode: vs.sentry_mode ?? null,
      doors_open: [vs.df, vs.dr, vs.pf, vs.pr].some((d: unknown) => d === 1),
      frunk_open: vs.ft === 1,
      trunk_open: vs.rt === 1,
      windows_open: [vs.fd_window, vs.fp_window, vs.rd_window, vs.rp_window].some((w: unknown) => w === 1),
    },
    location:
      Number.isFinite(Number(ds.latitude)) && Number.isFinite(Number(ds.longitude))
        ? { latitude: ds.latitude, longitude: ds.longitude, heading: ds.heading, links: mapLinks(ds.latitude, ds.longitude) }
        : null,
    odometer_miles: vs.odometer ?? null,
    software_version: vs.car_version ?? null,
  };
}

/** Factory for the many command tools that share the same shape. */
function cmd(
  name: string,
  apiCommand: string,
  description: string,
  extra: Record<string, z.ZodTypeAny> = {},
  body: (args: Record<string, any>) => Record<string, unknown> = () => ({})
): ToolDef {
  return {
    name,
    description,
    schema: { vehicle, ...extra },
    handler: async (client, args) => {
      const out = await client.command(apiCommand, args.vehicle, body(args));
      return { ok: true, command: apiCommand, ...out };
    },
  };
}

// ---------------------------------------------------------------------------
// Convenience tools (the "main purpose" flows: find, pin, lock/unlock)
// ---------------------------------------------------------------------------

const convenienceTools: ToolDef[] = [
  {
    name: "tesla_find_my_tesla",
    description:
      "Find where the car is parked. Wakes it if needed and returns GPS coordinates, a street address, compass heading, Apple/Google Maps links, and a speakable one-line summary. Use when someone can't find their Tesla.",
    schema: {
      vehicle,
      resolve_address: z.boolean().optional().describe("Reverse-geocode to a street address (default true)."),
    },
    handler: (client, args) => locate(client, args.vehicle, args.resolve_address !== false),
  },
  {
    name: "tesla_drop_pin",
    description:
      "Drop a pin at the car's current location: returns a ready-to-text share message with Apple Maps and Google Maps links so family or friends can navigate straight to the car.",
    schema: { vehicle },
    handler: async (client, args) => {
      const loc = await locate(client, args.vehicle, true);
      const share =
        `📍 ${loc.vehicle} is parked here` +
        (loc.address ? ` (${loc.address})` : "") +
        `\nApple Maps: ${loc.links.apple_maps}\nGoogle Maps: ${loc.links.google_maps}`;
      return { ...loc, share_message: share };
    },
  },
  {
    name: "tesla_navigate_to_tesla",
    description:
      "Get turn-by-turn directions TO the parked car. Returns walking and driving deep links (Apple Maps / Google Maps) that open navigation immediately — ideal for a Siri Shortcut or when leaving an airport/stadium.",
    schema: { vehicle },
    handler: async (client, args) => {
      const loc = await locate(client, args.vehicle, true);
      return {
        ...loc,
        open_walking: loc.links.apple_maps_walking,
        open_driving: loc.links.apple_maps_directions,
        speak: `Starting directions to ${loc.vehicle}. ${loc.speak}`,
      };
    },
  },
  {
    name: "tesla_status",
    description:
      "Composite snapshot: battery, range, charging, climate, lock/sentry state, open doors/windows, location with map links, odometer, and software version. The dashboard is built on this.",
    schema: {
      vehicle,
      wake: z.boolean().optional().describe("Wake the car if asleep (default false: report 'asleep' instead)."),
    },
    handler: (client, args) => statusSnapshot(client, args.vehicle, args.wake === true),
  },
];

// ---------------------------------------------------------------------------
// Vehicle data tools
// ---------------------------------------------------------------------------

function stateSection(name: string, key: string, description: string, endpoints: string[]): ToolDef {
  return {
    name,
    description,
    schema: { vehicle },
    handler: async (client, args) => {
      const data = await client.vehicleData(args.vehicle, endpoints, true);
      return data[key] ?? data;
    },
  };
}

const dataTools: ToolDef[] = [
  {
    name: "tesla_list_vehicles",
    description: "List every vehicle on the Tesla account with VIN, display name, and online/asleep state.",
    schema: {},
    handler: async (client) =>
      (await client.listVehicles()).map((v) => ({
        display_name: v.display_name,
        vin: v.vin,
        id: v.id_s,
        state: v.state,
        in_service: v.in_service ?? false,
      })),
  },
  {
    name: "tesla_wake_up",
    description: "Wake a sleeping vehicle and wait until it is online (most data/commands need an awake car).",
    schema: { vehicle },
    handler: async (client, args) => {
      const v = await client.wakeUp(args.vehicle);
      return { display_name: v.display_name, vin: v.vin, state: v.state };
    },
  },
  {
    name: "tesla_vehicle_data",
    description:
      "Raw full vehicle state (every section) or a filtered subset via 'endpoints' (charge_state, climate_state, drive_state, location_data, gui_settings, vehicle_config, vehicle_state).",
    schema: {
      vehicle,
      endpoints: z.array(z.string()).optional().describe("Sections to include; default all."),
      wake: z.boolean().optional().describe("Wake the car first if asleep (default true)."),
    },
    handler: (client, args) => client.vehicleData(args.vehicle, args.endpoints, args.wake !== false),
  },
  {
    name: "tesla_location",
    description: "Current GPS position: coordinates, heading, speed, and map links. (Prefer tesla_find_my_tesla for a human-friendly answer.)",
    schema: { vehicle },
    handler: async (client, args) => {
      const loc = await locate(client, args.vehicle, false);
      return loc;
    },
  },
  stateSection("tesla_charge_state", "charge_state", "Battery and charging detail: level, range, charging state, limit, amps, time to full, port status, scheduled charging.", ["charge_state"]),
  stateSection("tesla_climate_state", "climate_state", "Cabin climate detail: inside/outside temps, HVAC on/off, seat and steering-wheel heaters, defrost, climate keeper, cabin overheat protection.", ["climate_state"]),
  stateSection("tesla_vehicle_state", "vehicle_state", "Body state: locks, doors, trunks, windows, sentry, odometer, TPMS pressures, software update status, valet mode.", ["vehicle_state"]),
  stateSection("tesla_drive_state", "drive_state", "Raw drive state: gear, speed, power, GPS fix.", ["drive_state", "location_data"]),
  stateSection("tesla_vehicle_config", "vehicle_config", "Static configuration: model, trim, color, wheels, whether trunks/sunroof are remotely actuatable.", ["vehicle_config"]),
  stateSection("tesla_gui_settings", "gui_settings", "Driver display preferences: distance/temperature/charge-rate units, 24h time, range display mode.", ["gui_settings"]),
  {
    name: "tesla_nearby_charging_sites",
    description: "Superchargers and destination chargers near the car, with distance and live stall availability.",
    schema: { vehicle },
    handler: (client, args) => client.nearbyChargingSites(args.vehicle),
  },
  {
    name: "tesla_release_notes",
    description: "Software release notes for the car's current (or staged) firmware.",
    schema: { vehicle },
    handler: (client, args) =>
      client.simpleGet("/release_notes", args.vehicle, { release_notes: [{ title: "Mock release", subtitle: "2026.20.6" }] }),
  },
  {
    name: "tesla_service_data",
    description: "Service status: whether the car is in service and expected completion.",
    schema: { vehicle },
    handler: (client, args) => client.simpleGet("/service_data", args.vehicle, { service_status: "none" }),
  },
  {
    name: "tesla_mobile_enabled",
    description: "Whether mobile/remote access is enabled on the vehicle (Controls > Safety > Allow Mobile Access).",
    schema: { vehicle },
    handler: (client, args) => client.simpleGet("/mobile_enabled", args.vehicle, true),
  },
];

// ---------------------------------------------------------------------------
// Command tools — security, climate, charging, body, nav, media, misc
// ---------------------------------------------------------------------------

const securityTools: ToolDef[] = [
  cmd("tesla_lock_doors", "door_lock", "Lock the car remotely."),
  cmd("tesla_unlock_doors", "door_unlock", "Unlock the car remotely — e.g. let family in while you're away from home."),
  cmd("tesla_honk_horn", "honk_horn", "Honk the horn briefly (good for locating the car in a garage)."),
  cmd("tesla_flash_lights", "flash_lights", "Flash the headlights once."),
  cmd(
    "tesla_remote_start_drive",
    "remote_start_drive",
    "Enable keyless driving for 2 minutes so someone can drive without a key card."
  ),
  cmd(
    "tesla_set_sentry_mode",
    "set_sentry_mode",
    "Turn Sentry Mode (camera surveillance while parked) on or off.",
    { on: z.boolean().describe("true = enable Sentry Mode") },
    (a) => ({ on: a.on })
  ),
  cmd(
    "tesla_set_valet_mode",
    "set_valet_mode",
    "Enable/disable valet mode (speed + access restrictions). A 4-digit PIN is required the first time.",
    { on: z.boolean(), pin: z.string().optional().describe("4-digit PIN (required when enabling for the first time).") },
    (a) => ({ on: a.on, ...(a.pin ? { password: a.pin } : {}) })
  ),
  cmd("tesla_reset_valet_pin", "reset_valet_pin", "Clear the saved valet-mode PIN."),
  cmd(
    "tesla_speed_limit_set",
    "speed_limit_set_limit",
    "Set the Speed Limit Mode maximum speed (50–90 mph).",
    { limit_mph: z.number().min(50).max(90) },
    (a) => ({ limit_mph: a.limit_mph })
  ),
  cmd("tesla_speed_limit_activate", "speed_limit_activate", "Activate Speed Limit Mode.", { pin: z.string().describe("4-digit PIN") }, (a) => ({ pin: a.pin })),
  cmd("tesla_speed_limit_deactivate", "speed_limit_deactivate", "Deactivate Speed Limit Mode.", { pin: z.string().describe("4-digit PIN") }, (a) => ({ pin: a.pin })),
  cmd("tesla_speed_limit_clear_pin", "speed_limit_clear_pin", "Clear the Speed Limit Mode PIN.", { pin: z.string().describe("4-digit PIN") }, (a) => ({ pin: a.pin })),
  cmd(
    "tesla_guest_mode",
    "guest_mode",
    "Enable/disable Guest Mode (car behaves as if handed to a guest; pairs with the Tesla app guest flow).",
    { enable: z.boolean() },
    (a) => ({ enable: a.enable })
  ),
];

const climateTools: ToolDef[] = [
  cmd("tesla_climate_on", "auto_conditioning_start", "Start climate control / preconditioning (heats or cools cabin to the set temperature)."),
  cmd("tesla_climate_off", "auto_conditioning_stop", "Stop climate control."),
  cmd(
    "tesla_set_temperature",
    "set_temps",
    "Set driver (and optionally passenger) cabin temperature. Accepts Celsius by default; pass unit='F' for Fahrenheit.",
    {
      temp: z.number().describe("Target temperature."),
      passenger_temp: z.number().optional().describe("Passenger side target; defaults to the driver value."),
      unit: z.enum(["C", "F"]).optional().describe("Unit of the given temps (default C)."),
    },
    (a) => {
      const toC = (t: number) => (a.unit === "F" ? Math.round(((t - 32) * 5) / 9 * 2) / 2 : t);
      const driver = toC(a.temp);
      return { driver_temp: driver, passenger_temp: a.passenger_temp != null ? toC(a.passenger_temp) : driver };
    }
  ),
  cmd(
    "tesla_set_climate_keeper",
    "set_climate_keeper_mode",
    "Set Climate Keeper: off, keep (stay on while parked), dog (Dog Mode), or camp (Camp Mode).",
    { mode: z.enum(["off", "keep", "dog", "camp"]) },
    (a) => ({ climate_keeper_mode: { off: 0, keep: 1, dog: 2, camp: 3 }[a.mode as "off" | "keep" | "dog" | "camp"] })
  ),
  cmd(
    "tesla_set_seat_heater",
    "remote_seat_heater_request",
    "Set a seat heater level. Seats: 0 driver, 1 passenger, 2 rear-left, 4 rear-center, 5 rear-right.",
    { seat: z.number().int().min(0).max(8), level: z.number().int().min(0).max(3).describe("0 off … 3 high") },
    (a) => ({ heater: a.seat, level: a.level })
  ),
  cmd(
    "tesla_set_seat_cooler",
    "remote_seat_cooler_request",
    "Set a ventilated-seat cooling level (vehicles with cooled seats). Seats: 1 driver, 2 passenger.",
    { seat: z.number().int().min(0).max(8), level: z.number().int().min(0).max(3) },
    (a) => ({ seat_position: a.seat, seat_cooler_level: a.level })
  ),
  cmd(
    "tesla_steering_wheel_heater",
    "remote_steering_wheel_heater_request",
    "Turn the steering wheel heater on or off.",
    { on: z.boolean() },
    (a) => ({ on: a.on })
  ),
  cmd(
    "tesla_max_defrost",
    "set_preconditioning_max",
    "Toggle max defrost (blasts heat to clear ice/fog).",
    { on: z.boolean() },
    (a) => ({ on: a.on })
  ),
  cmd(
    "tesla_set_bioweapon_mode",
    "set_bioweapon_mode",
    "Toggle Bioweapon Defense Mode (HEPA max filtration; Model S/X/Y with HEPA).",
    { on: z.boolean(), manual_override: z.boolean().optional() },
    (a) => ({ on: a.on, manual_override: a.manual_override ?? false })
  ),
  cmd(
    "tesla_cabin_overheat_protection",
    "set_cabin_overheat_protection",
    "Configure Cabin Overheat Protection.",
    { on: z.boolean(), fan_only: z.boolean().optional().describe("Use fan only (no A/C).") },
    (a) => ({ on: a.on, fan_only: a.fan_only ?? false })
  ),
  cmd(
    "tesla_set_cop_temp",
    "set_cop_temp",
    "Set the Cabin Overheat Protection trigger temperature.",
    { level: z.enum(["low", "medium", "high"]).describe("low≈30C, medium≈35C, high≈40C") },
    (a) => ({ cop_temp: { low: 0, medium: 1, high: 2 }[a.level as "low" | "medium" | "high"] })
  ),
];

const chargingTools: ToolDef[] = [
  cmd("tesla_charge_start", "charge_start", "Start charging (cable must be plugged in)."),
  cmd("tesla_charge_stop", "charge_stop", "Stop charging."),
  cmd(
    "tesla_set_charge_limit",
    "set_charge_limit",
    "Set the charge limit percentage (50–100).",
    { percent: z.number().int().min(50).max(100) },
    (a) => ({ percent: a.percent })
  ),
  cmd(
    "tesla_set_charging_amps",
    "set_charging_amps",
    "Set the charging current in amps (reduce for shared circuits).",
    { amps: z.number().int().min(1).max(48) },
    (a) => ({ charging_amps: a.amps })
  ),
  cmd("tesla_charge_standard", "charge_standard", "Set charge limit to the standard/daily preset."),
  cmd("tesla_charge_max_range", "charge_max_range", "Set charge limit to max range (100%, for trips)."),
  cmd("tesla_charge_port_open", "charge_port_door_open", "Open the charge port door (also unlatches a plugged cable)."),
  cmd("tesla_charge_port_close", "charge_port_door_close", "Close the charge port door."),
  cmd(
    "tesla_scheduled_charging",
    "set_scheduled_charging",
    "Enable/disable scheduled charging at a daily start time.",
    { enable: z.boolean(), time: z.string().optional().describe("HH:MM 24h local vehicle time, e.g. '23:30'. Required when enabling.") },
    (a) => {
      let minutes = 0;
      if (a.time) {
        const [h, m] = String(a.time).split(":").map(Number);
        minutes = (h % 24) * 60 + (m % 60);
      }
      return { enable: a.enable, time: minutes };
    }
  ),
  cmd(
    "tesla_scheduled_departure",
    "set_scheduled_departure",
    "Configure scheduled departure: car finishes charging and preconditions by a departure time.",
    {
      enable: z.boolean(),
      departure_time: z.string().optional().describe("HH:MM 24h local vehicle time."),
      preconditioning: z.boolean().optional(),
      off_peak_charging: z.boolean().optional(),
      end_off_peak_time: z.string().optional().describe("HH:MM end of off-peak window."),
    },
    (a) => {
      const toMin = (t?: string) => {
        if (!t) return 0;
        const [h, m] = String(t).split(":").map(Number);
        return (h % 24) * 60 + (m % 60);
      };
      return {
        enable: a.enable,
        departure_time: toMin(a.departure_time),
        preconditioning_enabled: a.preconditioning ?? false,
        preconditioning_weekdays_only: false,
        off_peak_charging_enabled: a.off_peak_charging ?? false,
        off_peak_charging_weekdays_only: false,
        end_off_peak_time: toMin(a.end_off_peak_time),
      };
    }
  ),
];

const bodyTools: ToolDef[] = [
  cmd(
    "tesla_actuate_trunk",
    "actuate_trunk",
    "Open the frunk, or open/close the rear trunk (powered liftgates toggle).",
    { which: z.enum(["front", "rear"]) },
    (a) => ({ which_trunk: a.which })
  ),
  {
    name: "tesla_window_control",
    description: "Vent or close all windows. (Closing uses the car's own coordinates to satisfy the proximity check.)",
    schema: { vehicle, action: z.enum(["vent", "close"]) },
    handler: async (client, args) => {
      let lat = 0, lon = 0;
      if (args.action === "close") {
        try {
          const loc = await locate(client, args.vehicle, false);
          lat = loc.latitude; lon = loc.longitude;
        } catch { /* fall through with 0,0; some firmware accepts it for close */ }
      }
      const out = await client.command("window_control", args.vehicle, { command: args.action, lat, lon });
      return { ok: true, command: "window_control", ...out };
    },
  },
  cmd(
    "tesla_sunroof_control",
    "sun_roof_control",
    "Vent or close the panoramic sunroof (older Model S with powered sunroof).",
    { state: z.enum(["vent", "close"]) },
    (a) => ({ state: a.state })
  ),
  {
    name: "tesla_trigger_homelink",
    description: "Trigger the nearest programmed HomeLink device (garage door). Uses the car's current position.",
    schema: { vehicle },
    handler: async (client, args) => {
      const loc = await locate(client, args.vehicle, false);
      const out = await client.command("trigger_homelink", args.vehicle, { lat: loc.latitude, lon: loc.longitude });
      return { ok: true, command: "trigger_homelink", ...out };
    },
  },
];

const navTools: ToolDef[] = [
  {
    name: "tesla_send_destination",
    description:
      "Send an address or place name to the car's navigation — the car starts routing when the driver gets in. Great for 'send the restaurant to the car'.",
    schema: { vehicle, destination: z.string().describe("Street address or place name.") },
    handler: async (client, args) => {
      const out = await client.command("navigation_request", args.vehicle, {
        type: "share_ext_content_raw",
        locale: "en-US",
        timestamp_ms: String(Date.now()),
        value: { "android.intent.extra.TEXT": args.destination },
      });
      return { ok: true, command: "navigation_request", sent: args.destination, ...out };
    },
  },
  cmd(
    "tesla_send_gps_destination",
    "navigation_gps_request",
    "Send exact GPS coordinates to the car's navigation.",
    { lat: z.number(), lon: z.number(), order: z.number().int().optional().describe("Waypoint order (default 1).") },
    (a) => ({ lat: a.lat, lon: a.lon, order: a.order ?? 1 })
  ),
  cmd(
    "tesla_navigate_to_supercharger",
    "navigation_sc_request",
    "Route the car to a Supercharger by site id (see tesla_nearby_charging_sites).",
    { supercharger_id: z.number().int(), order: z.number().int().optional() },
    (a) => ({ id: a.supercharger_id, order: a.order ?? 1 })
  ),
];

const mediaAndMiscTools: ToolDef[] = [
  cmd("tesla_media_toggle_playback", "media_toggle_playback", "Play/pause media (someone must be in the car)."),
  cmd("tesla_media_next_track", "media_next_track", "Next track."),
  cmd("tesla_media_prev_track", "media_prev_track", "Previous track."),
  cmd("tesla_media_next_favorite", "media_next_fav", "Next favorite/preset."),
  cmd("tesla_media_prev_favorite", "media_prev_fav", "Previous favorite/preset."),
  cmd("tesla_media_volume_up", "media_volume_up", "Volume up one step."),
  cmd("tesla_media_volume_down", "media_volume_down", "Volume down one step."),
  cmd(
    "tesla_adjust_volume",
    "adjust_volume",
    "Set the media volume directly (0–11).",
    { volume: z.number().min(0).max(11) },
    (a) => ({ volume: a.volume })
  ),
  cmd(
    "tesla_remote_boombox",
    "remote_boombox",
    "Play a sound through the external speaker (Boombox-equipped cars). 0 = random fart, 2000 = locate ping.",
    { sound: z.number().int().optional() },
    (a) => ({ sound: a.sound ?? 2000 })
  ),
  cmd(
    "tesla_schedule_software_update",
    "schedule_software_update",
    "Schedule the staged software update to install after a delay.",
    { delay_seconds: z.number().int().min(0).optional().describe("Seconds from now (default 120).") },
    (a) => ({ offset_sec: a.delay_seconds ?? 120 })
  ),
  cmd("tesla_cancel_software_update", "cancel_software_update", "Cancel a scheduled software update."),
  cmd(
    "tesla_set_vehicle_name",
    "set_vehicle_name",
    "Rename the vehicle (shows in the app and this server).",
    { name: z.string().min(1).max(50) },
    (a) => ({ vehicle_name: a.name })
  ),
  {
    name: "tesla_erase_user_data",
    description:
      "DESTRUCTIVE: factory-erase user data on the car (nav history, homelink, profiles). Only for selling/returning the car. Requires confirm='ERASE'.",
    schema: { vehicle, confirm: z.string().describe("Must be exactly 'ERASE' to proceed.") },
    handler: async (client, args) => {
      if (args.confirm !== "ERASE") {
        throw new Error("Refusing: pass confirm='ERASE' to really erase user data on the vehicle.");
      }
      const out = await client.command("erase_user_data", args.vehicle, {});
      return { ok: true, command: "erase_user_data", ...out };
    },
  },
];

export const TOOLS: ToolDef[] = [
  ...convenienceTools,
  ...dataTools,
  ...securityTools,
  ...climateTools,
  ...chargingTools,
  ...bodyTools,
  ...navTools,
  ...mediaAndMiscTools,
];

export function getTool(name: string): ToolDef | undefined {
  return TOOLS.find((t) => t.name === name || t.name === `tesla_${name}`);
}
