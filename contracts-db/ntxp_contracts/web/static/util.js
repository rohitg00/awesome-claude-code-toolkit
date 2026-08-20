// Shared helpers for the dashboard and profile screens. Loaded before both
// page scripts (like brand.js). Keeping the security-sensitive primitives
// (esc, safeUrl) in ONE place means a hardening fix can never land in one
// screen and be forgotten in the other.

// HTML-escape for interpolation into innerHTML.
const esc = s => (s ?? '').toString().replace(/[&<>"]/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// Only allow safe link schemes — blocks javascript:/data: URLs in stored fields.
const safeUrl = u => /^(https?:|mailto:|tel:|sms:)/i.test((u || '').trim()) ? u : '';

// Currency, no cents. `blank` is what an empty/None value renders as.
const money = (v, blank = '—') => v == null || v === '' ? blank :
  '$' + Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });

// Whole days from today until an ISO date (negative = past); null if unparseable.
function daysUntil(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr + 'T00:00:00');
  if (isNaN(d)) return null;
  return Math.round((d - new Date(new Date().toDateString())) / 86400000);
}
