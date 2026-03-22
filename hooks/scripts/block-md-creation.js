const path = require("path");

const input = JSON.parse(process.argv[2] || "{}");
const filePath = input.file_path || input.filePath || "";

if (!filePath.endsWith(".md")) {
  console.log(JSON.stringify({ allowed: true }));
  process.exit(0);
}

const allowedPatterns = [
  "/docs/",
  "/documentation/",
  "CLAUDE.md",
  "AGENTS.md",
  "CHANGELOG.md",
  "CODEMAP.md",
  "CONTRIBUTING.md",
  "SKILL.md",
  "/commands/",
  "/skills/",
  "/agents/",
  "/rules/",
  "/templates/",
];

const isAllowed = allowedPatterns.some((pattern) => filePath.includes(pattern));

if (!isAllowed) {
  const fileName = path.basename(filePath);
  console.log(
    JSON.stringify({
      warning: `Creating ${fileName} outside of standard documentation directories. Make sure this file is intentional and not auto-generated boilerplate.`,
      file: filePath,
    })
  );
} else {
  console.log(JSON.stringify({ allowed: true }));
}
