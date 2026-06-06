'use strict';
// Parse a Claude Code transcript (.jsonl) into clean conversational turns,
// and redact obvious secrets before anything is written to disk.

const fs = require('fs');

/** Redact common secret formats so they never land in a Markdown note. */
function redactSecrets(s) {
  if (!s) return s;
  return s
    .replace(/-----BEGIN[^-]*PRIVATE KEY-----[\s\S]*?-----END[^-]*PRIVATE KEY-----/gi, '[REDACTED PRIVATE KEY]')
    .replace(/\b(sk|rk)-[A-Za-z0-9]{20,}/gi, '[REDACTED]')
    .replace(/\bAKIA[0-9A-Z]{16}\b/g, '[REDACTED]')
    .replace(/\bgh[pousr]_[A-Za-z0-9]{20,}/g, '[REDACTED]')
    .replace(/\bxox[baprs]-[A-Za-z0-9-]{10,}/g, '[REDACTED]')
    .replace(/\bAIza[0-9A-Za-z_-]{20,}/g, '[REDACTED]')
    .replace(/\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{6,}/g, '[REDACTED JWT]')
    .replace(/\b(authorization\s*[:=]\s*)(?:bearer|basic|token|digest)\s+\S+/gi, '$1[REDACTED]')
    .replace(/\bbearer\s+[A-Za-z0-9._~+/-]{6,}=*/gi, 'Bearer [REDACTED]')
    .replace(/\b(api[_-]?key|secret|token|password|passwd|pwd|client[_-]?secret|authorization|bearer)\b\s*[:=]\s*["']?[^\s"']+/gi, '$1: [REDACTED]');
}

/**
 * Parse a transcript JSONL file into a normalized shape.
 * Returns { turns: [{role:'user'|'assistant', text}], toolCount, firstTs, firstCwd }.
 * Best-effort: malformed lines are skipped, subagent/meta lines ignored.
 */
function parseTranscript(transcriptPath) {
  const out = { turns: [], toolCount: 0, firstTs: null, firstCwd: null };
  let raw;
  try {
    raw = fs.readFileSync(transcriptPath, 'utf8');
  } catch {
    return out;
  }

  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    let o;
    try {
      o = JSON.parse(trimmed);
    } catch {
      continue;
    }
    if (o.isSidechain === true || o.isMeta === true) continue;
    const type = o.type;
    if (type !== 'user' && type !== 'assistant') continue;
    const msg = o.message;
    if (!msg) continue;
    if (!out.firstTs && o.timestamp) out.firstTs = o.timestamp;
    if (!out.firstCwd && o.cwd) out.firstCwd = o.cwd;

    const content = msg.content;
    const parts = [];
    let hasText = false;
    let hasToolResult = false;

    if (typeof content === 'string') {
      if (content.trim()) {
        parts.push(content);
        hasText = true;
      }
    } else if (Array.isArray(content)) {
      for (const b of content) {
        switch (b && b.type) {
          case 'text':
            if (b.text) { parts.push(b.text); hasText = true; }
            break;
          case 'tool_use':
            parts.push('`[tool: ' + (b.name || 'unknown') + ']`');
            out.toolCount++;
            break;
          case 'tool_result':
            hasToolResult = true;
            break;
          default:
            break;
        }
      }
    }

    if (!hasText && hasToolResult) continue; // pure tool-result echo
    if (parts.length === 0) continue;

    out.turns.push({ role: type, text: redactSecrets(parts.join('\n')) });
  }

  return out;
}

module.exports = { redactSecrets, parseTranscript };
