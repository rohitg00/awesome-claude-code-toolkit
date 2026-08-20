#!/usr/bin/env node
/**
 * Tesla HTTP bridge: the same tool registry over plain HTTPS-friendly HTTP.
 *
 *   GET  /                     Tesla-themed dashboard GUI
 *   GET  /healthz              liveness (no auth)
 *   GET  /openapi.json         OpenAPI spec for ChatGPT Actions (no auth)
 *   ALL  /mcp                  MCP over streamable HTTP — add as a claude.ai
 *                              custom connector: https://<host>/mcp?token=<TOKEN>
 *   GET  /api/tools            list every tool + params
 *   POST /api/tools/{name}     invoke any tool, JSON body = args
 *   GET  /api/status           composite vehicle snapshot
 *   GET  /siri/find            speakable "where is my car" + map links
 *   GET  /siri/pin             shareable pin message (text family can tap)
 *   GET  /siri/navigate        maps deep link straight to the car
 *   GET  /siri/lock            lock, speakable confirmation
 *   GET  /siri/unlock          unlock, speakable confirmation
 *   GET  /siri/status          one-line battery/lock summary
 *
 * Siri endpoints return plain text by default (perfect for Shortcuts'
 * "Get contents of URL" → "Speak text"); add ?format=json for structure.
 *
 * Auth: every /api and /siri route requires the bridge token, either as
 * `Authorization: Bearer <token>` or `?token=<token>`. Set TESLA_BRIDGE_TOKEN;
 * if unset, a random token is generated and printed at startup.
 */

import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { randomBytes, timingSafeEqual } from "node:crypto";
import { z } from "zod";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { applyConfigFile, loadConfig } from "./config.js";
import { TeslaClient } from "./client.js";
import { buildMcpServer } from "./mcp.js";
import { TOOLS, getTool, statusSnapshot, mapLinks } from "./tools.js";

applyConfigFile();
const config = loadConfig();
const client = new TeslaClient(config);
const PORT = Number(process.env.TESLA_BRIDGE_PORT || 8321);
const HOST = process.env.TESLA_BRIDGE_HOST || "127.0.0.1";
const TOKEN = process.env.TESLA_BRIDGE_TOKEN || randomBytes(24).toString("base64url");

const here = dirname(fileURLToPath(import.meta.url));
const dashboardPath = join(here, "..", "public", "dashboard.html");

function tokenOk(req: IncomingMessage, url: URL): boolean {
  const header = req.headers.authorization || "";
  const presented = header.startsWith("Bearer ") ? header.slice(7) : url.searchParams.get("token") || "";
  const a = Buffer.from(presented);
  const b = Buffer.from(TOKEN);
  return a.length === b.length && timingSafeEqual(a, b);
}

function send(res: ServerResponse, status: number, body: string, type = "application/json") {
  res.writeHead(status, {
    "Content-Type": `${type}; charset=utf-8`,
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Cache-Control": "no-store",
  });
  res.end(body);
}

const json = (res: ServerResponse, status: number, data: unknown) =>
  send(res, status, JSON.stringify(data, null, 2));

async function readBody(req: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req) {
    size += (chunk as Buffer).length;
    if (size > 64 * 1024) throw new Error("Request body too large.");
    chunks.push(chunk as Buffer);
  }
  const text = Buffer.concat(chunks).toString("utf8").trim();
  if (!text) return {};
  return JSON.parse(text) as Record<string, unknown>;
}

async function runTool(name: string, args: Record<string, unknown>): Promise<unknown> {
  const tool = getTool(name);
  if (!tool) throw new Error(`Unknown tool '${name}'. GET /api/tools for the list.`);
  const parsed = z.object(tool.schema).parse(args ?? {});
  return tool.handler(client, parsed);
}

// --- Siri endpoints ---------------------------------------------------------

type SiriResult = { speak: string; open_url?: string; extra?: Record<string, unknown> };

