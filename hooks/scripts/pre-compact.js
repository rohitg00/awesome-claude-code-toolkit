const fs = require("fs");
const path = require("path");
const os = require("os");

const contextFile = path.join(os.homedir(), ".claude", "session-context.json");
const compactLog = path.join(os.homedir(), ".claude", "compact-log.json");
const cwd = process.cwd();

let context = {};
if (fs.existsSync(contextFile)) {
  try {
    context = JSON.parse(fs.readFileSync(contextFile, "utf8"));
  } catch (e) {}
}

const sessionData = context[cwd] || {};
const snapshot = {
  timestamp: new Date().toISOString(),
  project: cwd,
  packageManager: sessionData.packageManager || "unknown",
  editCount: sessionData.editCount || 0,
  notes: sessionData.notes || "",
};

let logs = [];
if (fs.existsSync(compactLog)) {
  try {
    logs = JSON.parse(fs.readFileSync(compactLog, "utf8"));
  } catch (e) {
    logs = [];
  }
}

logs.push(snapshot);
if (logs.length > 50) logs = logs.slice(-50);

fs.mkdirSync(path.dirname(compactLog), { recursive: true });
fs.writeFileSync(compactLog, JSON.stringify(logs, null, 2));

console.log(JSON.stringify({ contextSaved: true, editCount: snapshot.editCount }));
