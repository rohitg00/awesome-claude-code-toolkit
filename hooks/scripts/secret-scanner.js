const fs = require("fs");
const path = require("path");

const input = JSON.parse(process.argv[2] || "{}");
const filePath = input.file_path || input.filePath || "";
if (!filePath) process.exit(0);

const ext = path.extname(filePath).toLowerCase();
const binaryExts = [".png", ".jpg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".zip", ".tar", ".gz"];
if (binaryExts.includes(ext)) process.exit(0);

let content;
try {
  content = fs.readFileSync(filePath, "utf8");
} catch (e) {
  process.exit(0);
}

const patterns = [
  { name: "AWS Access Key", regex: /AKIA[0-9A-Z]{16}/g },
  { name: "AWS Secret Key", regex: /aws_secret_access_key\s*=\s*["']?[A-Za-z0-9/+=]{40}/gi },
  { name: "GitHub Token", regex: /(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}/g },
  { name: "Private Key", regex: /-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----/g },
  { name: "Generic API Key", regex: /api[_-]?key\s*[:=]\s*["'][a-zA-Z0-9]{20,}["']/gi },
  { name: "Slack Token", regex: /xox[bpors]-[0-9a-zA-Z-]{10,}/g },
  { name: "Database URL", regex: /(postgres|mysql|mongodb|redis):\/\/[^:]+:[^@\s]+@/g },
  { name: "JWT Token", regex: /eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g },
];

const findings = [];
const lines = content.split("\n");

for (const pattern of patterns) {
  for (let i = 0; i < lines.length; i++) {
    if (pattern.regex.test(lines[i])) {
      findings.push({ type: pattern.name, line: i + 1 });
    }
    pattern.regex.lastIndex = 0;
  }
}

if (findings.length > 0) {
  console.log(
    JSON.stringify({
      decision: "block",
      reason: `Potential secrets detected in ${path.basename(filePath)}:\n` +
        findings.map((f) => `  - Line ${f.line}: ${f.type}`).join("\n"),
    })
  );
} else {
  process.exit(0);
}
