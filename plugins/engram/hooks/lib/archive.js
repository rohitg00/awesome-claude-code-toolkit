'use strict';
// Turn one Claude Code session into a Markdown note + a daily-index line.
// Pure-ish: give it the hook input, it writes into the vault. Never throws
// (errors are logged to the vault error log and swallowed).

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { parseTranscript } = require('./transcript');
const { vaultPaths } = require('./paths');

const pad = (n) => String(n).padStart(2, '0');

function stamp(d) {
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
  };
}

function makeAlias(firstUser) {
  let a = (firstUser || '(no user prompt captured)').replace(/\s+/g, ' ').trim();
  a = a.replace(/[[\]|#^]/g, '');
  if (a.length > 80) a = a.slice(0, 80) + '…';
  return a;
}

function ensureDir(d) {
  fs.mkdirSync(d, { recursive: true });
}

/**
 * @param {{transcript_path?:string, session_id?:string, cwd?:string, reason?:string}} hook
 * @param {object} [opts] { vault }
 * @returns {{status:'written'|'skipped'|'error', note?:string, turns?:number}}
 */
function archiveSession(hook, opts = {}) {
  const P = vaultPaths(opts.vault);
  try {
    const tp = hook.transcript_path;
    const sid = hook.session_id || 'unknown';
    let cwd = hook.cwd || '';
    const reason = hook.reason || '';

    // Real session id → stable, idempotent short. No id → hash the transcript
    // path so each session still gets a unique, collision-free, stable name.
    let short = sid.replace(/[^a-zA-Z0-9]/g, '').slice(0, 8);
    if (!short || sid === 'unknown') {
      short = crypto.createHash('sha1').update(String(tp || 'engram')).digest('hex').slice(0, 8);
    }

    const { turns, toolCount, firstTs, firstCwd } = tp
      ? parseTranscript(tp)
      : { turns: [], toolCount: 0, firstTs: null, firstCwd: null };

    if (!cwd) cwd = firstCwd || '';
    if (turns.length < 2 && toolCount === 0) return { status: 'skipped' };

    let dt = firstTs ? new Date(firstTs) : new Date();
    if (isNaN(dt.getTime())) dt = new Date();
    const { date, time } = stamp(dt);

    const firstUser = (turns.find((t) => t.role === 'user') || {}).text;
    const alias = makeAlias(firstUser);
    const project = cwd ? path.basename(cwd) : 'unknown';
    const noteName = `${date}_${short}`;

    const fm = [
      '---',
      `date: ${date}`,
      `time: "${time}"`,
      `session: ${short}`,
      `project: ${project}`,
      `cwd: ${cwd}`,
      `messages: ${turns.length}`,
      `tools_used: ${toolCount}`,
      `end_reason: ${reason}`,
      'source: claude-code',
      'tags: [claude-session]',
      '---',
      '',
      `# ${date} ${time} — ${alias}`,
      '',
      `Project: **${project}** · [[Daily/${date}]] · ${turns.length} messages · ${toolCount} tool calls`,
      '',
    ];

    const body = turns
      .map((t) => `${t.role === 'user' ? '## 🧑 User' : '## 🤖 Claude'}\n\n${t.text}\n`)
      .join('\n');

    ensureDir(P.sessions);
    fs.writeFileSync(path.join(P.sessions, `${noteName}.md`), fm.join('\n') + body, 'utf8');

    // daily index — atomic header create + dedup + append.
    // Append (not rewrite) so concurrent SessionEnd hooks can't clobber each
    // other's lines; the dedup read keeps it idempotent on re-runs.
    ensureDir(P.daily);
    const dailyPath = path.join(P.daily, `${date}.md`);
    try { fs.writeFileSync(dailyPath, `# ${date}\n\n## Claude Code sessions\n\n`, { flag: 'wx' }); } catch { /* already exists */ }
    let existing = '';
    try { existing = fs.readFileSync(dailyPath, 'utf8'); } catch { /* ignore */ }
    if (!existing.includes(noteName)) {
      fs.appendFileSync(dailyPath, `- ${time} — [[Sessions/${noteName}|${alias}]] (${turns.length} msgs, ${toolCount} tools)\n`, 'utf8');
    }

    return { status: 'written', note: `${noteName}.md`, turns: turns.length };
  } catch (e) {
    try {
      ensureDir(P.vault);
      fs.appendFileSync(P.errorLog, `${new Date().toISOString()}  ${e && e.message}\n`, 'utf8');
    } catch { /* ignore */ }
    return { status: 'error' };
  }
}

module.exports = { archiveSession };
