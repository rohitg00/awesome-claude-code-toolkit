#!/usr/bin/env node
'use strict';
// SessionEnd hook. Reads the hook JSON on stdin, archives the session to the
// Obsidian vault. Silent-fails so it never blocks Claude Code from exiting.

const { archiveSession } = require('./lib/archive');

const stripBom = (s) => (s && s.charCodeAt(0) === 0xfeff ? s.slice(1) : s);

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (d) => (raw += d));
process.stdin.on('end', () => {
  let hook = {};
  try { hook = JSON.parse(stripBom(raw) || '{}'); } catch { /* ignore */ }
  const r = archiveSession(hook);
  if (r.status === 'written') {
    process.stdout.write(JSON.stringify({ systemMessage: `📓 Session archived to Obsidian (${r.turns} msgs)` }));
  }
  process.exit(0);
});
process.stdin.on('error', () => process.exit(0));
