import { useEffect, useState } from "react";
import { longDate } from "../../lib/format";

/** The reversed NTXP logo from the NTXP Document Engine assets (mounted at deploy time, never in git).
 *  Standard 2.1: fixed 1.55in zone, height-governed at 0.82in. Never recoloured, redrawn or faked: if the
 *  asset is missing we render NO substitute mark — only accessible text — and say so in the console. */
export function Logo({ zone = "w-[1.55in]", height = "h-[0.82in]", className = "" }) {
  const [ok, setOk] = useState(null);
  useEffect(() => { window.__logo = ok === true; }, [ok]);
  return (
    <div className={`logo flex items-center ${zone} ${height} ${className}`}>
      {ok !== false && (
        <img src="/assets/ntxp_logo_reversed.png" alt="NTXP LLC General Contractors" className={`${height} w-auto object-contain`}
          onLoad={() => setOk(true)}
          onError={() => { setOk(false); console.warn("NTXP logo asset missing: mount ntxp_logo_reversed.png at /assets (see deploy/RUNBOOK.md)."); }} />
      )}
      {ok === false && <span className="sr-only">NTXP LLC General Contractors</span>}
    </div>
  );
}

/** Navy band (1.00in) + accent fade (0.085in) + tag line, per NTXP-DOC-STANDARD 2.1. */
export function Header({ total, user, menuOpen, onMenu }) {
  const initial = user?.email ? user.email[0].toUpperCase() : "";
  return (
    <header id="top">
      <div className="band relative grid h-24 max-[640px]:h-[76px] items-center bg-band text-white pt-[env(safe-area-inset-top,0px)] px-(--gutter) grid-cols-[56px_1.55in_1fr_auto] max-[640px]:grid-cols-[52px_1fr_auto]">
        <button id="ham" type="button" aria-label="Reports menu" aria-expanded={menuOpen} aria-controls="drawer" onClick={onMenu}
          data-variant="icon-band"
          className={"hamburger size-11 rounded border border-white/40 bg-transparent grid place-items-center transition-[transform,background-color] duration-300 hover:bg-white/15 hover:border-white active:bg-white/25 " + (menuOpen ? "[transform:rotate(90deg)]" : "")}>
          <i />
        </button>
        <Logo className="max-[640px]:hidden" />
        <div className="lockup text-center min-w-0 px-2">
          <h1 className="m-0 text-[37px] max-[640px]:text-[22px] leading-[1.05] font-bold tracking-[.09em] uppercase whitespace-nowrap overflow-hidden text-ellipsis">NTXP Contacts</h1>
          <p className="mt-1 mb-0 text-[19px] leading-[1.1] font-normal whitespace-nowrap overflow-hidden text-ellipsis max-[640px]:hidden">Canonical directory · Lightfield is the source of truth</p>
        </div>
        <div className="acct flex items-center gap-2 text-xs max-w-[230px]">
          <span className="who overflow-hidden text-ellipsis whitespace-nowrap max-[640px]:hidden" id="who">{user?.email || ""}</span>
          <span id="av" aria-hidden="true" className="av size-[30px] rounded-full bg-white text-navy grid place-items-center font-bold text-xs shrink-0">{initial}</span>
        </div>
      </div>
      <div className="accent h-2" aria-hidden="true" />
      <div className="tag flex gap-[18px] max-[640px]:gap-x-3.5 max-[640px]:gap-y-1 justify-center flex-wrap py-[7px] px-(--gutter) text-[11px] text-ink-soft border-b border-warm-line">
        <span><b className="text-navy dark:text-ink tracking-[.06em] mr-1">CONTACTS</b><span id="tagN">{total == null ? "—" : total.toLocaleString()}</span></span>
        <span className="max-[640px]:hidden"><b className="text-navy dark:text-ink tracking-[.06em] mr-1">SOURCE</b>NTXP canonical (Lightfield, reconciled nightly)</span>
        <span><b className="text-navy dark:text-ink tracking-[.06em] mr-1">DATE</b><span id="tagD">{longDate()}</span></span>
      </div>
    </header>
  );
}

/** Navy section bar: white bold uppercase, centred; the count is absolutely positioned (standard 2.1). */
export function Bar({ children, count, as: Tag = "div", className = "", ...rest }) {
  return (
    <Tag className={"bar relative bg-navy text-white font-bold uppercase tracking-[.12em] text-xs text-center px-3 py-2.5 " + className} {...rest}>
      {children}
      {count != null && <span id="barN" className="n absolute right-3 top-1/2 -translate-y-1/2 text-xs tracking-[.04em]">{count}</span>}
    </Tag>
  );
}

/** Always mounted so assistive tech registers the live region before text appears.
 *  Errors are assertive (role=alert); confirmations are polite (role=status). */
export function Toast({ toast, onPause, onResume }) {
  const bad = !!toast?.bad;
  return (
    <div id="toast" role={bad ? "alert" : "status"} aria-live={bad ? "assertive" : "polite"}
      onMouseEnter={onPause} onMouseLeave={onResume} onFocus={onPause} onBlur={onResume}
      className={toast
        ? "toast fixed left-1/2 -translate-x-1/2 bottom-[max(18px,env(safe-area-inset-bottom,0px))] max-[900px]:bottom-[84px] px-4 py-2.5 rounded z-[120] max-w-[calc(100vw-32px)] shadow-[0_6px_20px_rgba(0,0,0,.35)] " +
          (bad ? "bad bg-signal-ink text-white dark:bg-[#FF8A90] dark:text-[#1b0b0d]" : "bg-navy text-white")
        : "toast sr-only"}>
      {toast?.msg}
    </div>
  );
}
