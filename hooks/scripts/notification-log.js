const fs = require("fs");
const path = require("path");
const os = require("os");

const logFile = path.join(os.homedir(), ".claude", "notification-log.json");

const stdinData = [];
process.stdin.on("data", (chunk) => stdinData.push(chunk));
process.stdin.on("end", () => {
  const input = Buffer.concat(stdinData).toString().trim();
  let notification = {};
  try {
    notification = JSON.parse(input);
  } catch (e) {
    notification = { message: input };
  }

  notification.timestamp = new Date().toISOString();
  notification.cwd = process.cwd();

  let logs = [];
  if (fs.existsSync(logFile)) {
    try {
      logs = JSON.parse(fs.readFileSync(logFile, "utf8"));
    } catch (e) {
      logs = [];
    }
  }

  logs.push(notification);
  if (logs.length > 100) logs = logs.slice(-100);

  fs.mkdirSync(path.dirname(logFile), { recursive: true });
  fs.writeFileSync(logFile, JSON.stringify(logs, null, 2));
  console.log(JSON.stringify({ logged: true }));
});

if (process.stdin.isTTY) {
  console.log(JSON.stringify({ logged: false, reason: "no input" }));
}
