import { useCallback, useEffect, useRef, useState } from "react";
import { CFG } from "./lib/config";
import { api, apiJson, currentUser, driveToken, onGate, signIn, signOut } from "./lib/auth";
import { buildQuery, emptyFilters } from "./lib/model";
import { download, stamp, store } from "./lib/format";
import { Header, Toast } from "./components/ui/Chrome";
import { FilterRail } from "./components/FilterRail";
import { Toolbar } from "./components/Toolbar";
import { ContactsTable } from "./components/ContactsTable";
import { ReportsDrawer, SettingsPanel } from "./components/Panels";
import { ReportView } from "./components/ReportView";
import { ExportRail, Gate } from "./components/Gate";

const SIZE = 100;

function wipeSpec(spec) {
  const s0 = (spec.sections || []).find((s) => s.columns);
  if (!s0) throw new Error("No table section found in that spec.");
  return { name: spec.doc_title || "Custom report", doc_title: spec.doc_title || "Custom Report", columns: s0.columns.slice(), widths: (s0.widths || []).slice() };
}

export default function App() {
  const [gate, setGate] = useState(CFG.dev ? null : "");
  const [started, setStarted] = useState(false);
  const [f, setF] = useState(emptyFilters);
  const [q, setQ] = useState(""); const [near, setNear] = useState(""); const [miles, setMiles] = useState("");
  const [sort, setSort] = useState("name"); const [dir, setDir] = useState("asc"); const [page, setPage] = useState(0);
  const [rows, setRows] = useState([]); const [total, setTotal] = useState(0); const [error, setError] = useState("");
  const [view, setView] = useState(() => store.get("ntxp.view", 1));
  const [railOpen, setRailOpen] = useState(() => !matchMedia("(max-width:900px)").matches);
  const [drawer, setDrawer] = useState(false); const [panel, setPanel] = useState(false);
  const [orient, setOrient] = useState("portrait");
  const [report, setReport] = useState(null); const [busy, setBusy] = useState("");
  const [toastMsg, setToast] = useState(null);
  const [live, setLive] = useState("");
  const [tick, setTick] = useState(0);
  const [templates, setTemplates] = useState(() => store.get("ntxp.tpls", []));
  const [dark, setDarkState] = useState(document.documentElement.dataset.theme === "dark");
  const [palette, setPaletteState] = useState(document.documentElement.dataset.palette || "ntxp");
  const delay = useRef(0); const seq = useRef(0); const toastT = useRef(null);

  const state = { f, q, near, miles, sort, dir };
  const query = buildQuery(state, { limit: SIZE, offset: page * SIZE });
  const toast = useCallback((msg, bad) => { setToast({ msg, bad }); clearTimeout(toastT.current); toastT.current = setTimeout(() => setToast(null), bad ? 5000 : 2600); }, []);

  useEffect(() => { document.body.dataset.view = view; document.documentElement.style.setProperty("--lines", view); store.set("ntxp.view", view); }, [view]);
  useEffect(() => onGate((m) => setGate(m || "")), []);
  useEffect(() => { if (CFG.dev) { signIn("").then(() => setStarted(true)); } }, []);

  // load (debounced) whenever the query changes
  useEffect(() => {
    if (!started) return undefined;
    const my = ++seq.current;
    const t = setTimeout(async () => {
      try {
        const d = await apiJson("/api/contacts?" + query);
        if (my !== seq.current) return;
        setRows(d.rows); setTotal(d.total); setError(""); setLive(d.total + " contacts");
      } catch (e) { if (e.message !== "auth") setError(e.message); }
    }, delay.current);
    delay.current = 120;
    return () => clearTimeout(t);
  }, [query, started, tick]);

  // an open report follows the filters, live
  const reportKey = report ? report.type + (report.custom ? JSON.stringify(report.tpl) : "") : "";
  useEffect(() => {
    if (!report) return undefined;
    let live = true;
    (async () => {
      try {
        const spec = report.custom ? await specFromTemplate(report.tpl) : (await apiJson("/api/report?" + buildQuery(state, { type: report.type, orientation: orient }))).spec;
        if (live) setReport((r) => (r && r.type === report.type ? { ...r, spec } : r));
      } catch (e) { if (e.message !== "auth") toast("Report: " + e.message, true); }
    })();
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, orient, reportKey]);

  const specFromTemplate = (t) => apiJson("/api/report/custom?" + buildQuery(state, { orientation: orient }), { method: "POST", body: { doc_title: t.doc_title, columns: t.columns, widths: t.widths } }).then((d) => d.spec);

  const resetPage = () => setPage(0);
  const addFilter = (k, v) => { delay.current = 0; setF((o) => (o[k].includes(v) ? o : { ...o, [k]: [...o[k], v] })); resetPage(); };
  const removeFilter = (k, v) => { delay.current = 0; setF((o) => ({ ...o, [k]: o[k].filter((x) => x !== v) })); resetPage(); };
  const clearAll = () => { delay.current = 0; setF(emptyFilters()); setQ(""); setNear(""); setMiles(""); resetPage(); };
  const onSort = (k) => { delay.current = 0; if (sort === k) setDir(dir === "asc" ? "desc" : "asc"); else { setSort(k); setDir("asc"); } resetPage(); };
  const onQ = (v) => { delay.current = 220; setQ(v); resetPage(); };
  const activeCount = Object.values(f).reduce((a, v) => a + v.length, 0) + (near && miles ? 1 : 0);

  const onSaved = (id, contact) => { setRows((rs) => rs.map((r) => (r.id === id ? { ...r, ...contact } : r))); setLive("Saved"); };
  const reload = () => { delay.current = 0; setTick((t) => t + 1); };
  const onLabels = async (id, body) => {
    if (body) { try { await apiJson("/api/contacts/" + id + "/labels", { method: "POST", body }); } catch (e) { toast(e.message, true); } }
    reload();
  };

  const setDark = (on) => { document.documentElement.dataset.theme = on ? "dark" : "light"; try { localStorage.setItem("ntxp.theme", on ? "dark" : "light"); } catch { /* ignore */ } setDarkState(on); };
  const setPalette = (p) => { document.documentElement.dataset.palette = p; try { localStorage.setItem("ntxp.palette", p); } catch { /* ignore */ } setPaletteState(p); };

  const closeDrawer = () => { setDrawer(false); setPanel(false); };
  useEffect(() => {
    const k = (e) => { if (e.key === "Escape" && (panel || drawer)) { closeDrawer(); document.getElementById('ham')?.focus(); } };
    document.addEventListener("keydown", k); return () => document.removeEventListener("keydown", k);
  }, [panel, drawer]);
  useEffect(() => { if (drawer) setTimeout(() => document.querySelector("#drawer .rb")?.focus(), 30); }, [drawer]);

  const openReport = async (type, tpl) => {
    closeDrawer();
    try {
      const spec = tpl ? await specFromTemplate(tpl) : (await apiJson("/api/report?" + buildQuery(state, { type, orientation: orient }))).spec;
      setReport({ type, spec, custom: !!tpl, tpl: tpl ? { doc_title: tpl.doc_title, columns: tpl.columns, widths: tpl.widths } : null }); scrollTo(0, 0);
    } catch (e) { if (e.message !== "auth") toast("Report: " + e.message, true); }
  };
  const saveReport = async (fmt) => {
    if (!report) return;
    setBusy(fmt); toast("Rendering with the NTXP document engine…");
    try {
      const r = report.custom
        ? await api("/api/report/render-custom?" + buildQuery(state, { orientation: orient }) + "&format=" + fmt, { method: "POST", body: report.tpl })
        : await api("/api/report/render?" + buildQuery(state, { type: report.type, orientation: orient }) + "&format=" + fmt);
      if (r.status === 501 && fmt === "pdf") { toast("Server renderer not configured — using your browser's Save as PDF."); setTimeout(() => print(), 400); return; }
      if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error((j.error || r.statusText) + (j.detail ? " — " + j.detail.slice(0, 160) : "")); }
      download(await r.blob(), "NTXP_" + report.spec.doc_title.replace(/\W+/g, "_") + "_" + stamp() + "." + fmt); toast("Saved " + fmt.toUpperCase());
    } catch (e) { if (e.message !== "auth") toast(e.message, true); } finally { setBusy(""); }
  };
  const exportCsv = async () => {
    try { const r = await api("/api/export.csv?" + buildQuery(state)); if (!r.ok) throw new Error(r.statusText); download(await r.blob(), "NTXP_contacts_" + stamp() + ".csv"); toast("CSV exported"); }
    catch (e) { if (e.message !== "auth") toast(e.message, true); }
  };
  const saveToDrive = async () => {
    if (f.project.length !== 1) return toast("Pick exactly one Project in the filters first — that's the folder it saves to.", true);
    if (CFG.dev || !CFG.clientId) return toast("Google Drive needs real sign-in (not available in dev mode).", true);
    const proj = f.project[0];
    try {
      toast("Rendering PDF…");
      const r = await api("/api/report/render?" + buildQuery(state, { type: "directory", orientation: orient }) + "&format=pdf");
      if (!r.ok) throw new Error("PDF render failed (" + r.status + ")");
      const pdf = await r.blob(); const tk = await driveToken(); const G = "https://www.googleapis.com/drive/v3/files";
      const find = async (qq) => (await (await fetch(G + "?supportsAllDrives=true&includeItemsFromAllDrives=true&fields=files(id,name)&q=" + encodeURIComponent(qq), { headers: { Authorization: "Bearer " + tk } })).json()).files || [];
      const root = (await find("name='!Active Projects' and mimeType='application/vnd.google-apps.folder' and trashed=false"))[0];
      if (!root) throw new Error("No '!Active Projects' folder found in your Drive.");
      const kids = await find("'" + root.id + "' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false and name contains '" + proj.replace(/'/g, "\\'") + "'");
      const dest = kids.find((x) => x.name.toLowerCase() === proj.toLowerCase()) || kids[0];
      if (!dest) throw new Error("No folder matching '" + proj + "' under !Active Projects.");
      const fd = new FormData();
      fd.append("metadata", new Blob([JSON.stringify({ name: "NTXP_Project_Directory_" + stamp() + ".pdf", parents: [dest.id] })], { type: "application/json" })); fd.append("file", pdf);
      const up = await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true", { method: "POST", headers: { Authorization: "Bearer " + tk }, body: fd });
      if (!up.ok) throw new Error("Drive upload failed (" + up.status + ")"); toast("Saved to !Active Projects / " + dest.name);
    } catch (e) { if (e.message !== "auth") toast(e.message, true); }
  };
  const onUpload = async (e) => {
    const file = e.target.files[0]; if (!file) return;
    try { const t = wipeSpec(JSON.parse(await file.text())); t.name = file.name.replace(/\.json$/i, ""); const l = [...templates, t]; store.set("ntxp.tpls", l); setTemplates(l); toast("Template added — all contact data in it was wiped, layout kept."); }
    catch (x) { toast("Couldn't read that template: " + x.message + " (upload a .json doc-engine spec; PDF/Word templates aren't supported yet)", true); }
    e.target.value = "";
  };
  const doSignIn = async (prompt) => { if (await signIn(prompt)) { setGate(null); setStarted(true); return true; } return false; };

  return (
    <>
      <div className="sr-only" id="live" role="status" aria-live="polite">{live}</div>
      {gate !== null && <Gate message={gate} onSignIn={() => doSignIn("select_account")} />}
      <Header total={started ? total : null} user={currentUser()} menuOpen={drawer} onMenu={() => (drawer ? closeDrawer() : setDrawer(true))} />
      {drawer && <div className="scrim fixed inset-0 bg-[rgba(15,22,38,.45)] z-[60]" id="scrim" onClick={closeDrawer} />}
      <ReportsDrawer open={drawer} orient={orient} onOrient={setOrient} templates={templates} onReport={(k) => openReport(k)} onTemplate={(t) => openReport("custom", t)}
        gearOpen={panel} onGear={() => setPanel(!panel)} />
      <SettingsPanel open={panel} dark={dark} onDark={setDark} palette={palette} onPalette={setPalette} templates={templates} onUpload={onUpload}
        onReauth={async () => { if (await signIn("consent")) toast("Re-authenticated"); }} onSignOut={() => { closeDrawer(); setStarted(false); signOut(); }} />
      <div className="shell grid grid-cols-[292px_minmax(0,1fr)] max-[900px]:grid-cols-[minmax(0,1fr)] gap-4 pt-4 pb-24 pl-(--gutter) pr-[calc(max(12px,env(safe-area-inset-right,0px))+164px)] max-[900px]:pr-(--gutter) items-start" id="shell">
        <FilterRail f={f} near={near} miles={miles} activeCount={activeCount} open={railOpen} onToggle={() => setRailOpen(!railOpen)}
          onAdd={addFilter} onRemove={removeFilter} onNear={(v) => { delay.current = 400; setNear(v); }} onMiles={(v) => { delay.current = 400; setMiles(v); }} onClear={clearAll} />
        <main id="main" className="min-w-0">
          {report ? (
            <ReportView report={report} landscape={orient === "landscape"} busy={busy} onBack={() => setReport(null)} onSave={saveReport} />
          ) : (
            <div id="tableView">
              <Toolbar view={view} onView={setView} q={q} onQ={onQ} f={f} near={near} miles={miles} onRemove={removeFilter}
                onClearProx={() => { delay.current = 0; setNear(""); setMiles(""); }} count={started ? total : null} />
              <ContactsTable rows={rows} total={total} sort={sort} dir={dir} onSort={onSort} page={page} size={SIZE} onPage={(p) => { delay.current = 0; setPage(p); scrollTo(0, 0); }}
                error={error} onHot={addFilter} onSaved={onSaved} onLabels={onLabels} toast={toast} />
            </div>
          )}
        </main>
      </div>
      {!report && <ExportRail onCsv={exportCsv} onPdf={() => openReport("full")} onDrive={saveToDrive} />}
      <Toast toast={toastMsg} />
    </>
  );
}
