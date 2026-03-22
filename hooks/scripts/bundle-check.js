const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const input = JSON.parse(process.argv[2] || "{}");
const filePath = input.file_path || input.filePath || "";
if (!filePath) process.exit(0);

const ext = path.extname(filePath).toLowerCase();
if (![".ts", ".tsx", ".js", ".jsx", ".css", ".scss"].includes(ext)) process.exit(0);

const cwd = process.cwd();
const pkgJson = path.join(cwd, "package.json");
if (!fs.existsSync(pkgJson)) process.exit(0);

let pkg;
try {
  pkg = JSON.parse(fs.readFileSync(pkgJson, "utf8"));
} catch (e) {
  process.exit(0);
}

const buildScript = pkg.scripts && (pkg.scripts.build || pkg.scripts["build:prod"]);
if (!buildScript) process.exit(0);

const distDirs = ["dist", "build", ".next", "out"].map((d) => path.join(cwd, d));
const distDir = distDirs.find((d) => fs.existsSync(d));
if (!distDir) process.exit(0);

function getDirSize(dir) {
  let size = 0;
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        size += getDirSize(fullPath);
      } else {
        size += fs.statSync(fullPath).size;
      }
    }
  } catch (e) {}
  return size;
}

const currentSize = getDirSize(distDir);
const sizeMB = (currentSize / 1024 / 1024).toFixed(2);
const thresholdMB = 5;

const result = { bundleSize: `${sizeMB}MB`, directory: path.basename(distDir) };

if (parseFloat(sizeMB) > thresholdMB) {
  result.warning = `Bundle size (${sizeMB}MB) exceeds ${thresholdMB}MB threshold`;
}

console.log(JSON.stringify(result));
