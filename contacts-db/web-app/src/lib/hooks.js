import { useEffect } from "react";

/** React 18 does not understand the `inert` attribute, so set the DOM property directly. */
export function useInert(ref, on) {
  useEffect(() => { if (ref.current) ref.current.inert = !!on; }, [ref, on]);
}

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select,textarea,[tabindex]:not([tabindex="-1"])';

/** Keeps Tab / Shift+Tab inside a dialog while it is open. */
export function useFocusTrap(ref, active) {
  useEffect(() => {
    const el = ref.current;
    if (!active || !el) return undefined;
    const onKey = (e) => {
      if (e.key !== "Tab") return;
      const f = [...el.querySelectorAll(FOCUSABLE)].filter((x) => { const cs = getComputedStyle(x); return cs.display !== "none" && cs.visibility !== "hidden" && !x.hidden; });
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    el.addEventListener("keydown", onKey);
    return () => el.removeEventListener("keydown", onKey);
  }, [ref, active]);
}