const SIRI_ROUTES: Record<string, (vehicle?: string) => Promise<SiriResult>> = {
  find: async (vehicle) => {
    const loc = (await runTool("tesla_find_my_tesla", { vehicle })) as any;
    return { speak: loc.speak, open_url: loc.links.apple_maps, extra: loc };
  },
  pin: async (vehicle) => {
    const pin = (await runTool("tesla_drop_pin", { vehicle })) as any;
    return { speak: pin.share_message, open_url: pin.links.apple_maps, extra: pin };
  },
  navigate: async (vehicle) => {
    const nav = (await runTool("tesla_navigate_to_tesla", { vehicle })) as any;
    return { speak: nav.speak, open_url: nav.open_walking, extra: nav };
  },
  lock: async (vehicle) => {
    await runTool("tesla_lock_doors", { vehicle });
    return { speak: "Your Tesla is now locked." };
  },
  unlock: async (vehicle) => {
    await runTool("tesla_unlock_doors", { vehicle });
    return { speak: "Your Tesla is now unlocked." };
  },
  status: async (vehicle) => {
    const s = (await runTool("tesla_status", { vehicle })) as any;
    if (s.asleep) return { speak: `${s.vehicle} is asleep. Battery data needs a wake-up.`, extra: s };
    const pieces = [
      `${s.vehicle}: battery ${s.battery.level_percent}%`,
      `${Math.round(s.battery.range_miles)} miles of range`,
      s.security.locked ? "doors locked" : "doors UNLOCKED",
      s.battery.charging_state === "Charging" ? "charging now" : null,
    ].filter(Boolean);
    return { speak: pieces.join(", ") + ".", extra: s };
  },
};

// --- OpenAPI (for ChatGPT Actions / custom GPTs) -----------------------------

function openapi(baseUrl: string): Record<string, unknown> {
  const siriOp = (id: string, summary: string) => ({
    get: {
      operationId: id,
      summary,
      parameters: [
        { name: "vehicle", in: "query", required: false, schema: { type: "string" }, description: "VIN or name; optional with one car." },
        { name: "format", in: "query", required: false, schema: { type: "string", enum: ["text", "json"] } },
      ],
      responses: { "200": { description: "Speakable text (or JSON with ?format=json)." } },
      security: [{ bearer: [] }],
    },
  });
  return {
    openapi: "3.1.0",
    info: {
      title: "Tesla Bridge",
      version: "0.1.0",
      description:
        "Personal Tesla control bridge. Locate the car, drop a pin, navigate to it, lock/unlock, and invoke any of the full tool set.",
    },
    servers: [{ url: baseUrl }],
    paths: {
      "/siri/find": siriOp("findMyTesla", "Where is my Tesla parked? Returns location, address, and map links."),
      "/siri/pin": siriOp("dropPin", "Drop a pin: shareable message with map links to the car."),
      "/siri/navigate": siriOp("navigateToTesla", "Get a maps deep link with directions to the parked car."),
      "/siri/lock": siriOp("lockTesla", "Lock the car."),
      "/siri/unlock": siriOp("unlockTesla", "Unlock the car (e.g. family needs in)."),
      "/siri/status": siriOp("teslaStatus", "One-line battery/range/lock summary."),
      "/api/tools/{name}": {
        post: {
          operationId: "invokeTeslaTool",
          summary: "Invoke any Tesla tool by name (GET /api/tools lists all 50+).",
          parameters: [{ name: "name", in: "path", required: true, schema: { type: "string" } }],
          requestBody: {
            content: { "application/json": { schema: { type: "object", additionalProperties: true } } },
          },
          responses: { "200": { description: "Tool result (JSON)." } },
          security: [{ bearer: [] }],
        },
      },
    },
    components: {
      securitySchemes: { bearer: { type: "http", scheme: "bearer" } },
    },
  };
}

// --- Server ------------------------------------------------------------------

