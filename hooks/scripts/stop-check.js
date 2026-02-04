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

const sessionData = context[cwd] || {};
const editCount = sessionData.editCount || 0;

const reminders = [];

if (editCount > 5) {
  const hasTestCmd =
    fs.existsSync(path.join(cwd, "package.json")) ||
    fs.existsSync(path.join(cwd, "pyproject.toml")) ||
    fs.existsSync(path.join(cwd, "Makefile"));

  if (hasTestCmd) {
    reminders.push(`${editCount} files were modified this session. Consider running the test suite before wrapping up.`);
  }
}

if (editCount > 0) {
  reminders.push("Check for unstaged changes with 'git status' before ending the session.");
}

console.log(JSON.stringify({ reminders, editCount }));
