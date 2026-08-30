#!/usr/bin/env node
/**
 * leftover-check — "the value you just deleted is still alive over here"
 *
 * PostToolUse hook for Edit / MultiEdit. Takes the tokens that DISAPPEARED from
 * the diff and searches the project for them again. It warns; it never blocks.
 *
 * WHY
 * "Search by concept, not by variable name" is correct advice that fails
 * exactly when your idea of the concept is wrong — and that is the moment you
 * needed the check. Real incident: a magic number was to be removed. It was
 * searched under two names, found in one place, changed, and reported as "no
 * traces left". Three other names for the same value were still live and still
 * rendering. The same shape of mistake recurred four times in three days.
 *
 * There is exactly one check with no judgement in it: look for the thing you
 * just deleted. You do not have to guess what to search for.
 *
 * Matches 1648 and 1,648 as the same value — the thousands separator is how it
 * hid the first time.
 *
 * Fails open: garbage in, exit 0, silence. A hook that interrupts legitimate
 * work gets uninstalled, and an uninstalled hook has a 100% false-negative rate.
 *
 * Reads local files only. Makes no network requests.
 *
 * Canonical version, with tests and the full incident log:
 *   https://github.com/jkrepublic/silent-failure-gates
 * This is a self-contained single-file port. MIT.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const MAX_TOKENS = 3;             // values checked per edit
const MAX_FILES = 500;            // walk cap — slow hooks get disabled
const MAX_BYTES = 400 * 1024;     // skip anything larger
const MAX_HITS = 12;              // reported sites cap

const SCAN_EXT = /\.(js|cjs|mjs|ts|tsx|jsx|vue|svelte|py|rb|php|go|rs|java|kt|cs|swift|html|css|scss|sql|sh|json|ya?ml|md|txt)$/i;
const SKIP_DIR = /^(node_modules|\.git|dist|build|out|target|vendor|__pycache__|\.?venv|\.next|\.nuxt|coverage|backups?|snapshots)$/i;
const ROOT_MARKS = ["package.json", ".git", "pyproject.toml", "go.mod", "Cargo.toml"];

/* Ordinary code words are not values. Without this the hook fires on every edit,
 * and a hook that always fires is a hook you learn to ignore. */
const NOISE = new Set([
  "function", "return", "const", "let", "var", "class", "import", "export",
  "default", "true", "false", "null", "undefined", "this", "async", "await",
  "typeof", "instanceof", "else", "elif", "while", "switch", "case", "break",
  "continue", "throw", "catch", "finally", "yield", "static", "public",
  "private", "protected", "extends", "implements", "interface", "struct",
  "length", "push", "join", "split", "slice", "splice", "replace", "filter",
  "map", "forEach", "reduce", "concat", "indexOf", "includes", "toString",
  "console", "window", "document", "innerHTML", "textContent", "value", "type",
  "name", "self", "print", "from", "None", "True", "False", "lambda", "def",
  "span", "style", "href", "http", "https", "utf", "json", "data", "item",
  "items", "index", "result", "results", "error", "string", "number", "boolean",
]);

function quit() { process.exit(0); }

function tell(text) {
  console.log(JSON.stringify({
    hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: text },
  }));
  process.exit(0);
}

/** Tokens present in `oldStr` and gone from `newStr`. */
function vanished(oldStr, newStr) {
  const grab = (s) => {
    const out = new Set();
    for (const m of String(s).matchAll(/[A-Za-z_][A-Za-z0-9_]{3,}/g)) {
      if (!NOISE.has(m[0])) out.add(m[0]);
    }
    for (const m of String(s).matchAll(/\d[\d,]{1,}\d/g)) {
      const bare = m[0].replace(/,/g, "");
      if (bare.length >= 3) out.add(bare);
    }
    return out;
  };
  const before = grab(oldStr), after = grab(newStr);
  const gone = [...before].filter((t) => !after.has(t));
  // longest first — long tokens produce fewer coincidental matches
  return gone.sort((a, b) => b.length - a.length).slice(0, MAX_TOKENS);
}

