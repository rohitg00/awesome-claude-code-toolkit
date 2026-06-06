const fs = require("fs");
const path = require("path");
const os = require("os");

const contextFile = path.join(os.homedir(), ".claude", "session-context.json");
const cwd = process.cwd();

let context = {};
if (fs.existsSync(contextFile)) {
  try {
    context = JSON.parse(fs.readFileSync(contextFile, "utf8"));
  } catch (e) {}
}

let pkgManager = "npm";
if (fs.existsSync(path.join(cwd, "pnpm-lock.yaml"))) pkgManager = "pnpm";
else if (fs.existsSync(path.join(cwd, "yarn.lock"))) pkgManager = "yarn";
else if (fs.existsSync(path.join(cwd, "bun.lockb"))) pkgManager = "bun";
else if (fs.existsSync(path.join(cwd, "Pipfile.lock"))) pkgManager = "pipenv";
else if (fs.existsSync(path.join(cwd, "poetry.lock"))) pkgManager = "poetry";
else if (fs.existsSync(path.join(cwd, "go.sum"))) pkgManager = "go mod";
else if (fs.existsSync(path.join(cwd, "Cargo.lock"))) pkgManager = "cargo";

const lastSession = context[cwd];
const output = { packageManager: pkgManager };
if (lastSession) {
  output.previousSession = {
    lastActive: lastSession.lastActive,
    editCount: lastSession.editCount || 0,
    notes: lastSession.notes || "",
  };
}

context[cwd] = { ...context[cwd], packageManager: pkgManager, lastActive: new Date().toISOString(), editCount: 0 };
fs.mkdirSync(path.dirname(contextFile), { recursive: true });
fs.writeFileSync(contextFile, JSON.stringify(context, null, 2));

console.log(JSON.stringify(output));
