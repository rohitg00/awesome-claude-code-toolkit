const { execFileSync } = require("child_process");
const path = require("path");

const input = JSON.parse(process.argv[2] || "{}");
const filePath = input.file_path || input.filePath || "";
if (!filePath) process.exit(0);

const ext = path.extname(filePath).toLowerCase();
const lintCommands = {
  ".ts": { cmd: "npx", args: ["eslint", "--no-error-on-unmatched-pattern", filePath] },
  ".tsx": { cmd: "npx", args: ["eslint", "--no-error-on-unmatched-pattern", filePath] },
  ".js": { cmd: "npx", args: ["eslint", "--no-error-on-unmatched-pattern", filePath] },
  ".jsx": { cmd: "npx", args: ["eslint", "--no-error-on-unmatched-pattern", filePath] },
  ".py": { cmd: "ruff", args: ["check", filePath] },
  ".go": { cmd: "go", args: ["vet", filePath] },
  ".rs": { cmd: "cargo", args: ["clippy", "--quiet"] },
};

const linter = lintCommands[ext];
if (!linter) process.exit(0);

try {
  execFileSync(linter.cmd, linter.args, {
    stdio: "pipe",
    timeout: 15000,
    cwd: path.dirname(filePath),
  });
  console.log(JSON.stringify({ lint: "pass", file: filePath }));
} catch (e) {
  const stderr = e.stderr ? e.stderr.toString().slice(0, 500) : "";
  console.log(JSON.stringify({ lint: "issues", file: filePath, output: stderr }));
}
