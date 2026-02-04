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
sessionData.lastActive = new Date().toISOString();
sessionData.sessionEnd = new Date().toISOString();

const stdinData = [];
process.stdin.on("data", (chunk) => stdinData.push(chunk));
process.stdin.on("end", () => {
  const input = Buffer.concat(stdinData).toString().trim();
  if (input) {
    try {
      const parsed = JSON.parse(input);
      if (parsed.notes) sessionData.notes = parsed.notes;
      if (parsed.editCount) sessionData.editCount = parsed.editCount;
    } catch (e) {}
  }
  context[cwd] = sessionData;
  fs.writeFileSync(contextFile, JSON.stringify(context, null, 2));
  console.log(JSON.stringify({ saved: true, project: cwd }));
});

if (process.stdin.isTTY) {
  context[cwd] = sessionData;
  fs.writeFileSync(contextFile, JSON.stringify(context, null, 2));
  console.log(JSON.stringify({ saved: true, project: cwd }));
}
