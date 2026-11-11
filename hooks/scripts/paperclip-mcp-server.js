#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const os = require("os");
const http = require("http");

const STATE_FILE = path.join(os.homedir(), ".paperclip", "connector-state.json");
const BASE_URL = process.env.PAPERCLIP_BASE_URL || "http://127.0.0.1:3100/api";

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
  } catch {
    return {};
  }
}

function getCredentials() {
  const state = loadState();
  return {
    apiKey: process.env.PAPERCLIP_API_KEY || state.agentKey || null,
    companyId: process.env.PAPERCLIP_COMPANY_ID || state.companyId || null,
    enabled: state.enabled !== false,
  };
}

function apiRequest(method, urlPath, body) {
  return new Promise((resolve) => {
    const creds = getCredentials();
    const base = BASE_URL.replace(/\/$/, "");
    const url = new URL(base + (urlPath.startsWith("/") ? "" : "/") + urlPath);
    const opts = {
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname + url.search,
      method,
      headers: { "Content-Type": "application/json" },
      timeout: 8000,
    };
    if (creds.apiKey) opts.headers["Authorization"] = "Bearer " + creds.apiKey;

    const payload = body ? JSON.stringify(body) : null;
    if (payload) opts.headers["Content-Length"] = Buffer.byteLength(payload);

    const req = http.request(opts, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    req.on("error", (e) => resolve({ status: 0, data: null, error: e.message }));
    req.on("timeout", () => { req.destroy(); resolve({ status: 0, data: null, error: "timeout" }); });
    if (payload) req.write(payload);
    req.end();
  });
}

function textResult(obj) {
  return { content: [{ type: "text", text: typeof obj === "string" ? obj : JSON.stringify(obj, null, 2) }] };
}

function errorResult(msg) {
  return { content: [{ type: "text", text: msg }], isError: true };
}

function notRunning() {
  return errorResult("Paperclip server is not running at " + BASE_URL + ". Start it with: npx paperclipai run");
}

const TOOLS = [
  {
    name: "paperclip_health",
    description: "Check if the Paperclip server is running and get version info",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "paperclip_list_issues",
    description: "List issues for the current company. Filter by status (backlog, in_progress, done, cancelled) or limit results.",
    inputSchema: {
      type: "object",
      properties: {
        status: { type: "string", description: "Filter by status: backlog, in_progress, done, cancelled" },
        limit: { type: "number", description: "Max results to return (default 20)" },
      },
    },
  },
  {
    name: "paperclip_create_issue",
    description: "Create a new issue/task in the current company",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string", description: "Issue title" },
        body: { type: "string", description: "Issue description" },
        priority: { type: "string", description: "Priority: low, medium, high, urgent" },
        assigneeAgentId: { type: "string", description: "Agent ID to assign to" },
      },
      required: ["title"],
    },
  },
  {
    name: "paperclip_update_issue",
    description: "Update an issue's status, title, or assignee",
    inputSchema: {
      type: "object",
      properties: {
        issueId: { type: "string", description: "Issue ID (UUID)" },
        status: { type: "string", description: "New status: backlog, in_progress, done, cancelled" },
        title: { type: "string", description: "New title" },
        assigneeAgentId: { type: "string", description: "Agent ID to assign to" },
      },
      required: ["issueId"],
    },
  },
  {
    name: "paperclip_add_comment",
    description: "Add a comment to an issue",
    inputSchema: {
      type: "object",
      properties: {
        issueId: { type: "string", description: "Issue ID (UUID)" },
        body: { type: "string", description: "Comment text" },
      },
      required: ["issueId", "body"],
    },
  },
  {
    name: "paperclip_list_agents",
    description: "List all agents in the current company with their roles and status",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "paperclip_agent_me",
    description: "Get the current agent's identity, role, and status",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "paperclip_costs",
    description: "Get budget and spend summary for the current company",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
];

