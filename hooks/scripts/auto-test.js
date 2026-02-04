const { execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const input = JSON.parse(process.argv[2] || "{}");
const filePath = input.file_path || input.filePath || "";
if (!filePath) process.exit(0);

const ext = path.extname(filePath).toLowerCase();
if (![".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"].includes(ext)) process.exit(0);

const dir = path.dirname(filePath);
const base = path.basename(filePath, ext);
const testPatterns = [
  path.join(dir, `${base}.test${ext}`),
  path.join(dir, `${base}.spec${ext}`),
  path.join(dir, "__tests__", `${base}.test${ext}`),
  path.join(dir, "__tests__", `${base}${ext}`),
  path.join(dir.replace("/src/", "/tests/"), `test_${base}.py`),
];

const testFile = testPatterns.find((p) => fs.existsSync(p));
if (!testFile) process.exit(0);

const runners = {
  ".ts": { cmd: "npx", args: ["vitest", "run", testFile, "--reporter=verbose"] },
  ".tsx": { cmd: "npx", args: ["vitest", "run", testFile, "--reporter=verbose"] },
  ".js": { cmd: "npx", args: ["jest", "--testPathPattern", testFile, "--no-coverage"] },
  ".jsx": { cmd: "npx", args: ["jest", "--testPathPattern", testFile, "--no-coverage"] },
  ".py": { cmd: "python", args: ["-m", "pytest", testFile, "-x", "-q"] },
  ".go": { cmd: "go", args: ["test", "-run", "", "-v", dir] },
  ".rs": { cmd: "cargo", args: ["test", "--quiet"] },
};

const runner = runners[ext];
try {
  const output = execFileSync(runner.cmd, runner.args, {
    stdio: "pipe",
    timeout: 30000,
    cwd: process.cwd(),
  });
  console.log(JSON.stringify({ tests: "pass", file: testFile, output: output.toString().slice(-300) }));
} catch (e) {
  const stderr = (e.stderr || e.stdout || "").toString().slice(0, 500);
  console.log(JSON.stringify({ tests: "fail", file: testFile, output: stderr }));
}
