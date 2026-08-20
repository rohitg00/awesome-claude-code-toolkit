/**
 * Demo mode: a plausible Model Y parked in Frisco, TX. Lets the MCP tools,
 * dashboard, and Siri endpoints be exercised end-to-end with no credentials.
 * Commands mutate the in-memory state so the dashboard feels alive.
 */

export const MOCK_VEHICLE = {
  id: 1492931420430921,
  vehicle_id: 1689245780,
  id_s: "1492931420430921",
  vin: "7SAYGDEE9PF000000",
  display_name: "Mock Y",
  state: "online",
  in_service: false,
  api_version: 71,
  access_type: "OWNER",
};

export const mockState = {
  charge_state: {
    battery_level: 72,
    usable_battery_level: 71,
    battery_range: 213.4,
    est_battery_range: 188.1,
    charge_limit_soc: 80,
    charge_limit_soc_min: 50,
    charge_limit_soc_max: 100,
    charging_state: "Disconnected",
    charge_port_door_open: false,
    charge_port_latch: "Engaged",
    charger_voltage: 0,
    charger_actual_current: 0,
    charge_amps: 32,
    charge_current_request: 32,
    charge_current_request_max: 48,
    charge_rate: 0,
    minutes_to_full_charge: 0,
    scheduled_charging_mode: "Off",
    time_to_full_charge: 0,
  },
  climate_state: {
    inside_temp: 24.5,
    outside_temp: 31.0,
    driver_temp_setting: 21.0,
    passenger_temp_setting: 21.0,
    is_climate_on: false,
    is_preconditioning: false,
    seat_heater_left: 0,
    seat_heater_right: 0,
    steering_wheel_heater: false,
    defrost_mode: 0,
    climate_keeper_mode: "off",
    cabin_overheat_protection: "On",
    min_avail_temp: 15,
    max_avail_temp: 28,
  },
  drive_state: {
    latitude: 33.150697,
    longitude: -96.823611,
    heading: 194,
    speed: null as number | null,
    power: 0,
    shift_state: null as string | null,
    gps_as_of: 1_750_000_000,
    timestamp: 1_750_000_000_000,
  },
  vehicle_state: {
    locked: true,
    sentry_mode: false,
    sentry_mode_available: true,
    odometer: 18452.7,
    car_version: "2026.20.6 3a4b5c6d",
    df: 0, dr: 0, pf: 0, pr: 0, // doors
    ft: 0, rt: 0, // frunk / trunk
    fd_window: 0, fp_window: 0, rd_window: 0, rp_window: 0,
    valet_mode: false,
    software_update: { status: "", version: "", install_perc: 0, download_perc: 0 },
    vehicle_name: "Mock Y",
    tpms_pressure_fl: 2.9, tpms_pressure_fr: 2.9, tpms_pressure_rl: 2.9, tpms_pressure_rr: 2.9,
  },
  vehicle_config: {
    car_type: "modely",
    exterior_color: "MidnightSilver",
    wheel_type: "Apollo19",
    trim_badging: "74d",
    can_actuate_trunks: true,
    sun_roof_installed: 0,
  },
  gui_settings: {
    gui_distance_units: "mi/hr",
    gui_temperature_units: "F",
    gui_charge_rate_units: "mi/hr",
    gui_24_hour_time: false,
    gui_range_display: "Rated",
  },
};

/** Apply a mock command's side effects and return a command-shaped response. */
export function mockCommand(name: string, body: Record<string, unknown>): { result: boolean; reason: string } {
  const s = mockState;
  switch (name) {
    case "door_lock": s.vehicle_state.locked = true; break;
    case "door_unlock": s.vehicle_state.locked = false; break;
    case "auto_conditioning_start": s.climate_state.is_climate_on = true; break;
    case "auto_conditioning_stop": s.climate_state.is_climate_on = false; break;
    case "set_temps":
      if (typeof body.driver_temp === "number") s.climate_state.driver_temp_setting = body.driver_temp;
      if (typeof body.passenger_temp === "number") s.climate_state.passenger_temp_setting = body.passenger_temp;
      break;
    case "charge_start": s.charge_state.charging_state = "Charging"; break;
    case "charge_stop": s.charge_state.charging_state = "Stopped"; break;
    case "set_charge_limit":
      if (typeof body.percent === "number") s.charge_state.charge_limit_soc = body.percent;
      break;
    case "set_charging_amps":
      if (typeof body.charging_amps === "number") s.charge_state.charge_amps = body.charging_amps;
      break;
    case "charge_port_door_open": s.charge_state.charge_port_door_open = true; break;
    case "charge_port_door_close": s.charge_state.charge_port_door_open = false; break;
    case "set_sentry_mode": s.vehicle_state.sentry_mode = Boolean(body.on); break;
    case "actuate_trunk":
      if (body.which_trunk === "front") s.vehicle_state.ft = s.vehicle_state.ft ? 0 : 1;
      else s.vehicle_state.rt = s.vehicle_state.rt ? 0 : 1;
      break;
    case "window_control": {
      const v = body.command === "vent" ? 1 : 0;
      s.vehicle_state.fd_window = s.vehicle_state.fp_window = v;
      s.vehicle_state.rd_window = s.vehicle_state.rp_window = v;
      break;
    }
    default: break; // Commands without visible mock state still succeed.
  }
  return { result: true, reason: `mock:${name}` };
}

export function mockVehicleData(): Record<string, unknown> {
  return { ...MOCK_VEHICLE, ...mockState };
}
