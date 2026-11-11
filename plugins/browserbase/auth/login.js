#!/usr/bin/env node
/**
 * login.js — Browserbase OAuth-style login flow
 *
 * Opens a browser popup to Browserbase's sign-in page, serves a local callback
 * page that validates the API key in real time, then auto-registers it across
 * every credential location and shuts down. The user never copies env vars manually.
 *
 * Usage:
 *   node login.js                     # interactive — opens browser
 *   node login.js --headless          # prints the local URL instead of opening
 *   node login.js --key bb_live_...   # skip the popup, just register this key
 */

const http = require("http");
const { execSync, exec } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const args = process.argv.slice(2);
const headless = args.includes("--headless");
const directKey = args.find((a) => a.startsWith("--key="))?.split("=")[1]
  || (args.indexOf("--key") !== -1 ? args[args.indexOf("--key") + 1] : null);

const BROWSERBASE_SETTINGS_URL = "https://www.browserbase.com/settings";
const BROWSERBASE_SIGNIN_URL = "https://www.browserbase.com/sign-in";

// ─── Credential registration ────────────────────────────────────────────────

function findProjectRoot() {
  let dir = process.cwd();
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, ".git")) || fs.existsSync(path.join(dir, "package.json"))) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

function registerKey(apiKey) {
  const root = findProjectRoot();
  const registered = [];
  const skipped = [];

  // 1. .env
  const envPath = path.join(root, ".env");
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, "utf8");
    if (/^BROWSERBASE_API_KEY=/.test(content)) {
      const current = content.match(/^BROWSERBASE_API_KEY=(.*)$/m)?.[1] || "";
      if (current.startsWith("<") || current.startsWith("${") || !current) {
        const updated = content.replace(/^BROWSERBASE_API_KEY=.*$/m, `BROWSERBASE_API_KEY=${apiKey}`);
        fs.writeFileSync(envPath, updated);
        registered.push(".env (updated placeholder)");
      } else if (current !== apiKey) {
        const updated = content.replace(/^BROWSERBASE_API_KEY=.*$/m, `BROWSERBASE_API_KEY=${apiKey}`);
        fs.writeFileSync(envPath, updated);
        registered.push(".env (updated)");
      } else {
        skipped.push(".env");
      }
    } else {
      fs.appendFileSync(envPath, `\nBROWSERBASE_API_KEY=${apiKey}\n`);
      registered.push(".env (appended)");
    }
  } else {
    fs.writeFileSync(envPath, `BROWSERBASE_API_KEY=${apiKey}\n`);
    registered.push(".env (created)");
  }

  // 2. Shell profiles
  for (const profile of [".bashrc", ".zshrc", ".bash_profile"].map(f => path.join(os.homedir(), f))) {
    if (fs.existsSync(profile)) {
      const content = fs.readFileSync(profile, "utf8");
      if (content.includes("BROWSERBASE_API_KEY")) {
        skipped.push(path.basename(profile));
      } else {
        fs.appendFileSync(profile, `\n# Browserbase API key (added by browserbase plugin)\nexport BROWSERBASE_API_KEY="${apiKey}"\n`);
        registered.push(path.basename(profile));
      }
    }
  }

  // 3. Set in current process
  process.env.BROWSERBASE_API_KEY = apiKey;

  return { registered, skipped };
}

function validateKey(apiKey) {
  if (!apiKey || !apiKey.startsWith("bb_")) return { valid: false, error: "Key must start with bb_" };
  try {
    const raw = execSync(
      `browse cloud projects list --json 2>/dev/null`,
      { env: { ...process.env, BROWSERBASE_API_KEY: apiKey }, timeout: 15000 }
    ).toString();
    // Strip CLI noise: "Update available" banner, npm install hints, deprecation warnings
    const jsonMatch = raw.match(/\[[\s\S]*\]/);
    if (!jsonMatch) {
      return { valid: false, error: "Unexpected CLI output" };
    }
    const projects = JSON.parse(jsonMatch[0]);
    if (Array.isArray(projects) && projects.length > 0 && projects[0].id) {
      return { valid: true, projects };
    }
    return { valid: false, error: "No projects found" };
  } catch (e) {
    return { valid: false, error: e.message?.slice(0, 200) || "Validation failed" };
  }
}

// ─── HTML for the local auth page ───────────────────────────────────────────

