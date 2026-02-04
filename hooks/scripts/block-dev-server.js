const input = JSON.parse(process.argv[2] || "{}");
const command = (input.command || "").toLowerCase();

const devServerPatterns = [
  "npm run dev",
  "npm start",
  "yarn dev",
  "pnpm dev",
  "bun dev",
  "next dev",
  "vite",
  "webpack serve",
  "nodemon",
  "ts-node-dev",
  "python manage.py runserver",
  "flask run",
  "uvicorn",
  "cargo watch",
];

const isDevServer = devServerPatterns.some((p) => command.includes(p));
if (!isDevServer) {
  console.log(JSON.stringify({ allowed: true }));
  process.exit(0);
}

const inTmux = !!process.env.TMUX;
const inScreen = !!process.env.STY;

if (!inTmux && !inScreen) {
  console.log(
    JSON.stringify({
      blocked: true,
      reason: "Dev server commands should run inside tmux or screen to prevent orphaned processes. Start a tmux session first or run the command in the background.",
    })
  );
  process.exit(1);
}

console.log(JSON.stringify({ allowed: true, multiplexer: inTmux ? "tmux" : "screen" }));
