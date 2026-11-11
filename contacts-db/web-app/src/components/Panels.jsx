import { useEffect, useRef, useState } from "react";
import { useFocusTrap, useInert } from "../lib/hooks";
import { apiJson, currentUser } from "../lib/auth";
import { PALETTES, REPORTS } from "../lib/model";
import { Button, IconButton, Seg, Switch } from "./ui/Button";

export function ReportsDrawer({ open, orient, onOrient, templates, onReport, onTemplate, onGear, gearOpen, panelOpen }) {
  const ref = useRef(null);
  useInert(ref, !open || panelOpen);         // closed drawer (or one under the Settings dialog) is not reachable
  useFocusTrap(ref, open && !panelOpen);
  return (
    <div id="drawer" ref={ref} role="dialog" aria-modal="true" aria-label="Reports"
      className={"drawer fixed top-0 left-0 bottom-0 w-[min(320px,88vw)] bg-baby text-baby-ink z-[70] px-4 pb-4 pt-[max(16px,env(safe-area-inset-top,0px))] flex flex-col gap-2 shadow-[4px_0_22px_rgba(0,0,0,.25)] overflow-auto transition-transform duration-[280ms] " +
        (open ? "open translate-x-0 visible" : "-translate-x-[102%] invisible")}>
      <h2 className="mt-1.5 mb-1 text-[15px] tracking-[.18em] text-center uppercase">Reports</h2>
      <div id="reportBtns" className="flex flex-col gap-2">
        {REPORTS.map(([k, n]) => <Button key={k} variant="drawer" className="rb" data-rep={k} onClick={() => onReport(k)}>{n}</Button>)}
        {templates.map((t, i) => <Button key={i} variant="drawer" className="rb" data-tpl={i} onClick={() => onTemplate(t)}>★ {t.name}</Button>)}
      </div>
      <div className="sub2 text-[11px] tracking-[.1em] uppercase font-bold mt-2">Page orientation</div>
      <Seg label="Report orientation" tone="drawer" value={orient} onChange={onOrient} options={[["portrait", "Portrait"], ["landscape", "Landscape"]]} />
      <div className="mini text-xs">Reports use the current filters, live.</div>
      <IconButton variant="drawer" id="gear" label="Settings" aria-expanded={gearOpen} aria-controls="panel" onClick={onGear} className="gear mt-auto self-start !size-12 !text-[22px]">⚙</IconButton>
    </div>
  );
}

function Council() {
  const [text, setText] = useState("Loading…");
  useEffect(() => {
    apiJson("/api/council").then((d) => {
      const e = d.effectiveness;
      setText(e.decisions ? <><b>{e.decisions}</b> decisions · <b>{e.resolved_free_by_jev_pct}%</b> resolved free by JEV · total cost <b>${e.total_cost}</b></> : "No council decisions recorded yet.");
    }).catch(() => setText("Unavailable."));
  }, []);
  return <div className="mini text-xs text-ink-soft" id="council">{text}</div>;
}

const H3 = "m-0 mb-2 text-[11px] tracking-[.12em] uppercase text-ink-soft";
export function SettingsPanel({ open, dark, onDark, palette, onPalette, templates, onUpload, onReauth, onSignOut, onClose }) {
  const ref = useRef(null);
  useFocusTrap(ref, open);
  useEffect(() => { if (open) ref.current?.querySelector("h2")?.focus(); }, [open]);   // focus moves into the dialog
  if (!open) return <div id="panel" className="panel" hidden />;
  const me = currentUser();
  return (
    <div id="panel" ref={ref} role="dialog" aria-modal="true" aria-labelledby="settings-title"
      className="panel fixed left-[max(16px,env(safe-area-inset-left,0px))] bottom-[76px] w-[min(380px,calc(100vw-32px))] max-h-[calc(100vh-110px)] overflow-auto z-[80] bg-paper border border-warm-edge rounded-md shadow-[0_12px_40px_rgba(0,0,0,.35)] [&_section]:px-3.5 [&_section]:py-3 [&_section]:border-b [&_section]:border-warm-line">
      <section className="flex items-center justify-between gap-2">
        <h2 id="settings-title" tabIndex={-1} className="m-0 text-[13px] tracking-[.12em] uppercase text-navy dark:text-ink">Settings</h2>
        <Button size="sm" id="panelClose" onClick={onClose}>Close</Button>
      </section>
      <section><h3 className={H3}>Account</h3>
        <div className="flex items-center justify-between gap-2.5"><span id="acctEmail" className="mini text-xs text-ink-soft">{me?.email}</span></div>
        <div className="flex items-center gap-2 mt-2"><Button size="sm" id="reauth" onClick={onReauth}>Re-authenticate</Button><Button size="sm" id="signout" onClick={onSignOut}>Sign out</Button></div>
        <div className="mini text-xs text-ink-soft mt-1.5">Access is limited to the ntxpllc.com Google Workspace domain.</div></section>
      <section><h3 className={H3}>Appearance</h3>
        <div className="flex items-center justify-between gap-2.5"><label htmlFor="dark">Dark mode</label><Switch id="dark" checked={dark} onChange={onDark} /></div>
        <div className="sw flex gap-2.5 flex-wrap mt-2.5" id="palettes" role="group" aria-label="Colour palette">
          {PALETTES.map(([k, n, c]) => (
            <button key={k} type="button" data-p={k} data-variant="swatch" aria-pressed={palette === k} onClick={() => onPalette(k)}
              className="flex items-center gap-1.5 border border-warm-edge bg-paper text-ink rounded px-2 py-1 min-h-9 text-xs hover:bg-warm active:bg-warm-line aria-pressed:border-link aria-pressed:shadow-[inset_0_0_0_2px_var(--link)]">
              <i className="size-[18px] rounded-full inline-block border border-black/20" style={{ background: c }} />{n}
            </button>))}
        </div></section>
      <section><h3 className={H3}>Report templates</h3>
        <label className="mini text-xs text-ink-soft" htmlFor="tplFile">Upload an example report (NTXP doc-engine <b>.json</b> spec). Its contact data is wiped on upload; only the layout is kept.</label>
        <input type="file" id="tplFile" accept=".json,application/json" className="mt-1.5 w-full" onChange={onUpload} />
        <div className="mini text-xs text-ink-soft" id="tplList">{templates.length ? "Saved: " + templates.map((t) => t.name).join(", ") : ""}</div></section>
      <section><h3 className={H3}>Model council · consensus of effectiveness</h3><Council /></section>
    </div>
  );
}
