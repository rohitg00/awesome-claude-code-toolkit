const fs = require("fs");
const path = require("path");
const os = require("os");

const logDir = path.join(os.homedir(), ".claude", "learnings");
const logFile = path.join(logDir, `${new Date().toISOString().slice(0, 10)}.json`);

fs.mkdirSync(logDir, { recursive: true });

let learnings = [];
if (fs.existsSync(logFile)) {
  try {
    learnings = JSON.parse(fs.readFileSync(logFile, "utf8"));
  } catch (e) {}
}

const cwd = process.cwd();
const sessionEntry = {
  timestamp: new Date().toISOString(),
  project: path.basename(cwd),
  path: cwd,
};

try {
  const { execFileSync } = require("child_process");
  const log = execFileSync("git", ["log", "--oneline", "-5", "--since=4 hours ago"], {
    cwd,
    stdio: "pipe",
  }).toString().trim();
  if (log) {
    sessionEntry.recentCommits = log.split("\n").map((l) => l.trim());
  }
  const diff = execFileSync("git", ["diff", "--stat"], { cwd, stdio: "pipe" }).toString().trim();
  if (diff) {
    sessionEntry.uncommittedChanges = diff.split("\n").length;
  }
} catch (e) {}

learnings.push(sessionEntry);

if (learnings.length > 100) {
  learnings = learnings.slice(-100);
}

fs.writeFileSync(logFile, JSON.stringify(learnings, null, 2));
console.log(JSON.stringify({ logged: true, file: logFile, entries: learnings.length }));
