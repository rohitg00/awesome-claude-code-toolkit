/**
 * NTXP Contacts — live, READ-ONLY Google Sheet mirror.
 *
 * The hosted app (contacts.ntxpllc.com) is the product; this Sheet mirrors its data for
 * people who want a spreadsheet. It pulls /api/contacts with the signed-in user's own
 * Google OAuth token. The server accepts only Google Workspace tokens whose hosted
 * domain is ntxpllc.com, and this script refuses to run for anyone else — so domain
 * OAuth is enforced on both sides. Edits belong in the app (the data range is protected).
 *
 * Pure helpers (buildQuery_, rowsFromApi_, safe_, isDomainEmail_) are unit-tested under
 * Node: see sheets/test/test_code.js.
 */
var CFG = {
  DOMAIN: 'ntxpllc.com',
  DEFAULT_API: 'https://contacts.ntxpllc.com',
  PAGE: 1000,                 // rows per API call (server cap is 5000)
  SHEET: 'Contacts',
  TITLE_ROW: 1, META_ROW: 2, HEADER_ROW: 3,
  REFRESH_MINUTES: 5,
  // NTXP-DOC-STANDARD 2.1 tokens
  NAVY: '#1B2A4E', NAVY_MID: '#46567D', WARM: '#F6F3EF', WARM_LINE: '#E2DAD0', LINK: '#2F529B', INK: '#1F2A3D'
};

// [header, api field, centred?]  — paragraph columns (Company, Labels) are left-aligned, per the standard.
var COLUMNS = [
  ['Name', 'full_name', true], ['Company / Entity', 'company', false], ['Title', 'title', false],
  ['Role', 'role', true], ['Trade', 'trade', true], ['City', 'city', true], ['State', 'state', true],
  ['Phone #', 'phone', true], ['Email', 'email', true], ['Labels', 'labels', false],
  ['LinkedIn', 'linkedin_url', true], ['Project', 'project', true], ['Grade', 'grade_band', true]
];

/* ---------------------------- pure helpers (tested) ---------------------------- */

function isDomainEmail_(email, domain) {
  email = String(email || '').toLowerCase(); domain = String(domain || CFG.DOMAIN).toLowerCase();
  var at = email.lastIndexOf('@');
  return at > 0 && email.substring(at + 1) === domain;
}

/** Neutralise spreadsheet-formula injection: contact data is untrusted. */
function safe_(v) {
  if (v === null || v === undefined) return '';
  var s = String(v);
  return /^[=+\-@\t\r]/.test(s) ? "'" + s : s;
}

function fmtPhone_(p) {
  var d = String(p || '').replace(/\D/g, '').replace(/^1(\d{10})$/, '$1');
  return d.length === 10 ? d.substring(0, 3) + '-' + d.substring(3, 6) + '-' + d.substring(6) : String(p || '');
}

/** filters: {q, project, role, trade, state, city, company, label, near, miles}; a value may be an array (OR). */
function buildQuery_(filters, extra) {
  var parts = [], f = filters || {};
  ['company', 'role', 'trade', 'city', 'state', 'project', 'label'].forEach(function (k) {
    var v = f[k]; if (v === undefined || v === null || v === '') return;
    (Array.isArray(v) ? v : [v]).forEach(function (x) { if (String(x).trim()) parts.push(k + '=' + encodeURIComponent(String(x).trim())); });
  });
  if (f.q) parts.push('q=' + encodeURIComponent(String(f.q).trim()));
  if (f.near && f.miles) { parts.push('near=' + encodeURIComponent(f.near)); parts.push('miles=' + encodeURIComponent(f.miles)); }
  for (var k in (extra || {})) parts.push(k + '=' + encodeURIComponent(extra[k]));
  return parts.join('&');
}

