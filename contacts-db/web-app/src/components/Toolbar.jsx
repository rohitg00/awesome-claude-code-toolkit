import { FIELDS } from "../lib/model";
import { IconButton, Seg } from "./ui/Button";

export function Toolbar({ view, onView, q, onQ, f, near, miles, onRemove, onClearProx, count }) {
  const chips = [];
  for (const [k, t] of FIELDS) f[k].forEach((v) => chips.push({ key: k + v, text: `${t}: ${v}`, label: "Remove filter " + v, off: () => onRemove(k, v), k, v }));
  if (near && miles) chips.push({ key: "prox", text: `Within ${miles} mi of ${near}`, label: "Remove proximity filter", off: onClearProx, prox: true });
  return (
    <div className="ctl sticky top-2 z-20 bg-float border border-warm-edge rounded shadow-[0_4px_14px_rgba(27,42,78,.16)] px-3 py-2 flex gap-3 items-center flex-wrap mb-3" role="search">
      <Seg label="View: lines per row" caption="VIEW" value={view} onChange={(v) => onView(+v)} options={[[1, "1"], [3, "3"], [5, "5"]]} />
      <input id="q" type="search" className="fld search flex-1 min-w-[180px] px-2.5 py-2 min-h-10 border border-warm-edge rounded bg-paper text-ink hover:border-navy"
        placeholder="Search name, company, email, project…" aria-label="Search contacts" value={q} onChange={(e) => onQ(e.target.value)} />
      <div className="chips flex gap-1.5 flex-wrap items-center" id="chips" role="group" aria-label="Active filters">
        {chips.map((c) => (
          <span key={c.key} className="chip inline-flex items-center gap-1 bg-warm border border-warm-edge rounded-full py-0.5 pl-2.5 pr-1 text-xs">
            {c.text}
            <IconButton size="sm" label={c.label} data-unf={c.k} data-val={c.v} data-unprox={c.prox ? "" : undefined} onClick={c.off}>×</IconButton>
          </span>
        ))}
      </div>
      <span className="count text-xs text-ink-soft ml-auto whitespace-nowrap" id="count" aria-live="polite">{count == null ? "" : count.toLocaleString() + " contacts"}</span>
    </div>
  );
}
