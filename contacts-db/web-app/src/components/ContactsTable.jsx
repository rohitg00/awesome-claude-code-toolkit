import { useEffect, useRef, useState } from "react";
import { apiJson } from "../lib/auth";
import { COLS, editBody, rawFor } from "../lib/model";
import { fmtPhone, initials, mapUrl, safeUrl, telHref } from "../lib/format";
import { Bar } from "./ui/Chrome";
import { Button } from "./ui/Button";

const A11Y_LINK = "inline-block min-h-6 min-w-6 text-center leading-6 rounded-sm hover:bg-warm-line active:bg-warm-edge";

function Hot({ field, val, onHot }) {
  const go = () => onHot(field, val);
  return (
    <a className={"hot cursor-pointer underline underline-offset-2 text-link " + A11Y_LINK} role="button" tabIndex={0} data-hot={field} data-val={val}
      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); e.stopPropagation(); go(); } }}>
      {val}
    </a>
  );
}

function LabelAdder({ onDone }) {
  const [adding, setAdding] = useState(false);
  const done = useRef(false);
  const finish = (ok, val) => { if (done.current) return; done.current = true; setAdding(false); onDone(ok ? val.trim() : ""); };
  if (!adding) return <Button size="sm" className="lbl !min-h-6 !rounded-full !px-2 !py-0" data-variant="pill" data-addlbl aria-label="Add label" onClick={() => { done.current = false; setAdding(true); }}>+</Button>;
  return (
    <input autoFocus aria-label="New label" className="fld w-[120px] px-2 py-1 min-h-8 border border-warm-edge rounded bg-paper text-ink"
      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); finish(true, e.currentTarget.value); } else if (e.key === "Escape") finish(false, ""); }}
      onBlur={(e) => finish(true, e.currentTarget.value)} />
  );
}

function Cell({ c, r, onHot, onLabels }) {
  switch (c.k) {
    case "name":
      return (
        <div className="nm flex items-start gap-2 justify-center text-left">
          {safeUrl(r.photo_url)
            ? <img className="ph size-[30px] rounded-full object-cover shrink-0" alt="" loading="lazy" src={r.photo_url} />
            : <span className="ph size-[30px] rounded-full bg-navy text-white grid place-items-center text-[11px] font-bold shrink-0" aria-hidden="true">{initials(r)}</span>}
          <div className="cell leading-6">{r.full_name || ""}<span className="sub block text-ink-soft text-[11px] leading-[1.3]">{r.title || ""}</span></div>
        </div>
      );
    case "company":
      return r.company ? <div className="cell"><Hot field="company" val={r.company} onHot={onHot} /><span className="sub block text-ink-soft text-[11px]">{r.title || ""}</span></div> : null;
    case "role": case "trade": case "project":
      return r[c.k] ? <div className="cell"><Hot field={c.k} val={r[c.k]} onHot={onHot} /></div> : null;
    case "city":
      return r.city ? <div className="cell"><Hot field="city" val={r.city} onHot={onHot} />{" "}
        <a className={A11Y_LINK} href={mapUrl(r.city, r.state)} target="_blank" rel="noopener" aria-label={"Map of " + r.city} title="Open in Maps">↗</a></div> : null;
    case "state":
      return r.state ? <div className="cell"><Hot field="state" val={r.state} onHot={onHot} /></div> : null;
    case "phone":
      return r.phone ? <div className="cell"><a className={A11Y_LINK} href={telHref(r.phone)}>{fmtPhone(r.phone)}</a></div> : null;
    case "email":
      return r.email ? <div className="cell"><a className={A11Y_LINK} href={"mailto:" + r.email}>{r.email}</a></div> : null;
    case "labels":
      return (
        <div className="lbls flex flex-wrap gap-1">
          {(r.labels || []).map((l) => (
            <span key={l} className="lbl whitespace-nowrap bg-paper border border-warm-edge rounded-full px-2 text-[11px] min-h-[22px] inline-flex items-center gap-0.5">
              <Hot field="label" val={l} onHot={onHot} />
              <button type="button" aria-label={"Remove label " + l} data-rm={l} data-variant="icon-ghost"
                className="min-w-6 min-h-6 px-1 font-bold leading-none rounded-full hover:bg-warm-line active:bg-warm-edge" onClick={() => onLabels(r.id, { remove: [l] })}>×</button>
            </span>
          ))}
          <LabelAdder onDone={(val) => onLabels(r.id, val ? { add: [val] } : null)} />
        </div>
      );
    case "linkedin":
      return safeUrl(r.linkedin_url)
        ? <div className="cell"><a className={A11Y_LINK} href={r.linkedin_url} target="_blank" rel="noopener">LinkedIn</a></div>
        : <div className="cell mini text-xs text-ink-soft">—</div>;
    default: return null;
  }
}