async function handleTool(name, args) {
  const creds = getCredentials();

  if (!creds.enabled) {
    return errorResult("Paperclip connector is disabled. Run /paperclip-ai:toggle to enable.");
  }

  if (name === "paperclip_health") {
    const r = await apiRequest("GET", "/health");
    if (r.status === 0) return notRunning();
    return textResult(r.data);
  }

  if (!creds.apiKey) {
    return errorResult("No Paperclip API key found. Run: npx paperclipai onboard --yes");
  }

  if (name === "paperclip_agent_me") {
    const r = await apiRequest("GET", "/agents/me");
    if (r.status === 0) return notRunning();
    if (r.status === 401 || r.status === 403) return errorResult("Auth failed. Re-run: npx paperclipai onboard --yes");
    return textResult(r.data);
  }

  if (!creds.companyId) {
    return errorResult("No company ID configured. Set up via: npx paperclipai onboard --yes");
  }

  const companyPath = "/companies/" + creds.companyId;

  if (name === "paperclip_list_issues") {
    let q = companyPath + "/issues?";
    if (args.status) q += "status=" + encodeURIComponent(args.status) + "&";
    if (args.limit) q += "limit=" + args.limit + "&";
    const r = await apiRequest("GET", q);
    if (r.status === 0) return notRunning();
    const issues = Array.isArray(r.data) ? r.data : r.data.items || [];
    const summary = issues.map((i) => ({
      identifier: i.identifier,
      title: i.title,
      status: i.status,
      priority: i.priority,
      assignee: i.assigneeAgentId || "unassigned",
    }));
    return textResult({ count: summary.length, issues: summary });
  }

  if (name === "paperclip_create_issue") {
    const payload = { title: args.title };
    if (args.body) payload.body = args.body;
    if (args.priority) payload.priority = args.priority;
    if (args.assigneeAgentId) payload.assigneeAgentId = args.assigneeAgentId;
    const state = loadState();
    if (state.projectId) payload.projectId = state.projectId;
    const r = await apiRequest("POST", companyPath + "/issues", payload);
    if (r.status === 0) return notRunning();
    if (r.status >= 400) return errorResult("Failed to create issue: " + JSON.stringify(r.data));
    return textResult({ created: r.data.identifier, id: r.data.id, title: r.data.title });
  }

  if (name === "paperclip_update_issue") {
    const payload = {};
    if (args.status) payload.status = args.status;
    if (args.title) payload.title = args.title;
    if (args.assigneeAgentId) payload.assigneeAgentId = args.assigneeAgentId;
    const r = await apiRequest("PATCH", "/issues/" + args.issueId, payload);
    if (r.status === 0) return notRunning();
    if (r.status >= 400) return errorResult("Failed to update issue: " + JSON.stringify(r.data));
    return textResult({ updated: r.data.identifier, status: r.data.status });
  }

  if (name === "paperclip_add_comment") {
    const r = await apiRequest("POST", "/issues/" + args.issueId + "/comments", { body: args.body });
    if (r.status === 0) return notRunning();
    if (r.status >= 400) return errorResult("Failed to add comment: " + JSON.stringify(r.data));
    return textResult({ commented: true, issueId: args.issueId });
  }

  if (name === "paperclip_list_agents") {
    const r = await apiRequest("GET", companyPath + "/agents");
    if (r.status === 0) return notRunning();
    const agents = Array.isArray(r.data) ? r.data : [];
    const summary = agents.map((a) => ({
      id: a.id,
      name: a.name,
      role: a.role,
      title: a.title,
      status: a.status,
      spentMonthlyCents: a.spentMonthlyCents,
    }));
    return textResult({ count: summary.length, agents: summary });
  }

  if (name === "paperclip_costs") {
    const r = await apiRequest("GET", companyPath);
    if (r.status === 0) return notRunning();
    return textResult({
      company: r.data.name,
      budgetMonthlyCents: r.data.budgetMonthlyCents,
      spentMonthlyCents: r.data.spentMonthlyCents,
    });
  }

  return errorResult("Unknown tool: " + name);
}

// --- MCP JSON-RPC over stdio with Content-Length framing ---

const SERVER_INFO = {
  name: "paperclip-mcp",
  version: "1.0.0",
};

function sendMessage(msg) {
  const json = JSON.stringify(msg);
  const header = "Content-Length: " + Buffer.byteLength(json) + "\r\n\r\n";
  process.stdout.write(header + json);
}

function sendResult(id, result) {
  sendMessage({ jsonrpc: "2.0", id, result });
}

function sendError(id, code, message) {
  sendMessage({ jsonrpc: "2.0", id, error: { code, message } });
}

async function handleMessage(msg) {
  if (msg.method === "initialize") {
    sendResult(msg.id, {
      protocolVersion: "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: SERVER_INFO,
    });
    return;
  }

  if (msg.method === "notifications/initialized") {
    return;
  }

  if (msg.method === "tools/list") {
    sendResult(msg.id, { tools: TOOLS });
    return;
  }

  if (msg.method === "tools/call") {
    const { name, arguments: args } = msg.params;
    const result = await handleTool(name, args || {});
    sendResult(msg.id, result);
    return;
  }

  if (msg.method === "ping") {
    sendResult(msg.id, {});
    return;
  }

  if (msg.id !== undefined) {
    sendError(msg.id, -32601, "Method not found: " + msg.method);
  }
}

let buffer = "";
let contentLength = -1;

process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buffer += chunk;

  while (true) {
    if (contentLength === -1) {
      const headerEnd = buffer.indexOf("\r\n\r\n");
      if (headerEnd === -1) break;
      const header = buffer.slice(0, headerEnd);
      const match = header.match(/Content-Length:\s*(\d+)/i);
      if (!match) {
        buffer = buffer.slice(headerEnd + 4);
        continue;
      }
      contentLength = parseInt(match[1], 10);
      buffer = buffer.slice(headerEnd + 4);
    }

    if (Buffer.byteLength(buffer, "utf8") < contentLength) break;

    const bytes = Buffer.from(buffer, "utf8");
    const body = bytes.slice(0, contentLength).toString("utf8");
    buffer = bytes.slice(contentLength).toString("utf8");
    contentLength = -1;

    try {
      const msg = JSON.parse(body);
      handleMessage(msg).catch((e) => {
        if (msg.id !== undefined) sendError(msg.id, -32603, e.message);
      });
    } catch {
      // skip malformed messages
    }
  }
});

process.stdin.on("end", () => setTimeout(() => process.exit(0), 100));
process.stderr.write("Paperclip MCP server started\n");