function findRoot(start) {
  let d = start;
  for (let i = 0; i < 8; i++) {
    for (const mark of ROOT_MARKS) {
      try { if (fs.existsSync(path.join(d, mark))) return d; } catch (e) { /* keep going */ }
    }
    const up = path.dirname(d);
    if (up === d) break;
    d = up;
  }
  return start;
}

function listFiles(root) {
  const out = [];
  const walk = (d, depth) => {
    if (out.length >= MAX_FILES || depth > 6) return;
    let ents;
    try { ents = fs.readdirSync(d, { withFileTypes: true }); } catch (e) { return; }
    for (const e of ents) {
      if (out.length >= MAX_FILES) return;
      if (e.isDirectory()) {
        if (!SKIP_DIR.test(e.name) && !e.name.startsWith(".")) walk(path.join(d, e.name), depth + 1);
      } else if (SCAN_EXT.test(e.name)) out.push(path.join(d, e.name));
    }
  };
  walk(root, 0);
  return out;
}

/** Numbers may be written with separators; match 1648 and 1,648 alike. */
function patternFor(token) {
  if (/^\d+$/.test(token)) return new RegExp(token.split("").join("[,_]?"));
  return new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
}

function findHits(files, tokens) {
  const hits = [];
  for (const f of files) {
    let text;
    try {
      if (fs.statSync(f).size > MAX_BYTES) continue;
      text = fs.readFileSync(f, "utf8");
    } catch (e) { continue; }
    const lines = text.split("\n");
    for (const t of tokens) {
      const pat = patternFor(t);
      for (let i = 0; i < lines.length; i++) {
        if (!pat.test(lines[i])) continue;
        hits.push({ t, f, n: i + 1, line: lines[i].trim().slice(0, 90) });
        if (hits.length >= MAX_HITS) return hits;
      }
    }
  }
  return hits;
}

function buildMessage(hits, root, fileCount) {
  const byToken = new Map();
  for (const h of hits) {
    if (!byToken.has(h.t)) byToken.set(h.t, []);
    byToken.get(h.t).push(h);
  }
  let msg = "A value you just removed is still present elsewhere.\n\n";
  for (const [t, list] of byToken) {
    msg += '"' + t + '" — ' + list.length + " site(s)\n";
    for (const h of list) msg += "  " + path.relative(root, h.f) + ":" + h.n + "  " + h.line + "\n";
    msg += "\n";
  }
  msg += "Scanned " + fileCount + " file(s) under " + path.basename(root) +
    " (dependencies and build output excluded).\n\n" +
    "If these are the same concept, change them ALL in this turn.\n" +
    "If they mean something different, SAY SO and move on.\n" +
    "Doing neither is the failure this hook exists to catch: the last time it\n" +
    "happened, three live sites were reported as \"no traces left\".";
  return msg;
}

/* ── run ── */

let input = {};
try { input = JSON.parse(fs.readFileSync(0, "utf8") || "{}"); } catch (e) { quit(); }

const tool = String(input.tool_name || "");
if (tool !== "Edit" && tool !== "MultiEdit") quit();

const ti = input.tool_input || {};
const file = String(ti.file_path || "");
if (!file || !fs.existsSync(file)) quit();

try {
  const pairs = Array.isArray(ti.edits)
    ? ti.edits.map((e) => [e.old_string, e.new_string])
    : [[ti.old_string, ti.new_string]];

  const tokens = [];
  for (const [o, n] of pairs) {
    if (o == null) continue;
    for (const t of vanished(o, n == null ? "" : n)) if (!tokens.includes(t)) tokens.push(t);
  }
  if (!tokens.length) quit();

  const root = findRoot(path.dirname(file));
  const files = listFiles(root);
  const hits = findHits(files, tokens.slice(0, MAX_TOKENS));
  if (!hits.length) quit();

  tell(buildMessage(hits, root, files.length));
} catch (e) {
  quit();   // fail open, always
}
