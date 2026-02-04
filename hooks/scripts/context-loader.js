const fs = require("fs");
const path = require("path");

const cwd = process.cwd();
const context = {};

const claudeMd = path.join(cwd, "CLAUDE.md");
if (fs.existsSync(claudeMd)) {
  const content = fs.readFileSync(claudeMd, "utf8");
  const lines = content.split("\n").filter((l) => l.trim());
  context.claudeMd = { exists: true, lines: lines.length };
}

const gitDir = path.join(cwd, ".git");
if (fs.existsSync(gitDir)) {
  try {
    const { execFileSync } = require("child_process");
    const branch = execFileSync("git", ["branch", "--show-current"], { cwd, stdio: "pipe" }).toString().trim();
    const status = execFileSync("git", ["status", "--porcelain"], { cwd, stdio: "pipe" }).toString().trim();
    const changedFiles = status ? status.split("\n").length : 0;
    context.git = { branch, changedFiles };
  } catch (e) {}
}

const configFiles = ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", "tsconfig.json"];
context.projectType = configFiles.filter((f) => fs.existsSync(path.join(cwd, f)));

const todoFile = path.join(cwd, ".claude", "todos.json");
if (fs.existsSync(todoFile)) {
  try {
    const todos = JSON.parse(fs.readFileSync(todoFile, "utf8"));
    const pending = Array.isArray(todos) ? todos.filter((t) => !t.done).length : 0;
    context.pendingTodos = pending;
  } catch (e) {}
}

const envExample = path.join(cwd, ".env.example");
const envFile = path.join(cwd, ".env");
if (fs.existsSync(envExample) && !fs.existsSync(envFile)) {
  context.warning = "Missing .env file. Copy from .env.example";
}

console.log(JSON.stringify(context));