function DataCell({ c, r, onHot, onLabels, onSaved, toast }) {
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const td = useRef(null);
  const link = useRef(null);
  const refocus = useRef(false);
  useEffect(() => { if (!editing && refocus.current) { refocus.current = false; td.current?.focus(); } }, [editing]);

  const begin = () => { if (c.edit && !editing) setEditing(true); };
  const end = async (commit, val, keepFocus) => {
    if (!editing) return;
    refocus.current = keepFocus;
    setEditing(false);
    val = val.trim();
    if (!commit || val === rawFor(c, r)) return;
    try {
      const d = await apiJson("/api/contacts/" + r.id, { method: "PATCH", body: editBody(c, val) });
      onSaved(r.id, d.contact || {});
      setSaved(true); setTimeout(() => setSaved(false), 1000);
      refocus.current = true; td.current?.focus();
    } catch (e) { if (e.message !== "auth") toast(c.t + ": " + e.message, true); td.current?.focus(); }
  };
  const follow = (a) => {
    if (a.dataset.hot) return onHot(a.dataset.hot, a.dataset.val);
    const href = a.getAttribute("href"); if (!href) return;
    if (a.target === "_blank") window.open(href, "_blank", "noopener"); else window.location.href = href;
  };
  const props = c.edit ? {
    tabIndex: 0, "data-edit": c.edit, "data-col": c.k,
    onDoubleClick: () => { clearTimeout(link.current); begin(); },
    onKeyDown: (e) => { if (e.target === td.current && !editing && (e.key === "Enter" || e.key === "F2")) { e.preventDefault(); begin(); } },
    onClick: (e) => {
      const a = e.target.closest("a"); if (!a || editing || !td.current.contains(a)) return;
      e.preventDefault(); clearTimeout(link.current); link.current = setTimeout(() => follow(a), 260);   // a double-click edits instead
    },
  } : {};
  return (
    <td ref={td} {...props}
      className={["px-2 py-[7px] align-top text-[13px] border-t border-r border-warm-line break-normal", c.para ? "para text-left [overflow-wrap:anywhere]" : "text-center",
        c.k === "company" ? "min-w-[170px]" : "", c.k === "labels" ? "min-w-[210px]" : "", editing ? "editing" : "", saved ? "saved" : "",
        "focus-visible:outline-offset-[-3px]"].join(" ")}>
      {editing
        ? <input autoFocus aria-label={"Edit " + c.t} defaultValue={rawFor(c, r)} onFocus={(e) => e.target.select()}
            className="w-full bg-transparent text-ink border-0 outline-none font-[inherit]"
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); end(true, e.currentTarget.value, true); } else if (e.key === "Escape") { e.preventDefault(); end(false, "", true); } }}
            onBlur={(e) => end(true, e.currentTarget.value, false)} />
        : <Cell c={c} r={r} onHot={onHot} onLabels={onLabels} />}
    </td>
  );
}

export function ContactsTable({ rows, total, sort, dir, onSort, page, size, onPage, error, onHot, onSaved, onLabels, toast }) {
  const pages = Math.max(1, Math.ceil(total / size));
  return (
    <div className="card bg-paper border border-warm-edge border-b-2 rounded shadow-card overflow-hidden">
      <Bar count={total.toLocaleString()}>Contacts</Bar>
      <div className="tbl-wrap overflow-x-auto">
        <table id="tbl" className="ntxp border-collapse w-full min-w-[1320px]">
          <caption className="sr-only">Company contacts. Double-click or press Enter on a cell to edit it.</caption>
          <thead>
            <tr id="thr">
              {COLS.map((c) => {
                const aria = c.sort ? (sort === c.sort ? (dir === "asc" ? "ascending" : "descending") : "none") : undefined;
                return (
                  <th key={c.k} scope="col" aria-sort={aria} className="bg-navy-mid text-white font-bold uppercase tracking-[.08em] text-[11px] p-0 border-r border-navy-rule sticky top-0">
                    {c.sort
                      ? <button type="button" data-sort={c.sort} onClick={() => onSort(c.sort)} className="w-full bg-transparent border-0 text-white [font:inherit] uppercase tracking-[inherit] px-2 py-3 flex justify-center items-center gap-1.5 min-h-11 hover:bg-navy-rule active:bg-navy">
                          {c.t} <span className="ar text-[10px] opacity-55" aria-hidden="true" /></button>
                      : <div className="w-full text-white px-2 py-3 flex justify-center items-center min-h-11">{c.t}</div>}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody id="tb">
            {error ? <tr><td colSpan={11} className="empty err p-9 text-center text-signal-ink font-semibold">{error}</td></tr>
              : rows.length ? rows.map((r) => (
                <tr key={r.id} data-id={r.id}>
                  {COLS.map((c) => <DataCell key={c.k} c={c} r={r} onHot={onHot} onLabels={onLabels} onSaved={onSaved} toast={toast} />)}
                </tr>))
              : <tr><td colSpan={11} className="empty p-9 text-center text-ink-soft">No contacts match these filters.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="foot flex justify-between items-center gap-3 px-3 py-2.5 border-t border-warm-line flex-wrap">
        <span className="mini text-xs text-ink-soft" id="hint">Double-click a cell (or press Enter) to edit · changes save instantly</span>
        <span className="inline-flex items-center gap-2">
          <Button size="sm" id="prev" disabled={page === 0} onClick={() => onPage(page - 1)}>Previous</Button>
          <Button size="sm" id="next" disabled={page + 1 >= pages} onClick={() => onPage(page + 1)}>Next</Button>
          <span className="pg font-bold italic text-navy dark:text-ink" id="pg">Page {page + 1} of {pages}</span>
        </span>
      </div>
    </div>
  );
}
