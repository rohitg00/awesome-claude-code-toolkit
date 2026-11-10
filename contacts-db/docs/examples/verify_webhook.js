// Reference receiver-side verification for NTXP Contacts webhooks (Node >= 18, no dependencies).
//   const { verify, sign } = require('./verify_webhook');
//   app.post('/hooks/ntxp-contacts', express.raw({ type: '*/*' }), (req, res) => {   // RAW body, not parsed JSON
//     if (!verify(process.env.NTXP_CONTACTS_SECRET, req.body, req.get('X-NTXP-Signature'))) return res.sendStatus(401);
//     const event = JSON.parse(req.body);        // { id, type, data }
//     ...handle idempotently by event.id...
//     res.sendStatus(204);                       // reply 2xx fast; 4xx = "never retry", 5xx/timeout = retry with backoff
//   });
// The same scheme signs what YOU send to /api/v1/hooks/in/<peer>: sign(secret, bodyBuffer) -> header value.
const crypto = require('crypto');
const TOLERANCE_S = 300;

function sign(secret, body, ts = Math.floor(Date.now() / 1000)) {
  const mac = crypto.createHmac('sha256', secret).update(`${ts}.`).update(body).digest('hex');
  return `t=${ts},v1=${mac}`;
}

function verify(secret, body, header, now = Date.now() / 1000) {
  if (!header) return false;
  const parts = Object.fromEntries(header.split(',').map((p) => p.split(/=(.*)/s).slice(0, 2)));
  const ts = Number(parts.t);
  if (!Number.isFinite(ts) || !parts.v1 || Math.abs(now - ts) > TOLERANCE_S) return false;
  const want = crypto.createHmac('sha256', secret).update(`${ts}.`).update(body).digest();
  let got;
  try { got = Buffer.from(parts.v1, 'hex'); } catch { return false; }
  return got.length === want.length && crypto.timingSafeEqual(got, want);
}

module.exports = { sign, verify };
