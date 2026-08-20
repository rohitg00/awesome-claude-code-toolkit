// NTXP Contract Profile — a clean, responsive single-contract screen.
// Profiles the contract + its owner entity (website, customer-service and
// accounting lines with click-to-call/text and a downloadable contact file),
// and rolls up the jobs done under it with total sales.

const id = new URLSearchParams(location.search).get('id');
const contentEl = document.getElementById('content');

// esc / safeUrl / money / daysUntil come from util.js (loaded first).
const fmtDate = s => s ? new Date(s + 'T00:00:00').toLocaleDateString(undefined,
  { year: 'numeric', month: 'short', day: 'numeric' }) : '—';
// pretty-print +1XXXXXXXXXX for display; keep raw for tel:/sms:
const prettyTel = t => {
  if (!t) return '';
  const d = t.replace(/\D/g, '').replace(/^1/, '');
  return d.length === 10 ? `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}` : t;
};

function kv(k, v) { return `<div class="kv"><span class="k">${esc(k)}</span><span class="v">${v}</span></div>`; }

function contactRow(label, phone) {
  if (!phone) return '';
  const tel = phone.replace(/[^\d+]/g, '');
  return `<div class="contact-row">
    <span><strong>${esc(label)}</strong><br><span class="muted">${esc(prettyTel(phone))}</span></span>
    <span class="contact-actions">
      <a class="chip call" href="tel:${esc(tel)}">📞 Call</a>
      <a class="chip text" href="sms:${esc(tel)}">💬 Text</a>
    </span></div>`;
}

function daysBadge(exp) {
  const d = daysUntil(exp);
  if (d == null) return '';
  if (d < 0) return `<span class="badge bad">Expired ${-d} days ago</span>`;
  if (d <= 90) return `<span class="badge bad">Expires in ${d} days</span>`;
  return `<span class="badge">Expires in ${d} days</span>`;
}

async function load() {
  if (!id) { contentEl.innerHTML = '<p class="muted">No contract id.</p>'; return; }
  let p;
  try { p = await (await fetch('/api/contracts/' + id)).json(); }
  catch (e) { contentEl.innerHTML = '<p class="muted">Could not load.</p>'; return; }
  if (p.error) { contentEl.innerHTML = '<p class="muted">Contract not found.</p>'; return; }

  const c = p.contract, o = p.owner || {}, t = p.totals || {};
  document.title = `NTXP — ${c.contract_title || 'Contract'}`;

  const ownerName = o.name || c.owner_entity;
  const website = o.website;

  const jobsRows = (p.jobs || []).map(j => `<tr>
      <td>${esc(j.name)}</td>
      <td>${esc(j.customer || '')}</td>
      <td>${esc(j.status || '')}</td>
      <td style="text-align:right">${money(j.contract_value)}</td>
      <td style="text-align:right">${money(j.sales_amount)}</td>
    </tr>`).join('');

  contentEl.innerHTML = `
    <div class="crumbs no-print"><a href="/">← Master Contracts</a></div>

    <div class="hero">
      <div class="eyebrow">${esc(c.contract_type || 'Contract')}</div>
      <h1>${esc(c.contract_title || 'Untitled')}</h1>
      <div class="cono-big">Contract / RFP # <strong>${esc(c.contract_no || '—')}</strong>
        &nbsp;·&nbsp; Recipient: <strong>${esc(c.recipient || 'NTXP LLC')}</strong></div>
      <div class="badges">
        <span class="badge ${c.is_executed ? 'ok' : 'bad'}">
          ${c.is_executed ? '✓ Executed' : '⚠ Unexecuted'}</span>
        ${daysBadge(c.expiration_date)}
        ${safeUrl(c.pdf_url) ? `<a class="badge" href="${esc(safeUrl(c.pdf_url))}" target="_blank" rel="noopener">📄 Signed copy</a>` : ''}
        <a class="badge no-print" href="/api/contracts/${id}/ics">📅 Add expiration to calendar</a>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Contract terms</h3>
        ${kv('Type', esc(c.contract_type || '—'))}
        ${kv('Owner entity', esc(ownerName || '—'))}
        ${kv('Location', esc(c.location || '—'))}
        ${kv('Estimated budget', money(c.estimated_budget))}
        ${kv('Coefficient multiplier', esc(c.coefficient_multiplier ?? '—'))}
        ${kv('Cooperative fee', esc(c.cooperative_fee || '—'))}
        ${kv('Allowable scope', esc(c.allowable_scope || '—'))}
      </div>
      <div class="card">
        <h3>Lifecycle</h3>
        ${kv('Award date', fmtDate(c.award_date))}
        ${kv('Duration', esc(c.duration || '—'))}
        ${kv('Expiration date', fmtDate(c.expiration_date))}
        ${kv('Status', c.is_executed ? 'Executed' : 'Unexecuted')}
        ${c.notes ? `<div style="margin-top:10px"><span class="k muted">Notes</span><br>${esc(c.notes)}</div>` : ''}
      </div>
      <div class="card">
        <h3>Performance under this contract</h3>
        <div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:6px">
          <div><div class="stat accent">${money(t.total_sales)}</div><div class="muted">total sales</div></div>
          <div><div class="stat">${t.job_count || 0}</div><div class="muted">jobs</div></div>
        </div>
        ${kv('Total contract value (jobs)', money(t.total_contract_value))}
      </div>
    </div>

    <div class="card" style="margin-bottom:18px">
      <h3>Owner entity — ${esc(ownerName || 'contact')}</h3>
      ${safeUrl(website) ? `<div class="kv"><span class="k">Website</span>
        <span class="v"><a href="${esc(safeUrl(website))}" target="_blank" rel="noopener">${esc(website.replace(/^https?:\/\//, ''))}</a></span></div>` : ''}
      ${o.email ? `<div class="kv"><span class="k">Email</span>
        <span class="v"><a href="mailto:${esc(o.email)}">${esc(o.email)}</a></span></div>` : ''}
      ${o.address ? kv('Address', esc(o.address)) : ''}
      <div style="margin-top:10px">
        ${contactRow('Main line', o.main_phone)}
        ${contactRow('Customer service', o.customer_service_phone)}
        ${contactRow('Accounting', o.accounting_phone)}
      </div>
      ${(o.main_phone || o.customer_service_phone || o.accounting_phone || o.email)
      ? `<div style="margin-top:14px" class="no-print">
            <a class="chip" href="/api/contracts/${id}/vcard">⬇ Download contact file (.vcf)</a>
         </div>`
      : '<p class="muted">No owner-entity contact info on file yet. Add a website and phone lines so this profile can offer click-to-call, text, and a downloadable contact card.</p>'}
    </div>

    <div class="card">
      <h3>Jobs done under this contract</h3>
      ${(p.jobs || []).length ? `<table class="jobs-table">
        <thead><tr><th>Job</th><th>Customer</th><th>Status</th>
          <th style="text-align:right">Contract value</th><th style="text-align:right">Sales</th></tr></thead>
        <tbody>${jobsRows}</tbody>
        <tfoot><tr><td colspan="3">Total</td>
          <td style="text-align:right">${money(t.total_contract_value)}</td>
          <td style="text-align:right">${money(t.total_sales)}</td></tr></tfoot>
      </table>`
      : '<p class="muted">No jobs synced yet. Jobs flow in from JobTread via the jobs sync (see the README) and roll up here automatically.</p>'}
    </div>`;
}

document.getElementById('printBtn').addEventListener('click', () => window.print());
document.getElementById('pdfBtn').addEventListener('click', () => window.print());
load();
