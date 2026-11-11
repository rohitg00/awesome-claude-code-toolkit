const { execSync, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const PAPERCLIP_HOME = path.join(os.homedir(), ".paperclip");
const CONFIG = path.join(PAPERCLIP_HOME, "instances", "default", "config.json");
const CONTEXT_FILE = path.join(PAPERCLIP_HOME, "context.json");
const STATE_FILE = path.join(PAPERCLIP_HOME, "connector-state.json");
const HEALTH_URL = "http://127.0.0.1:3100/api/health";

function isRunning() {
  try {
    execSync(`curl -sf ${HEALTH_URL}`, { timeout: 3000, stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
}

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
  } catch {
    return {};
  }
}

function saveState(state) {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function tryStart() {
  try {
    const dbDir = path.join(PAPERCLIP_HOME, "instances", "default", "db");
    try {
      fs.chmodSync(dbDir, 0o700);
    } catch {}

    const child = spawn("npx", ["paperclipai", "run"], {
      detached: true,
      stdio: "ignore",
      env: { ...process.env },
    });
    child.unref();

    for (let i = 0; i < 10; i++) {
      execSync("sleep 1.5");
      if (isRunning()) return true;
    }
  } catch {}
  return false;
}

const toggleState = loadState();
if (toggleState.enabled === false) {
  console.log(JSON.stringify({ paperclip: { status: "disabled" } }));
  process.exit(0);
}

const output = { paperclip: {} };

if (!fs.existsSync(CONFIG)) {
  output.paperclip.status = "not_installed";
  output.paperclip.note = "Paperclip not onboarded. Run: npx paperclipai onboard --yes";
  console.log(JSON.stringify(output));
  process.exit(0);
}

if (isRunning()) {
  output.paperclip.status = "running";
} else {
  output.paperclip.status = "starting";
  if (tryStart()) {
    output.paperclip.status = "started";
  } else {
    output.paperclip.status = "start_failed";
    output.paperclip.note = "Could not auto-start Paperclip. Run manually: npx paperclipai run";
    console.log(JSON.stringify(output));
    process.exit(0);
  }
}

try {
  const health = JSON.parse(
    execSync(`curl -sf ${HEALTH_URL}`, { timeout: 3000 }).toString()
  );
  output.paperclip.version = health.version;
  output.paperclip.mode = health.deploymentMode;
} catch {}

const state = loadState();
if (state.agentKey && state.companyId) {
  try {
    const me = JSON.parse(
      execSync(
        `curl -sf http://127.0.0.1:3100/api/agents/me -H "Authorization: Bearer ${state.agentKey}"`,
        { timeout: 3000 }
      ).toString()
    );
    output.paperclip.agent = { name: me.name, role: me.role, status: me.status };

    const issues = JSON.parse(
      execSync(
        `curl -sf "http://127.0.0.1:3100/api/companies/${state.companyId}/issues?assigneeAgentId=${me.id}&status=backlog,in_progress" -H "Authorization: Bearer ${state.agentKey}"`,
        { timeout: 3000 }
      ).toString()
    );
    if (Array.isArray(issues) && issues.length > 0) {
      output.paperclip.pendingWork = issues.map((i) => ({
        id: i.identifier,
        title: i.title,
        status: i.status,
      }));
    }
  } catch {}
}

output.paperclip.dashboard = "http://127.0.0.1:3100";
saveState({ ...state, lastSessionStart: new Date().toISOString() });

console.log(JSON.stringify(output));
