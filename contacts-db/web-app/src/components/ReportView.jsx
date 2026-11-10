import { Button } from "./ui/Button";
import { Logo } from "./ui/Chrome";
import { longDate } from "../lib/format";

const isEmail = (v) => /^[^\s@]+@[^\s@]+$/.test(v);
const isPhone = (v) => /^\d{3}-\d{3}-\d{4}$/.test(v);

/** The live, full-size NTXP document (standard 2.1): navy band + accent fade + tag line + section bars + warm rows. */
export function DocPreview({ spec, landscape }) {
  return (
    <div id="doc" className={"doc bg-white text-[#1F2A3D] mx-auto shadow-[0_2px_18px_rgba(0,0,0,.3)] pb-7 font-sans " + (landscape ? "land w-[1056px] min-h-[816px]" : "w-[816px] min-h-[1056px]")}>
      <div className="d-band bg-[#182746] h-24 grid grid-cols-[1.55in_1fr_1.55in] items-center text-white px-4">
        <Logo />
        <div><h2 className="m-0 text-[36px] tracking-[.09em] uppercase text-center leading-[1.05]">{spec.doc_title}</h2><p className="mt-[3px] mb-0 text-center text-lg">{spec.project_title || ""}</p></div>
        <span />
      </div>
      <div className="d-acc h-2" />
      <div className="d-tag flex gap-4 justify-center text-[10px] text-[#5A6880] p-1.5 border-b border-[#E2DAD0] mb-3.5">
        {(spec.meta || []).map((m) => <span key={m[0]}><b>{m[0]}</b> {m[1]}</span>)}<span><b>DATE</b> {longDate()}</span>
      </div>
      {spec.sections.map((s, si) => s.flow ? (
        <div key={si} className="d-card mx-7 mb-3.5 border border-[#CDC0B2] rounded overflow-hidden shadow-[0_1px_3px_rgba(27,42,78,.14)]">
          <div className="d-bar bg-[#1B2A4E] text-white font-bold uppercase tracking-[.12em] text-[11px] text-center p-2">{s.title}</div>
          <div className="d-tiles flex gap-2.5 justify-center p-3">{s.flow[0].items.map((i) => (
            <div key={i.label} className="d-tile bg-[#1B2A4E] text-white rounded text-center px-4 py-3 min-w-[118px]"><b className="block text-[26px]">{i.value}</b><span className="text-[9px] tracking-[.1em] uppercase">{i.label}</span></div>))}</div>
        </div>
      ) : (
        <div key={si} className="d-card mx-7 mb-3.5 border border-[#CDC0B2] rounded overflow-hidden shadow-[0_1px_3px_rgba(27,42,78,.14)]">
          <div className="d-bar relative bg-[#1B2A4E] text-white font-bold uppercase tracking-[.12em] text-[11px] text-center p-2">{s.title}<span className="absolute right-2.5">{s.rows.length}</span></div>
          <table className="w-full border-collapse text-[10px]">
            <thead><tr>{s.columns.map((c, i) => <th key={c} style={{ width: (s.widths ? s.widths[i] : 100 / s.columns.length) + "%" }} className="bg-[#46567D] text-white px-1 py-[7px] text-[9px] uppercase tracking-[.08em] border-r border-[#35446B]">{c}</th>)}</tr></thead>
            <tbody>{s.rows.map((r, ri) => (
              <tr key={ri} className={ri % 2 ? "bg-[#F6F3EF]" : ""}>{r.map((v, i) => (
                <td key={i} className="px-1 py-[5px] border-t border-[#E2DAD0] text-center text-[10px] text-[#1F2A3D]">
                  {isEmail(v) ? <a className="text-[#2F529B]" href={"mailto:" + v}>{v}</a> : isPhone(v) ? <a className="text-[#2F529B]" href={"tel:" + v}>{v}</a> : v}
                </td>))}</tr>))}</tbody>
          </table>
        </div>
      ))}
      <div className="d-foot flex justify-between mx-7 mt-2 text-[9px] text-[#5A6880]"><span>{spec.footer_left || ""}</span><span>{spec.footer_center || ""}</span><b className="italic text-[#1B2A4E]">Page 1 of 1 (preview)</b></div>
    </div>
  );
}

export function ReportView({ report, landscape, onBack, onSave, busy }) {
  return (
    <div id="reportView">
      <div className="rv-bar flex gap-2.5 items-center justify-center flex-wrap mb-3">
        <Button id="rvBack" onClick={onBack}>← Back to contacts</Button>
        <strong id="rvTitle">{report.spec.doc_title} · {report.spec.project_title || ""}</strong>
        <Button id="rvWord" loading={busy === "docx"} disabled={!!busy} onClick={() => onSave("docx")}>Word (.docx)</Button>
        <Button id="rvDone" variant="primary" size="lg" className="done" autoFocus loading={busy === "pdf"} disabled={!!busy} onClick={() => onSave("pdf")}>Done · Save as PDF</Button>
      </div>
      <div className="docscroll overflow-auto pt-1 pb-6"><DocPreview spec={report.spec} landscape={landscape} /></div>
    </div>
  );
}
