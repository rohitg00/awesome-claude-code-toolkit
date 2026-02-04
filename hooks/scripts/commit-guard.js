const { execFileSync } = require("child_process");

const input = JSON.parse(process.argv[2] || "{}");
const command = input.command || input.input || "";

if (!command.includes("git commit")) process.exit(0);

const msgMatch = command.match(/-m\s+["']([^"']+)["']/);
if (!msgMatch) process.exit(0);

const msg = msgMatch[1];
const errors = [];

const conventionalPattern = /^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?!?:\s.+/;
if (!conventionalPattern.test(msg)) {
  errors.push("Message does not follow conventional commit format: type(scope): description");
}

if (msg.length > 72) {
  errors.push(`Subject line is ${msg.length} chars (max 72)`);
}

if (msg.endsWith(".")) {
  errors.push("Subject line should not end with a period");
}

const firstChar = msg.replace(/^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?!?:\s/, "")[0];
if (firstChar && firstChar === firstChar.toUpperCase()) {
  errors.push("Description should start with lowercase letter");
}

if (errors.length > 0) {
  console.log(
    JSON.stringify({
      decision: "block",
      reason: "Commit message issues:\n" + errors.map((e) => "  - " + e).join("\n"),
    })
  );
} else {
  console.log(JSON.stringify({ decision: "allow", message: "Commit message looks good" }));
}
