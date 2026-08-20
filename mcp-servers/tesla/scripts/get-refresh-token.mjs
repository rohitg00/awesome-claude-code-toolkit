#!/usr/bin/env node
/**
 * Obtain a Tesla refresh token (owner/app-style auth) with the standard
 * OAuth2 PKCE flow — the same tokens the mobile app uses.
 *
 * Interactive (default):
 *   node scripts/get-refresh-token.mjs [--write-config]
 *
 * Two-step / non-interactive (used by the /tesla-connector:setup command):
 *   node scripts/get-refresh-token.mjs --print-url
 *     → prints the tesla.com login URL; the PKCE verifier is saved to
 *       ~/.config/tesla-mcp/pkce-pending.json
 *   node scripts/get-refresh-token.mjs --exchange "<pasted redirect URL>" --write-config
 *     → exchanges the code and (with --write-config) stores the refresh token
 *       in ~/.config/tesla-mcp/config.json (chmod 600) so the connector's
 *       bootstrap picks it up automatically. No env editing needed.
 *
 * Flow: sign in at the printed URL (MFA/passkeys fine); the browser lands on
 * a "Page Not Found" at https://auth.tesla.com/void/callback?code=... —
 * that full URL is what gets pasted/passed back. Nothing is sent anywhere
 * except auth.tesla.com.
 */

import { createHash, randomBytes } from "node:crypto";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { createInterface } from "node:readline/promises";

const AUTH_BASE = process.env.TESLA_AUTH_BASE || "https://auth.tesla.com";
const REDIRECT = `${AUTH_BASE}/void/callback`;
const CONFIG_DIR = process.env.TESLA_CONFIG_DIR || join(homedir(), ".config", "tesla-mcp");
const CONFIG_PATH = process.env.TESLA_CONFIG_PATH || join(CONFIG_DIR, "config.json");
const PENDING_PATH = join(CONFIG_DIR, "pkce-pending.json");

const args = process.argv.slice(2);
const flag = (name) => args.includes(name);
const flagValue = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};

const b64url = (buf) => buf.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

function buildAuthUrl(verifier, state) {
  const challenge = b64url(createHash("sha256").update(verifier).digest());
  return (
    `${AUTH_BASE}/oauth2/v3/authorize?` +
    new URLSearchParams({
      client_id: "ownerapi",
      code_challenge: challenge,
      code_challenge_method: "S256",
      redirect_uri: REDIRECT,
      response_type: "code",
      scope: "openid email offline_access",
      state,
    })
  );
}

async function exchange(pastedUrl, verifier) {
  let code;
  try {
    code = new URL(pastedUrl.trim()).searchParams.get("code");
  } catch {
    code = null;
  }
  if (!code) throw new Error("Could not find ?code=... in the pasted URL. Re-run the auth flow.");
  const res = await fetch(`${AUTH_BASE}/oauth2/v3/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code",
      client_id: "ownerapi",
      code,
      code_verifier: verifier,
      redirect_uri: REDIRECT,
    }),
  });
  if (!res.ok) throw new Error(`Token exchange failed (${res.status}): ${(await res.text()).slice(0, 400)}`);
  return res.json();
}

function writeConfig(tokens) {
  mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
  let config = {};
  try {
    config = JSON.parse(readFileSync(CONFIG_PATH, "utf8"));
  } catch {}
  config.TESLA_REFRESH_TOKEN = tokens.refresh_token;
  config.TESLA_AUTH_MODE = config.TESLA_AUTH_MODE || "owner";
  writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2) + "\n", { mode: 0o600 });
  return CONFIG_PATH;
}

function finish(tokens) {
  if (flag("--write-config")) {
    const path = writeConfig(tokens);
    const masked = tokens.refresh_token.slice(0, 8) + "…" + tokens.refresh_token.slice(-4);
    console.log(`\n✅ Linked. Refresh token (${masked}) saved to ${path} (mode 600).`);
    console.log("The Tesla connector will pick it up automatically on its next start — no env editing needed.");
  } else {
    console.log("\n✅ Success. Add this to your environment (keep it secret — it IS your car key):\n");
    console.log(`export TESLA_REFRESH_TOKEN="${tokens.refresh_token}"`);
    console.log(
      "\nOptional short-lived access token (expires in ~" + Math.round((tokens.expires_in ?? 3600) / 60) + " min):"
    );
    console.log(`export TESLA_ACCESS_TOKEN="${tokens.access_token}"`);
  }
}

// --- Step 1 of the two-step flow: print URL, stash verifier -----------------
if (flag("--print-url")) {
  const verifier = b64url(randomBytes(64));
  mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
  writeFileSync(PENDING_PATH, JSON.stringify({ verifier, created: new Date().toISOString() }), { mode: 0o600 });
  console.log(buildAuthUrl(verifier, b64url(randomBytes(12))));
  process.exit(0);
}

// --- Step 2: exchange a pasted redirect URL ----------------------------------
if (flag("--exchange")) {
  const pasted = flagValue("--exchange");
  if (!pasted) {
    console.error('Usage: get-refresh-token.mjs --exchange "<redirect URL>" [--write-config]');
    process.exit(1);
  }
  let pending;
  try {
    pending = JSON.parse(readFileSync(PENDING_PATH, "utf8"));
  } catch {
    console.error(`No pending auth found at ${PENDING_PATH}. Run --print-url first.`);
    process.exit(1);
  }
  try {
    const tokens = await exchange(pasted, pending.verifier);
    rmSync(PENDING_PATH, { force: true });
    finish(tokens);
  } catch (err) {
    console.error(`\n${err.message}`);
    process.exit(1);
  }
  process.exit(0);
}

// --- Interactive flow (default) ----------------------------------------------
const verifier = b64url(randomBytes(64));
console.log("\n1) Open this URL in a browser and sign in to your Tesla account:\n");
console.log(`   ${buildAuthUrl(verifier, b64url(randomBytes(12)))}\n`);
console.log('2) After login you will land on a "Page Not Found" — that is normal.');
console.log("   Copy the FULL address bar URL (starts with " + REDIRECT + ").\n");

const rl = createInterface({ input: process.stdin, output: process.stdout });
const pasted = (await rl.question("3) Paste that URL here: ")).trim();
rl.close();

try {
  finish(await exchange(pasted, verifier));
} catch (err) {
  console.error(`\n${err.message}`);
  process.exit(1);
}