function authPageHTML(port) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Browserbase Login</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0a0a0a; color: #e5e5e5;
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; padding: 20px;
  }
  .card {
    background: #171717; border: 1px solid #262626; border-radius: 16px;
    padding: 48px; max-width: 480px; width: 100%; text-align: center;
  }
  .logo { font-size: 48px; margin-bottom: 16px; }
  h1 { font-size: 24px; font-weight: 600; margin-bottom: 8px; color: #fff; }
  .subtitle { color: #a3a3a3; margin-bottom: 32px; line-height: 1.5; }
  .step { text-align: left; margin-bottom: 24px; }
  .step-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%; background: #f97316;
    color: #fff; font-weight: 700; font-size: 14px; margin-right: 12px;
  }
  .step-text { color: #d4d4d4; font-size: 15px; }
  .btn {
    display: inline-block; padding: 14px 32px; background: #f97316;
    color: #fff; border: none; border-radius: 10px; font-size: 16px;
    font-weight: 600; cursor: pointer; text-decoration: none;
    transition: background 0.2s; margin-bottom: 24px; width: 100%;
  }
  .btn:hover { background: #ea580c; }
  .btn-outline {
    background: transparent; border: 1px solid #404040; color: #e5e5e5;
  }
  .btn-outline:hover { background: #262626; }
  .divider { border-top: 1px solid #262626; margin: 24px 0; }
  .key-input {
    width: 100%; padding: 14px 16px; background: #0a0a0a;
    border: 1px solid #333; border-radius: 10px; color: #fff;
    font-family: 'SF Mono', 'Fira Code', monospace; font-size: 14px;
    margin-bottom: 12px; outline: none; transition: border-color 0.2s;
  }
  .key-input:focus { border-color: #f97316; }
  .key-input::placeholder { color: #525252; }
  .status {
    padding: 12px 16px; border-radius: 8px; font-size: 14px;
    margin-top: 12px; display: none;
  }
  .status.success { display: block; background: #052e16; color: #4ade80; border: 1px solid #16a34a; }
  .status.error { display: block; background: #2a0a0a; color: #f87171; border: 1px solid #dc2626; }
  .status.loading { display: block; background: #1a1a2e; color: #60a5fa; border: 1px solid #2563eb; }
  .registered { text-align: left; margin-top: 16px; font-size: 13px; color: #a3a3a3; }
  .registered li { margin: 4px 0; }
  .registered .loc { color: #4ade80; }
  .fade-in { animation: fadeIn 0.3s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  #success-view { display: none; }
</style>
</head>
<body>
<div class="card">
  <!-- Login view -->
  <div id="login-view">
    <div class="logo">🌐</div>
    <h1>Connect to Browserbase</h1>
    <p class="subtitle">Log in to your Browserbase account to automatically configure your API credentials.</p>

    <div class="step">
      <span class="step-num">1</span>
      <span class="step-text">Click below to open Browserbase and sign in</span>
    </div>

    <a class="btn" href="${BROWSERBASE_SIGNIN_URL}" target="_blank" rel="noopener"
       onclick="document.getElementById('step2').style.display='block'">
      Log in to Browserbase →
    </a>

    <div id="step2" style="display:none" class="fade-in">
      <div class="step">
        <span class="step-num">2</span>
        <span class="step-text">
          After signing in, go to
          <a href="${BROWSERBASE_SETTINGS_URL}" target="_blank" style="color:#f97316">Settings → API Keys</a>
          and copy your key
        </span>
      </div>

      <div class="divider"></div>

      <div class="step">
        <span class="step-num">3</span>
        <span class="step-text">Paste your API key below — it starts with <code style="color:#f97316">bb_</code></span>
      </div>

      <input type="text" class="key-input" id="apiKey"
             placeholder="bb_live_..." autocomplete="off" spellcheck="false"
             oninput="handleKeyInput(this.value)">

      <button class="btn" id="submitBtn" onclick="submitKey()" disabled>
        Validate & Save
      </button>

      <div class="status" id="status"></div>
    </div>
  </div>

  <!-- Success view -->
  <div id="success-view" class="fade-in">
    <div class="logo">✅</div>
    <h1>Connected!</h1>
    <p class="subtitle">Your Browserbase API key has been validated and saved.</p>
    <div id="registered-list" class="registered"></div>
    <div class="divider"></div>
    <p style="color:#a3a3a3; font-size: 14px; margin-top: 16px;">
      You can close this window. Your CLI session is ready.
    </p>
  </div>
</div>

<script>
function handleKeyInput(val) {
  const btn = document.getElementById('submitBtn');
  btn.disabled = !val.startsWith('bb_') || val.length < 10;
}

async function submitKey() {
  const key = document.getElementById('apiKey').value.trim();
  const status = document.getElementById('status');
  const btn = document.getElementById('submitBtn');

  status.className = 'status loading';
  status.textContent = 'Validating key and registering credentials...';
  btn.disabled = true;
  btn.textContent = 'Validating...';

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key })
    });
    const data = await res.json();

    if (data.valid) {
      // Switch to success view
      document.getElementById('login-view').style.display = 'none';
      document.getElementById('success-view').style.display = 'block';

      let html = '<p style="margin-bottom:8px; color:#e5e5e5;">Credentials saved to:</p><ul>';
      for (const loc of data.registered) {
        html += '<li><span class="loc">✓</span> ' + loc + '</li>';
      }
      if (data.skipped.length > 0) {
        html += '</ul><p style="margin-top:12px; margin-bottom:8px;">Already configured:</p><ul>';
        for (const loc of data.skipped) {
          html += '<li>— ' + loc + '</li>';
        }
      }
      html += '</ul>';
      if (data.projects && data.projects.length > 0) {
        html += '<p style="margin-top:12px;">Project: <strong style="color:#fff">' + data.projects[0].name + '</strong></p>';
      }
      document.getElementById('registered-list').innerHTML = html;
    } else {
      status.className = 'status error';
      status.textContent = 'Invalid key: ' + (data.error || 'could not connect to Browserbase');
      btn.disabled = false;
      btn.textContent = 'Validate & Save';
    }
  } catch (e) {
    status.className = 'status error';
    status.textContent = 'Connection error: ' + e.message;
    btn.disabled = false;
    btn.textContent = 'Validate & Save';
  }
}
</script>
</body>
</html>`;
}

// ─── Local HTTP server ──────────────────────────────────────────────────────

function startServer() {
  const server = http.createServer((req, res) => {
    if (req.method === "GET" && (req.url === "/" || req.url === "/login")) {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(authPageHTML(server.address().port));
      return;
    }

    if (req.method === "POST" && req.url === "/api/register") {
      let body = "";
      req.on("data", (chunk) => (body += chunk));
      req.on("end", () => {
        try {
          const { key } = JSON.parse(body);
          const validation = validateKey(key);
          if (validation.valid) {
            const { registered, skipped } = registerKey(key);
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
              valid: true,
              registered,
              skipped,
              projects: validation.projects,
            }));
            // Print summary to terminal
            console.log("\n✅ Browserbase API key validated and saved!");
            console.log("\nRegistered in:");
            registered.forEach((l) => console.log(`  + ${l}`));
            if (skipped.length) {
              console.log("Already configured:");
              skipped.forEach((l) => console.log(`  - ${l}`));
            }
            if (validation.projects?.[0]) {
              console.log(`\nProject: ${validation.projects[0].name}`);
            }
            console.log("\nYou can close the browser tab. Shutting down auth server...");
            setTimeout(() => process.exit(0), 2000);
          } else {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ valid: false, error: validation.error }));
          }
        } catch (e) {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ valid: false, error: e.message }));
        }
      });
      return;
    }

    // Health check for the CLI to know the server is up
    if (req.method === "GET" && req.url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok" }));
      return;
    }

    res.writeHead(404);
    res.end("Not found");
  });

  server.listen(0, "127.0.0.1", () => {
    const port = server.address().port;
    const url = `http://127.0.0.1:${port}/login`;

    console.log("🌐 Browserbase Login");
    console.log(`\nAuth server running at: ${url}`);

    if (headless) {
      console.log("\n(headless mode — open the URL above in your browser)");
    } else {
      console.log("Opening browser...\n");
      openBrowser(url);
    }

    console.log("Waiting for you to log in and paste your API key...\n");
  });

  server.on("error", (err) => {
    console.error("Failed to start auth server:", err.message);
    process.exit(1);
  });
}

function openBrowser(url) {
  const platform = process.platform;
  try {
    if (platform === "darwin") {
      exec(`open "${url}"`);
    } else if (platform === "win32") {
      exec(`start "${url}"`);
    } else {
      // Linux — try xdg-open, then sensible-browser, then just print
      exec(`xdg-open "${url}" 2>/dev/null || sensible-browser "${url}" 2>/dev/null`, (err) => {
        if (err) {
          console.log(`\n⚠ Could not open browser automatically.`);
          console.log(`  Open this URL manually: ${url}\n`);
        }
      });
    }
  } catch {
    console.log(`\n⚠ Could not open browser. Open this URL: ${url}\n`);
  }
}

// ─── Direct key mode (--key) ────────────────────────────────────────────────

if (directKey) {
  console.log("🌐 Browserbase — registering provided key...\n");
  const validation = validateKey(directKey);
  if (validation.valid) {
    const { registered, skipped } = registerKey(directKey);
    console.log("✅ API key validated and saved!\n");
    console.log("Registered in:");
    registered.forEach((l) => console.log(`  + ${l}`));
    if (skipped.length) {
      console.log("Already configured:");
      skipped.forEach((l) => console.log(`  - ${l}`));
    }
    if (validation.projects?.[0]) {
      console.log(`\nProject: ${validation.projects[0].name}`);
    }
  } else {
    console.error(`❌ Invalid key: ${validation.error}`);
    process.exit(1);
  }
} else {
  startServer();
}