const serverInstance = createServer(async (req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);
  try {
    if (req.method === "OPTIONS") return send(res, 204, "");

    if (url.pathname === "/" || url.pathname === "/dashboard") {
      return send(res, 200, readFileSync(dashboardPath, "utf8"), "text/html");
    }
    if (url.pathname === "/healthz") {
      return json(res, 200, { ok: true, mode: config.mock ? "mock" : config.mode, tools: TOOLS.length });
    }
    if (url.pathname === "/openapi.json") {
      const base = process.env.TESLA_BRIDGE_PUBLIC_URL || `http://${req.headers.host}`;
      return json(res, 200, openapi(base));
    }

    // Everything below requires the bridge token.
    if (!tokenOk(req, url)) {
      return json(res, 401, { error: "Unauthorized. Pass Authorization: Bearer <TESLA_BRIDGE_TOKEN> or ?token=." });
    }

    // MCP over streamable HTTP (stateless): lets claude.ai / Claude mobile add
    // this bridge as a custom connector. Fresh server+transport per request.
    if (url.pathname === "/mcp") {
      const body = req.method === "POST" ? await readBody(req) : undefined;
      const mcp = buildMcpServer(client);
      const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
      res.on("close", () => {
        transport.close();
        mcp.close();
      });
      await mcp.connect(transport);
      await transport.handleRequest(req, res, body);
      return;
    }

    if (url.pathname === "/api/tools" && req.method === "GET") {
      return json(
        res,
        200,
        TOOLS.map((t) => ({
          name: t.name,
          description: t.description,
          params: Object.entries(t.schema).map(([k, v]) => ({
            name: k,
            description: (v as z.ZodTypeAny).description ?? "",
            optional: (v as z.ZodTypeAny).isOptional(),
          })),
        }))
      );
    }

    const toolMatch = url.pathname.match(/^\/api\/tools\/([a-z0-9_]+)$/);
    if (toolMatch && req.method === "POST") {
      const args = await readBody(req);
      return json(res, 200, { ok: true, result: await runTool(toolMatch[1], args) });
    }

    if (url.pathname === "/api/status" && req.method === "GET") {
      return json(res, 200, await statusSnapshot(client, url.searchParams.get("vehicle") || undefined));
    }

    const siriMatch = url.pathname.match(/^\/siri\/([a-z]+)$/);
    if (siriMatch && req.method === "GET") {
      const route = SIRI_ROUTES[siriMatch[1]];
      if (!route) return json(res, 404, { error: `Unknown siri route. Options: ${Object.keys(SIRI_ROUTES).join(", ")}` });
      const out = await route(url.searchParams.get("vehicle") || undefined);
      if (url.searchParams.get("format") === "json") return json(res, 200, out);
      return send(res, 200, out.open_url ? `${out.speak}\n${out.open_url}` : out.speak, "text/plain");
    }

    return json(res, 404, { error: "Not found. Routes: /, /api/tools, /api/status, /siri/{find,pin,navigate,lock,unlock,status}, /openapi.json" });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const status = err instanceof z.ZodError ? 400 : 502;
    if (url.pathname.startsWith("/siri/") && url.searchParams.get("format") !== "json") {
      return send(res, status, `Sorry — ${message}`, "text/plain");
    }
    return json(res, status, { error: message });
  }
});

serverInstance.listen(PORT, HOST, () => {
  console.log(`[tesla-bridge] listening on http://${HOST}:${PORT} — mode=${config.mock ? "MOCK" : config.mode}`);
  console.log(`[tesla-bridge] dashboard: http://${HOST}:${PORT}/`);
  if (!process.env.TESLA_BRIDGE_TOKEN) {
    console.log(`[tesla-bridge] TESLA_BRIDGE_TOKEN not set — generated for this run: ${TOKEN}`);
  }
  console.log(`[tesla-bridge] Siri example: curl -s "http://${HOST}:${PORT}/siri/find?token=<TOKEN>"`);
});
