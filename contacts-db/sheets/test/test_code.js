// Unit tests for the Apps Script mirror, run under Node with stubbed Google services.
//   node sheets/test/test_code.js
// These verify OUR logic (query building, injection safety, domain gate, paging, Drive routing).
// They do not exercise Google's runtime — that needs a real Workspace account (see sheets/README.md).
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const src = fs.readFileSync(__dirname + '/../Code.gs', 'utf8');

function makeCtx(opts = {}) {
  const calls = { fetch: [], written: null, files: [], triggers: [] };
  const eff = opts.eff || 't@ntxpllc.com', act = opts.act === undefined ? 't@ntxpllc.com' : opts.act;
  const pages = opts.pages || [];
  const ctx = {
    console, JSON, encodeURIComponent, Math, Date, String, Array, RegExp, Error,
    Session: { getEffectiveUser: () => ({ getEmail: () => eff }), getActiveUser: () => ({ getEmail: () => act }), getScriptTimeZone: () => 'America/Chicago' },
    ScriptApp: { getOAuthToken: () => 'TOKEN123', getProjectTriggers: () => [], deleteTrigger() {},
      newTrigger: (fn) => ({ timeBased: () => ({ everyMinutes: (m) => ({ create: () => calls.triggers.push([fn, m]) }) }) }) },
    PropertiesService: { getScriptProperties: () => ({ getProperty: () => null }),
      getDocumentProperties: () => ({ getProperty: () => null, setProperty() {} }) },
    Utilities: { formatDate: () => 'Oct 29, 2026 1:00 PM' },
    UrlFetchApp: { fetch: (url, o) => {
      calls.fetch.push({ url, auth: o.headers.Authorization });
      const m = url.match(/offset=(\d+)/); const i = m ? Math.floor(+m[1] / 1000) : 0;
      if (opts.status) return { getResponseCode: () => opts.status, getContentText: () => 'nope', getBlob: () => ({ setName: (n) => ({ n }) }) };
      return { getResponseCode: () => 200, getContentText: () => JSON.stringify(pages[i] || { total: 0, rows: [] }), getBlob: () => ({ setName: (n) => ({ name: n }) }) };
    } },
    DriveApp: { getFoldersByName: (n) => { const f = (opts.folders || {})[n]; let i = 0; return { hasNext: () => !!f && i < f.length, next: () => f[i++] }; },
      createFolder: (n) => ({ getName: () => n, createFile: (b) => (calls.files.push(['created:' + n, b]), { getUrl: () => 'https://drive/x' }) }) },
    SpreadsheetApp: { getUi: () => ({}), ProtectionType: { RANGE: 'RANGE' }, BandingTheme: { LIGHT_GREY: 'G' }, BorderStyle: { SOLID: 'S' },
      getActiveSpreadsheet: () => { const mk = () => { const r = new Proxy(function () {}, { get: (t, k) => k === 'setValues' ? (v) => (calls.written = calls.written || [], (v.length > 1 || (v[0] && v[0].length > 3)) && calls.written.push(v), r) : (...a) => r, apply: () => r }); return r; };
        const sh = new Proxy({}, { get: (t, k) => k === 'getRange' ? mk : k === 'getBandings' ? () => [] : k === 'getFilter' ? () => null : k === 'getProtections' ? () => [] : k === 'getMaxRows' ? () => 100 : k === 'getMaxColumns' ? () => 13 : () => sh });
        return { getSheetByName: () => sh, insertSheet: () => sh }; } },
  };
  vm.createContext(ctx); vm.runInContext(src, ctx);
  return { ctx, calls };
}
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok  ' + name); };

