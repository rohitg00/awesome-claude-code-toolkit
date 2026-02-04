const { execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const input = JSON.parse(process.argv[2] || "{}");
const filePath = input.file_path || input.filePath || "";
if (!filePath) process.exit(0);

const ext = path.extname(filePath).toLowerCase();
if (![".ts", ".tsx"].includes(ext)) process.exit(0);

let tsconfigDir = path.dirname(filePath);
while (tsconfigDir !== path.dirname(tsconfigDir)) {
  if (fs.existsSync(path.join(tsconfigDir, "tsconfig.json"))) break;
  tsconfigDir = path.dirname(tsconfigDir);
}

if (!fs.existsSync(path.join(tsconfigDir, "tsconfig.json"))) {
  process.exit(0);
}

try {
  execFileSync("npx", ["tsc", "--noEmit", "--pretty"], {
    stdio: "pipe",
    timeout: 30000,
    cwd: tsconfigDir,
  });
  console.log(JSON.stringify({ typeCheck: "pass", file: filePath }));
} catch (e) {
  const output = (e.stdout || "").toString();
  const relevantErrors = output
    .split("\n")
    .filter((line) => line.includes(path.basename(filePath)))
    .slice(0, 5)
    .join("\n");
  console.log(
    JSON.stringify({
      typeCheck: "fail",
      file: filePath,
      errors: relevantErrors || output.slice(0, 500),
    })
  );
}
