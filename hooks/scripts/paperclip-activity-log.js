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

function loadQueue() {
  try {
    return JSON.parse(fs.readFileSync(QUEUE_FILE, "utf8"));
  } catch {
    return [];
  }
}

function saveQueue(queue) {
  fs.writeFileSync(QUEUE_FILE, JSON.stringify(queue.slice(-50), null, 2));
}

function flushToIssue(state, activities) {
  if (!state.agentKey || !state.activeIssueId) return false;
  const body = activities
    .map((a) => `**${a.type}** ${a.summary} _(${a.timestamp})_`)
    .join("\n");
  try {
    execSync(
      `curl -sf http://127.0.0.1:3100/api/issues/${state.activeIssueId}/comments -X POST ` +
        `-H "Authorization: Bearer ${state.agentKey}" ` +
        `-H "Content-Type: application/json" ` +
        `-d '${JSON.stringify({ body }).replace(/'/g, "'\\''")}'`,
      { timeout: 3000, stdio: "pipe" }
    );
    return true;
  } catch {
    return false;
  }
}

const stdinData = [];
process.stdin.on("data", (chunk) => stdinData.push(chunk));
process.stdin.on("end", () => {
  const input = Buffer.concat(stdinData).toString().trim();
  const state = loadState();
  if (state.enabled === false) {
    console.log(JSON.stringify({}));
    return;
  }

  let event = {};
  try {
    event = JSON.parse(input);
  } catch {
    console.log(JSON.stringify({}));
    return;
  }

  const toolName = event.tool_name || event.toolName || "";
  const toolInput = event.tool_input || event.input || {};
  const toolResult = event.tool_result || event.result || "";

  let activity = null;

  if (toolName === "Bash") {
    const cmd = toolInput.command || "";
    if (cmd.startsWith("git commit")) {
      activity = { type: "commit", summary: cmd.slice(0, 120) };
    } else if (cmd.startsWith("git push")) {
      activity = { type: "push", summary: cmd.slice(0, 120) };
    } else if (cmd.match(/^(npm|pnpm|yarn|bun)\s+(test|run test)/)) {
      const passed = String(toolResult).includes("passed");
      activity = { type: "test", summary: passed ? "Tests passed" : "Tests ran" };
    } else if (cmd.match(/^(npm|pnpm|yarn|bun)\s+(run\s+)?(build|deploy)/)) {
      activity = { type: "build", summary: cmd.slice(0, 80) };
    }
  } else if (toolName === "Write" || toolName === "Edit") {
    const filePath = toolInput.file_path || toolInput.path || "";
    const filename = path.basename(filePath);
    activity = {
      type: toolName === "Write" ? "file_create" : "file_edit",
      summary: filename,
    };
  }

  if (!activity) {
    console.log(JSON.stringify({}));
    return;
  }

  activity.timestamp = new Date().toISOString();
  const queue = loadQueue();
  queue.push(activity);

  const FLUSH_THRESHOLD = 5;

  if (queue.length >= FLUSH_THRESHOLD && state.agentKey && state.activeIssueId) {
    if (flushToIssue(state, queue)) {
      saveQueue([]);
    } else {
      saveQueue(queue);
    }
  } else {
    saveQueue(queue);
  }

  console.log(JSON.stringify({ tracked: activity.type }));
});

if (process.stdin.isTTY) {
  console.log(JSON.stringify({}));
}