t('domain check is exact (no look-alikes, no subdomain tricks)', () => {
  const { ctx } = makeCtx();
  assert(ctx.isDomainEmail_('a@ntxpllc.com')); assert(ctx.isDomainEmail_('A@NTXPLLC.COM'));
  for (const bad of ['a@gmail.com', 'a@ntxpllc.com.evil.io', 'a@evilntxpllc.com', 'a@x.ntxpllc.com', '@ntxpllc.com', '', null])
    assert(!ctx.isDomainEmail_(bad), bad);
});
t('requireDomain_ blocks outside accounts (owner and active user)', () => {
  assert.throws(() => makeCtx({ eff: 'x@gmail.com' }).ctx.requireDomain_(), /limited to @ntxpllc.com/);
  assert.throws(() => makeCtx({ act: 'x@gmail.com' }).ctx.requireDomain_(), /limited to @ntxpllc.com/);
  makeCtx().ctx.requireDomain_();
});
t('safe_ neutralises formula injection', () => {
  const { ctx } = makeCtx();
  for (const v of ['=1+1', '+SUM(A1)', '-2', '@cmd', '\t=x']) assert(ctx.safe_(v).startsWith("'"), v);
  assert.strictEqual(ctx.safe_('Eric'), 'Eric'); assert.strictEqual(ctx.safe_(null), '');
});
t('buildQuery_: repeated keys = OR, proximity needs both, values encoded', () => {
  const { ctx } = makeCtx();
  assert.strictEqual(ctx.buildQuery_({ role: ['Sub', 'Owner'], q: 'a b&c', near: 'Dallas, TX', miles: '30', state: 'TX' }, { limit: 5 }),
    'role=Sub&role=Owner&state=TX&q=a%20b%26c&near=Dallas%2C%20TX&miles=30&limit=5');
  assert.strictEqual(ctx.buildQuery_({ near: 'Dallas, TX' }), '');            // miles missing -> no proximity
  assert.strictEqual(ctx.buildQuery_({}), '');
});
t('rowsFromApi_ maps columns, builds only validated links, blocks injection', () => {
  const { ctx } = makeCtx();
  const [r] = ctx.rowsFromApi_([{ full_name: 'Eric Vaden', company: 'Vaden', title: null, role: 'Sub', trade: 'Drywall', city: 'Dallas', state: 'TX',
    phone: '+18178478822', email: 'eric@vaden.com', labels: ['DBE', 'RHCA'], linkedin_url: 'https://linkedin.com/in/x', project: 'Spruce', grade_band: 'A' }]);
  assert.strictEqual(r.length, 13);
  assert.strictEqual(r[0], 'Eric Vaden'); assert.strictEqual(r[9], 'DBE; RHCA');
  assert.strictEqual(r[7], '=HYPERLINK("tel:+18178478822","817-847-8822")');
  assert.strictEqual(r[8], '=HYPERLINK("mailto:eric@vaden.com","eric@vaden.com")');
  assert.strictEqual(r[10], '=HYPERLINK("https://linkedin.com/in/x","LinkedIn")');
  const [x] = ctx.rowsFromApi_([{ full_name: '=HYPERLINK("http://evil")', email: 'a"b@x.com', phone: '12', linkedin_url: 'javascript:alert(1)', labels: ['=1'] }]);
  assert(x[0].startsWith("'=")); assert(!x[8].startsWith('=HYPERLINK')); assert(!x[10]); assert(x[9].startsWith("'="));
});
t('refresh_ pages through the API with the user OAuth token and writes everything', () => {
  const row = (i) => ({ full_name: 'P' + i, email: 'p' + i + '@x.com', labels: [] });
  const pages = [{ total: 2300, rows: Array.from({ length: 1000 }, (_, i) => row(i)) }, { total: 2300, rows: Array.from({ length: 1000 }, (_, i) => row(1000 + i)) }, { total: 2300, rows: Array.from({ length: 300 }, (_, i) => row(2000 + i)) }];
  const { ctx, calls } = makeCtx({ pages });
  const out = ctx.refresh_({ project: 'Spruce HS' });
  assert.strictEqual(out.total, 2300); assert.strictEqual(out.written, 2300);
  assert.strictEqual(calls.fetch.length, 3);
  assert.deepStrictEqual(calls.fetch.map(c => +c.url.match(/offset=(\d+)/)[1]), [0, 1000, 2000]);
  assert(calls.fetch.every(c => c.auth === 'Bearer TOKEN123' && c.url.startsWith('https://contacts.ntxpllc.cloud/api/contacts?') && c.url.includes('project=Spruce%20HS')));
  assert.strictEqual(calls.written.reduce((a, v) => a + v.length, 0) >= 2300, true);
});
t('401/403 give a sign-in message; server errors surface', () => {
  assert.throws(() => makeCtx({ status: 401 }).ctx.refresh_({}), /rejected your sign-in/);
  assert.throws(() => makeCtx({ status: 403 }).ctx.refresh_({}), /@ntxpllc.com/);
  assert.throws(() => makeCtx({ status: 500 }).ctx.refresh_({}), /error 500/);
});
t('outside-domain user never reaches the network', () => {
  const { ctx, calls } = makeCtx({ eff: 'x@gmail.com' });
  assert.throws(() => ctx.refresh_({}), /limited to/); assert.strictEqual(calls.fetch.length, 0);
});
t('sidebarExport routes the PDF to the project folder under !Active Projects', () => {
  const made = [];
  const proj = { getName: () => 'Spruce HS', createFile: (b) => (made.push(b), { getUrl: () => 'https://drive/f' }) };
  const root = { getFoldersByName: (n) => ({ hasNext: () => n === 'Spruce HS', next: () => proj }), searchFolders: () => ({ hasNext: () => false }) };
  const { ctx, calls } = makeCtx({ folders: { '!Active Projects': [root] } });
  const r = ctx.sidebarExport('directory', 'portrait', { project: 'Spruce HS' }, true);
  assert.strictEqual(r.where, '!Active Projects / Spruce HS'); assert.strictEqual(made.length, 1);
  assert(calls.fetch[0].url.includes('/api/report/render?') && calls.fetch[0].url.includes('type=directory') && calls.fetch[0].url.includes('format=pdf'));
});
t('sidebarExport: missing project folder is an error; no project -> NTXP Reports', () => {
  const root = { getFoldersByName: () => ({ hasNext: () => false }), searchFolders: () => ({ hasNext: () => false }) };
  assert.throws(() => makeCtx({ folders: { '!Active Projects': [root] } }).ctx.sidebarExport('full', 'portrait', { project: 'Nope' }, true), /No folder matching 'Nope'/);
  const { ctx, calls } = makeCtx();
  assert.strictEqual(ctx.sidebarExport('full', 'landscape', {}, true).where, 'NTXP Reports'); assert.strictEqual(calls.files.length, 1);
});
t('auto-refresh installs one time trigger at the configured interval', () => {
  const { ctx, calls } = makeCtx(); ctx.SpreadsheetApp.getActive = () => ({ toast() {} });
  ctx.enableAutoRefresh(); assert.deepStrictEqual(calls.triggers, [['refreshNow', 5]]);
});
console.log('\n' + n + ' Apps Script tests passed');
