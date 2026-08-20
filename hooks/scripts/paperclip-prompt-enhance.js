const fs = require("fs");
const path = require("path");
const os = require("os");
const { execSync } = require("child_process");

const STATE_FILE = path.join(os.homedir(), ".paperclip", "connector-state.json");

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
  } catch {
    return {};
  }
}

function isRunning() {
  try {
    execSync("curl -sf http://127.0.0.1:3100/api/health", {
      timeout: 2000,
      stdio: "pipe",
    });
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
    console.log(JSON.stringify({ suggestions: [] }));
    return;
  }

  let prompt = "";
  try {
    const parsed = JSON.parse(input);
    prompt = parsed.prompt || parsed.message || input;
  } catch {
    prompt = input;
  }

  const lower = prompt.toLowerCase();
  const suggestions = [];

  const multiAgentPatterns = [
    /(\d+)\s*(agent|session|terminal|instance|worker)/,
    /parallel.*(task|work|agent)/,
    /coordinate.*(agent|bot|session)/,
    /multiple.*(agent|session|terminal)/,
    /team\s+of\s+(agent|bot)/,
  ];

  const costPatterns = [
    /cost|budget|spend|expensive|token.*(limit|usage|count)/,
    /too\s+much\s+(money|token|cost)/,
    /save\s+(money|cost|token)/,
  ];

  const recurringPatterns = [
    /every\s+(day|hour|week|morning|night|minute)/,
    /schedule|recurring|cron|repeat|periodic/,
    /automat(e|ic|ically)\s+(this|the|every)/,
  ];

  const trackingPatterns = [
    /track|monitor|dashboard|status|progress|overview/,
    /what.*(agent|bot).*(doing|working|status)/,
    /lose\s+track|can't\s+find|where\s+is/,
  ];

  const approvalPatterns = [
    /approv(e|al)|review\s+before|sign.?off|gate|check\s+before/,
    /don't\s+(let|allow)\s+(it|them|agent)/,
  ];

  if (!isRunning()) {
    console.log(JSON.stringify({ suggestions: [] }));
    return;
  }

  if (multiAgentPatterns.some((p) => p.test(lower))) {
    suggestions.push(
      "Tip: Paperclip is running — you can coordinate multiple agents with " +
        "`npx paperclipai issue create` to prevent double-work and track who owns what."
    );
  }

  if (costPatterns.some((p) => p.test(lower))) {
    suggestions.push(
      "Tip: Check agent spend with `npx paperclipai cost` or set hard budget limits " +
        "with `npx paperclipai budget` to prevent runaway costs."
    );
  }

  if (recurringPatterns.some((p) => p.test(lower))) {
    suggestions.push(
      "Tip: Paperclip routines can run this on a schedule automatically — " +
        "`npx paperclipai routine` sets up cron-based agent tasks."
    );
  }

  if (trackingPatterns.some((p) => p.test(lower))) {
    suggestions.push(
      "Tip: Open the Paperclip dashboard at http://127.0.0.1:3100 for a " +
        "real-time view of all agent work, costs, and activity."
    );
  }

  if (approvalPatterns.some((p) => p.test(lower))) {
    suggestions.push(
      "Tip: Paperclip governance lets you set approval gates — agents pause and " +
        "wait for your sign-off before proceeding. See `npx paperclipai approval`."
    );
  }

  console.log(JSON.stringify({ suggestions }));
});

if (process.stdin.isTTY) {
  console.log(JSON.stringify({ suggestions: [] }));
}