/** API rows -> 2D array of display values. Hyperlinks are validated before becoming formulas. */
function rowsFromApi_(apiRows) {
  return (apiRows || []).map(function (r) {
    return COLUMNS.map(function (c) {
      var k = c[1], v = r[k];
      if (k === 'labels') return safe_((v || []).join('; '));
      if (k === 'phone') {
        var ph = fmtPhone_(v); var tel = String(v || '').replace(/[^+\d]/g, '');
        return /^\+?\d{7,15}$/.test(tel) ? '=HYPERLINK("tel:' + tel + '","' + ph + '")' : safe_(ph);
      }
      if (k === 'email') {
        return /^[^\s@"<>]+@[^\s@"<>]+\.[^\s@"<>]+$/.test(v || '') ? '=HYPERLINK("mailto:' + v + '","' + v + '")' : safe_(v);
      }
      if (k === 'linkedin_url') {
        return /^https?:\/\/[^\s"<>]+$/i.test(v || '') ? '=HYPERLINK("' + v + '","LinkedIn")' : '';
      }
      return safe_(v);
    });
  });
}

/* ------------------------------ Apps Script glue ------------------------------ */

function onOpen() {
  SpreadsheetApp.getUi().createMenu('NTXP Contacts')
    .addItem('Refresh now', 'refreshNow')
    .addItem('Filters & reports…', 'showSidebar')
    .addSeparator()
    .addItem('Turn on live auto-refresh (every ' + CFG.REFRESH_MINUTES + ' min)', 'enableAutoRefresh')
    .addItem('Turn off auto-refresh', 'disableAutoRefresh')
    .addItem('Open the live app', 'openApp')
    .addToUi();
}

function apiBase_() { return PropertiesService.getScriptProperties().getProperty('NTXP_API') || CFG.DEFAULT_API; }

/** Domain gate. Triggers run as the trigger owner, UI actions as the active user: both must be @ntxpllc.com. */
function requireDomain_() {
  var eff = Session.getEffectiveUser().getEmail(), act = Session.getActiveUser().getEmail();
  if (!isDomainEmail_(eff) || (act && !isDomainEmail_(act))) {
    throw new Error('NTXP Contacts is limited to @' + CFG.DOMAIN + ' Google Workspace accounts.');
  }
}

function fetchJson_(path) {
  var res = UrlFetchApp.fetch(apiBase_() + path, {
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true
  });
  var code = res.getResponseCode();
  if (code === 401 || code === 403) throw new Error('The contacts service rejected your sign-in (HTTP ' + code + '). Use your @' + CFG.DOMAIN + ' account, then re-authorize via NTXP Contacts › Refresh now.');
  if (code >= 400) throw new Error('Contacts service error ' + code + ': ' + String(res.getContentText()).substring(0, 200));
  return JSON.parse(res.getContentText());
}

function getFilters_() {
  var raw = PropertiesService.getDocumentProperties().getProperty('FILTERS');
  return raw ? JSON.parse(raw) : {};
}
function setFilters_(f) { PropertiesService.getDocumentProperties().setProperty('FILTERS', JSON.stringify(f || {})); }

function refreshNow() { return refresh_(getFilters_()); }

function refresh_(filters) {
  requireDomain_();
  var all = [], total = null, offset = 0;
  do {
    var d = fetchJson_('/api/contacts?' + buildQuery_(filters, { limit: CFG.PAGE, offset: offset, sort: 'name' }));
    total = d.total; all = all.concat(d.rows); offset += CFG.PAGE;
  } while (offset < total && all.length < 50000);
  writeSheet_(rowsFromApi_(all), total, filters);
  return { total: total, written: all.length };
}

function writeSheet_(rows, total, filters) {
  var ss = SpreadsheetApp.getActiveSpreadsheet(), sh = ss.getSheetByName(CFG.SHEET) || ss.insertSheet(CFG.SHEET);
  var ncol = COLUMNS.length, first = CFG.HEADER_ROW + 1;
  sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).breakApart();   // a re-refresh must not collide with old merges
  sh.clear(); sh.clearConditionalFormatRules();
  (sh.getBandings() || []).forEach(function (b) { b.remove(); });
  var oldFilter = sh.getFilter(); if (oldFilter) oldFilter.remove();
  var existing = sh.getProtections(SpreadsheetApp.ProtectionType.RANGE); existing.forEach(function (p) { p.remove(); });

  // Title bar — navy, centred, bold caps (doc standard)
  sh.getRange(CFG.TITLE_ROW, 1, 1, ncol).merge().setValue('NTXP CONTACTS — LIVE MIRROR (READ-ONLY)')
    .setBackground(CFG.NAVY).setFontColor('#FFFFFF').setFontWeight('bold').setFontSize(13).setHorizontalAlignment('center').setVerticalAlignment('middle');
  sh.setRowHeight(CFG.TITLE_ROW, 34);
  var fdesc = describeFilters_(filters);
  sh.getRange(CFG.META_ROW, 1, 1, ncol).merge()
    .setValue(total + ' contacts' + (fdesc ? ' · filters: ' + fdesc : '') + ' · synced ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'MMM d, yyyy h:mm a') + ' · edit in the app (contacts.ntxpllc.com)')
    .setFontColor('#5A6880').setFontSize(9).setHorizontalAlignment('center');
  // Header row — navy-mid, bold, centred
  sh.getRange(CFG.HEADER_ROW, 1, 1, ncol).setValues([COLUMNS.map(function (c) { return c[0]; })])
    .setBackground(CFG.NAVY_MID).setFontColor('#FFFFFF').setFontWeight('bold').setHorizontalAlignment('center').setVerticalAlignment('middle');
  sh.setRowHeight(CFG.HEADER_ROW, 30);
  if (rows.length) {
    var body = sh.getRange(first, 1, rows.length, ncol);
    body.setValues(rows).setVerticalAlignment('top').setFontColor(CFG.INK).setFontFamily('Open Sans').setFontSize(10).setBorder(null, null, null, null, null, true, CFG.WARM_LINE, SpreadsheetApp.BorderStyle.SOLID);
    COLUMNS.forEach(function (c, i) { sh.getRange(first, i + 1, rows.length, 1).setHorizontalAlignment(c[2] ? 'center' : 'left'); });
    [ 'email', 'phone', 'linkedin_url' ].forEach(function (k) {   // links in NTXP link ink
      var i = COLUMNS.map(function (c) { return c[1]; }).indexOf(k) + 1; sh.getRange(first, i, rows.length, 1).setFontColor(CFG.LINK);
    });
    // Two-tone rows: row A paper, row B warm #F6F3EF
    sh.getRange(first, 1, rows.length, ncol).applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, false, false)
      .setFirstRowColor('#FFFFFF').setSecondRowColor(CFG.WARM);
    sh.getRange(CFG.HEADER_ROW, 1, rows.length + 1, ncol).createFilter();   // native column filters
  }
  var widths = [170, 200, 150, 90, 100, 100, 55, 110, 230, 220, 80, 130, 55];
  widths.forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
  sh.setFrozenRows(CFG.HEADER_ROW); sh.setFrozenColumns(1);
  // One-way mirror: warn on any manual edit of the data
  sh.getRange(1, 1, Math.max(rows.length + CFG.HEADER_ROW, CFG.HEADER_ROW), ncol).protect()
    .setDescription('Read-only mirror — edit contacts in the NTXP Contacts app').setWarningOnly(true);
}

function describeFilters_(f) {
  var out = []; f = f || {};
  ['q', 'company', 'role', 'trade', 'city', 'state', 'project', 'label'].forEach(function (k) { if (f[k] && String(f[k]).length) out.push(k + '=' + (Array.isArray(f[k]) ? f[k].join('|') : f[k])); });
  if (f.near && f.miles) out.push(f.miles + ' mi of ' + f.near);
  return out.join(', ');
}

/* ------------------------------ live auto-refresh ------------------------------ */

function enableAutoRefresh() {
  requireDomain_(); disableAutoRefresh();
  ScriptApp.newTrigger('refreshNow').timeBased().everyMinutes(CFG.REFRESH_MINUTES).create();
  SpreadsheetApp.getActive().toast('Live auto-refresh is on (every ' + CFG.REFRESH_MINUTES + ' min).', 'NTXP Contacts', 5);
}
function disableAutoRefresh() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'refreshNow') ScriptApp.deleteTrigger(t); });
}

