import { useEffect, useRef, useState } from "react";
import { apiJson } from "../lib/auth";
import { Bar } from "./ui/Chrome";
import { Button } from "./ui/Button";
import { FIELDS } from "../lib/model";

const fld = "fld w-full px-2.5 py-2 min-h-10 border border-warm-edge rounded bg-paper text-ink hover:border-navy focus:border-link";

/** One click-to-reveal facet: typable input, then a checklist (multi-select = OR within the field). */
function Facet({ k, title, selected, onAdd, onRemove }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [vals, setVals] = useState([]);
  const input = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    let live = true;
    const t = setTimeout(async () => {
      try {
        let v;
        if (k === "label") {
          const all = await apiJson("/api/facets");
          v = (all.labels || []).filter((l) => l.value.toLowerCase().includes(text.toLowerCase())).slice(0, 40);
        } else v = (await apiJson("/api/facets?" + new URLSearchParams({ field: k, q: text, limit: 40 }))).values || [];
        if (live) setVals(v);
      } catch { /* auth errors surface via the gate */ }
    }, text ? 180 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [open, text, k, selected.length]);
  useEffect(() => { if (open) input.current?.focus(); }, [open]);
  const merged = selected.map((v) => ({ value: v, count: null })).concat(vals.filter((x) => !selected.includes(x.value)));
  return (
    <div className="acc border-b border-warm-line last-of-type:border-b-0">
      <button type="button" className="acc-h w-full flex justify-between items-center gap-2 px-2 py-2.5 min-h-11 bg-transparent border-0 text-left font-semibold hover:bg-warm focus-visible:bg-warm"
        aria-expanded={open} aria-controls={"p-" + k} data-acc={k} onClick={() => setOpen(!open)}>
        <span>{title}</span>
        <span className="inline-flex items-center gap-1">
          <span className="cnt bg-navy text-white rounded-full text-[11px] px-2 py-px min-w-[22px] text-center" data-f={k} hidden={!selected.length}>{selected.length}</span>
          <span className={"chev transition-transform duration-200 " + (open ? "rotate-180" : "")} aria-hidden="true">▾</span>
        </span>
      </button>
      <div className="acc-p px-2 pb-2.5" id={"p-" + k} hidden={!open}>
        <label className="sr-only" htmlFor={"i-" + k}>Type to find {title}</label>
        <input ref={input} className={fld} id={"i-" + k} data-fi={k} type="search" placeholder="Type to find…" autoComplete="off" value={text} onChange={(e) => setText(e.target.value)} />
        <ul className="chk list-none m-0 mt-1.5 p-0 max-h-[210px] overflow-auto" id={"l-" + k}>
          {merged.length ? merged.map((x) => (
            <li key={x.value} className="flex items-center gap-2 px-0.5 py-1 min-h-8">
              <label className="flex-1 flex items-center gap-2 cursor-pointer min-w-0">
                <input type="checkbox" className="size-[18px] accent-navy" data-ck={k} data-val={x.value} checked={selected.includes(x.value)}
                  onChange={(e) => (e.target.checked ? onAdd(k, x.value) : onRemove(k, x.value))} />
                <span className="t overflow-hidden text-ellipsis whitespace-nowrap">{x.value}</span>
              </label>
              <span className="ct text-ink-soft text-[11px]">{x.count == null ? "" : x.count}</span>
            </li>
          )) : <li className="mini text-xs text-ink-soft">No matches</li>}
        </ul>
      </div>
    </div>
  );
}

export function FilterRail({ f, near, miles, activeCount, open, onToggle, onAdd, onRemove, onNear, onMiles, onClear }) {
  return (
    <aside className={"rail card sticky top-3 max-[900px]:static max-h-[calc(100vh-24px)] max-[900px]:max-h-none overflow-auto bg-paper border border-warm-edge border-b-2 rounded shadow-card " + (open ? "" : "closed")} aria-label="Filters">
      <Bar as="button" id="railToggle" type="button" aria-expanded={open} aria-controls="rail" onClick={onToggle}
        className="barbtn block w-full border-0 min-h-11 cursor-pointer hover:bg-navy-mid focus-visible:bg-navy-mid">
        <span aria-hidden="true" className={"absolute left-3.5 top-1/2 -translate-y-1/2 transition-transform duration-200 " + (open ? "-translate-y-1/2" : "-rotate-90")}>▾</span>
        Filters <span className="n absolute right-3 top-1/2 -translate-y-1/2 text-xs tracking-[.04em]" id="railN" aria-hidden="true">{activeCount ? activeCount + " active" : ""}</span>
      </Bar>
      <div className="rail-body p-2" id="rail">
        {FIELDS.map(([k, t]) => <Facet key={k} k={k} title={t} selected={f[k]} onAdd={onAdd} onRemove={onRemove} />)}
        <div className="acc border-b border-warm-line">
          <div className="acc-h px-2 py-2.5 font-semibold"><span>Proximity (miles)</span></div>
          <div className="prox grid grid-cols-[1fr_84px] gap-2 p-2">
            <div><label htmlFor="near" className="block mb-[3px] text-[11px] font-bold tracking-[.06em] uppercase text-ink-soft">Near (City, ST)</label>
              <input id="near" className={fld} placeholder="Dallas, TX" autoComplete="off" value={near} onChange={(e) => onNear(e.target.value)} /></div>
            <div><label htmlFor="miles" className="block mb-[3px] text-[11px] font-bold tracking-[.06em] uppercase text-ink-soft">Miles</label>
              <input id="miles" className={fld} inputMode="numeric" placeholder="25" value={miles} onChange={(e) => onMiles(e.target.value.replace(/\D/g, ""))} /></div>
          </div>
          <div className="presets flex gap-1.5 px-2 pb-2 flex-wrap" aria-label="Distance presets">
            {[10, 25, 50, 100].map((m) => <Button key={m} size="sm" data-mi={m} aria-pressed={String(miles) === String(m)} onClick={() => onMiles(String(m))}>{m}</Button>)}
          </div>
        </div>
        <div className="px-2 py-2.5"><Button id="clear" className="w-full" onClick={onClear}>Clear all filters</Button></div>
      </div>
    </aside>
  );
}
