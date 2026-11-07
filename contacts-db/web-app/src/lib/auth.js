// Real Google Workspace sign-in (token client). Access is enforced server-side on every request.
import { CFG } from "./config";

let token = null, tokenExp = 0, me = null, gsiReady = null;
const listeners = new Set();
const emit = (msg) => listeners.forEach((fn) => fn(msg));

export const onGate = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
export const currentUser = () => me;

function loadGsi() {
  if (gsiReady) return gsiReady;
  gsiReady = new Promise((res, rej) => {
    const s = document.createElement("script");
    s.src = "https://accounts.google.com/gsi/client";
    s.onload = res;
    s.onerror = () => rej(new Error("Could not load Google sign-in"));
    document.head.appendChild(s);
  });
  return gsiReady;
}

async function getToken(prompt) {
  await loadGsi();
  return new Promise((resolve, reject) => {
    const tc = window.google.accounts.oauth2.initTokenClient({
      client_id: CFG.clientId, scope: "openid email profile", hd: CFG.domain,
      callback: (r) => (r.error ? reject(new Error(r.error)) : resolve(r)),
      error_callback: (e) => reject(new Error(e.type || "auth")),
    });
    tc.requestAccessToken({ prompt: prompt || "" });
  });
}

export async function signIn(prompt) {
  if (CFG.dev) { me = { email: "dev@" + CFG.domain }; return true; }
  if (!CFG.clientId) { emit("This server has no Google OAuth client configured (NTXP_GOOGLE_CLIENT_ID)."); return false; }
  try {
    const r = await getToken(prompt);
    token = r.access_token;
    tokenExp = Date.now() + (r.expires_in - 60) * 1000;
    const res = await fetch("/api/me", { headers: { Authorization: "Bearer " + token } });
    if (!res.ok) { token = null; emit("That account isn't allowed. Sign in with your @" + CFG.domain + " Google account."); return false; }
    me = await res.json();
    return true;
  } catch (e) { emit("Sign-in was cancelled or failed. " + e.message); return false; }
}

export function signOut() {
  if (token && window.google) window.google.accounts.oauth2.revoke(token, () => {});
  token = null; me = null; emit("Signed out.");
}

export async function api(path, opts = {}) {
  if (!CFG.dev && (!token || Date.now() > tokenExp)) { if (!(await signIn(""))) throw new Error("auth"); }
  const headers = { ...(opts.headers || {}) };
  if (token) headers.Authorization = "Bearer " + token;
  let body = opts.body;
  if (body && typeof body !== "string") { body = JSON.stringify(body); headers["Content-Type"] = "application/json"; }
  const r = await fetch(path, { ...opts, body, headers });
  if (r.status === 401) { token = null; emit("Your session expired. Sign in again."); throw new Error("auth"); }
  return r;
}

export async function apiJson(path, opts) {
  const r = await api(path, opts);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

export async function driveToken() {
  await loadGsi();
  return new Promise((res, rej) =>
    window.google.accounts.oauth2.initTokenClient({
      client_id: CFG.clientId, scope: "https://www.googleapis.com/auth/drive", hd: CFG.domain,
      callback: (r) => (r.error ? rej(new Error(r.error)) : res(r.access_token)),
      error_callback: (e) => rej(new Error(e.type || "auth")),
    }).requestAccessToken({ prompt: "" }));
}