/* ------------------------------ sidebar: filters + reports ------------------------------ */

function showSidebar() {
  SpreadsheetApp.getUi().showSidebar(HtmlService.createHtmlOutputFromFile('Sidebar').setTitle('NTXP Contacts'));
}
function sidebarState() { return { filters: getFilters_(), api: apiBase_() }; }
function sidebarApply(filters) { setFilters_(filters); return refresh_(filters); }

/**
 * Render a report with the NTXP document engine on the server and save the PDF to Drive:
 * the project's folder under "!Active Projects" when a project filter is set, else "NTXP Reports".
 */
function sidebarExport(type, orientation, filters, toProject) {
  requireDomain_();
  var q = buildQuery_(filters, { type: type, orientation: orientation || 'portrait', format: 'pdf' });
  var res = UrlFetchApp.fetch(apiBase_() + '/api/report/render?' + q, { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) throw new Error('Report failed (' + res.getResponseCode() + '): ' + String(res.getContentText()).substring(0, 200));
  var name = 'NTXP_' + type + '_' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd') + '.pdf';
  var blob = res.getBlob().setName(name), folder = null, where = '';
  var proj = filters && (Array.isArray(filters.project) ? filters.project[0] : filters.project);
  if (toProject && proj) {
    folder = findProjectFolder_(proj);
    if (!folder) throw new Error("No folder matching '" + proj + "' under !Active Projects in your Drive.");
    where = '!Active Projects / ' + folder.getName();
  } else {
    var it = DriveApp.getFoldersByName('NTXP Reports'); folder = it.hasNext() ? it.next() : DriveApp.createFolder('NTXP Reports'); where = 'NTXP Reports';
  }
  var file = folder.createFile(blob);
  return { url: file.getUrl(), where: where, name: name };
}

function findProjectFolder_(project) {
  var roots = DriveApp.getFoldersByName('!Active Projects');
  while (roots.hasNext()) {
    var root = roots.next(), exact = root.getFoldersByName(project);
    if (exact.hasNext()) return exact.next();
    var esc = String(project).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    var like = root.searchFolders("title contains '" + esc + "'");
    if (like.hasNext()) return like.next();
  }
  return null;
}

function openApp() {
  var html = HtmlService.createHtmlOutput('<script>window.open(' + JSON.stringify(apiBase_()) + ',"_blank");google.script.host.close();</script>');
  SpreadsheetApp.getUi().showModalDialog(html, 'Opening NTXP Contacts…');
}
