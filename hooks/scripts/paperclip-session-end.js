const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const STATE_FILE = path.join(os.homedir(), ".paperclip", "connector-state.json");
const QUEUE_FILE = path.join(os.homedir(), ".paperclip", "activity-queue.json");

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
  } catch {
    return {};
  }
}

const state = loadState();

if (state.enabled === false) {
  console.log(JSON.stringify({ paperclip: "disabled" }));
  process.exit(0);
}

let queue = [];
try {
  queue = JSON.parse(fs.readFileSync(QUEUE_FILE, "utf8"));
} catch {}

if (queue.length > 0 && state.agentKey && state.activeIssueId) {
  const body =
    "**Session ended** — flushing activity log:\n\n" +
    queue.map((a) => `- **${a.type}**: ${a.summary} _(${a.timestamp})_`).join("\n");
  try {
    execSync(
      `curl -sf http://127.0.0.1:3100/api/issues/${state.activeIssueId}/comments -X POST ` +
        `-H "Authorization: Bearer ${state.agentKey}" ` +
        `-H "Content-Type: application/json" ` +
        `-d '${JSON.stringify({ body }).replace(/'/g, "'\\''")}'`,
      { timeout: 3000, stdio: "pipe" }
    );
    fs.writeFileSync(QUEUE_FILE, "[]");
  } catch {}
}

state.lastSessionEnd = new Date().toISOString();
fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));

console.log(JSON.stringify({ paperclip: "session_logged" }));
