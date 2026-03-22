const fs = require("fs");
const path = require("path");
const os = require("os");

const contextFile = path.join(os.homedir(), ".claude", "session-context.json");
const cwd = process.cwd();
const COMPACT_THRESHOLD = 50;

let context = {};
if (fs.existsSync(contextFile)) {
  try {
    context = JSON.parse(fs.readFileSync(contextFile, "utf8"));
  } catch (e) {}
}

const sessionData = context[cwd] || {};
const editCount = (sessionData.editCount || 0) + 1;
sessionData.editCount = editCount;
sessionData.lastActive = new Date().toISOString();
context[cwd] = sessionData;

fs.mkdirSync(path.dirname(contextFile), { recursive: true });
fs.writeFileSync(contextFile, JSON.stringify(context, null, 2));

const output = { editCount };
if (editCount > 0 && editCount % COMPACT_THRESHOLD === 0) {
  output.suggestion = `You have made ${editCount} edits this session. Consider running /compact to free up context window space.`;
}

console.log(JSON.stringify(output));
