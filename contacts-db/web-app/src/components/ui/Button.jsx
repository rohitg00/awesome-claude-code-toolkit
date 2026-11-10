import { forwardRef } from "react";

/**
 * The one button. Every clickable control in the app goes through this (or IconButton/Seg/Switch
 * below) so states stay consistent and auditable:
 *   rest · hover · active (pressed-in) · focus-visible (global 3px ring) · disabled · loading · aria-pressed
 * Sizes: md = 44px (primary actions, touch), sm = 32px (dense toolbars). Icon-only: see IconButton.
 */
const BASE =
  "inline-flex items-center justify-center gap-2 rounded font-semibold border select-none " +
  "transition-colors duration-150 active:translate-y-px " +
  "disabled:opacity-50 disabled:cursor-not-allowed disabled:active:translate-y-0";

const VARIANT = {
  primary:
    "bg-navy text-white border-navy hover:bg-navy-mid hover:border-navy-mid active:bg-navy-rule " +
    "dark:border-warm-edge",
  secondary:
    "bg-paper text-ink border-warm-edge hover:bg-warm hover:border-navy active:bg-warm-line " +
    "dark:hover:border-link",
  // on the navy band
  band: "bg-transparent text-white border-white/40 hover:bg-white/15 hover:border-white active:bg-white/25",
  // REPORTS drawer (baby blue)
  drawer:
    "bg-white/65 text-baby-ink border-baby-ink/25 hover:bg-white hover:border-baby-ink active:bg-white/90 w-full justify-start text-left",
};
const PRESSED = "aria-pressed:bg-navy aria-pressed:text-white aria-pressed:border-navy aria-pressed:hover:bg-navy-mid";
const SIZE = { md: "min-h-11 px-4 py-2 text-sm", sm: "min-h-8 px-2.5 py-1 text-xs", lg: "min-h-13 px-9 py-3 text-[17px] tracking-[.08em] uppercase font-bold" };

export const Button = forwardRef(function Button(
  { variant = "secondary", size = "md", loading = false, className = "", children, disabled, type = "button", ...rest }, ref) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      data-variant={variant}
      className={[BASE, VARIANT[variant], PRESSED, SIZE[size], className].join(" ")}
      {...rest}
    >
      {loading && <span aria-hidden="true" className="size-4 rounded-full border-2 border-current border-t-transparent animate-spin" />}
      {children}
    </button>
  );
});

/** Icon-only button: `label` is mandatory (it becomes aria-label + title). */
export const IconButton = forwardRef(function IconButton(
  { label, variant = "ghost", size = "md", className = "", children, ...rest }, ref) {
  const sizes = { md: "size-11 text-xl", sm: "size-7 text-sm" };       // sm >= 28px, never below 24px
  const variants = {
    ghost: "bg-transparent text-inherit border-transparent hover:bg-warm-line active:bg-warm-edge",
    band: VARIANT.band,
    drawer: "bg-white/70 text-baby-ink border-baby-ink/35 hover:bg-white hover:border-baby-ink active:bg-white/90",
  };
  return (
    <button ref={ref} type="button" aria-label={label} title={label} data-variant={`icon-${variant}`}
      className={["inline-flex items-center justify-center rounded-full border font-bold leading-none select-none transition-colors duration-150 active:translate-y-px",
        sizes[size], variants[variant], className].join(" ")}
      {...rest}>
      {children}
    </button>
  );
});

/** Segmented control (VIEW 1/3/5, orientation). */
export function Seg({ label, value, options, onChange, caption, tone = "paper" }) {
  return (
    <div role="group" aria-label={label} className="seg inline-flex border border-warm-edge rounded overflow-hidden">
      {caption && <b className="px-2.5 grid place-items-center text-[11px] tracking-[.1em] text-ink-soft bg-warm">{caption}</b>}
      {options.map(([v, text], i) => (
        <button key={v} type="button" data-v={v} data-variant="seg" aria-pressed={String(value) === String(v)}
          onClick={() => onChange(v)}
          className={["min-w-11 min-h-10 px-3 font-bold border-l border-warm-edge transition-colors duration-150",
            tone === "drawer" ? "bg-white/65 text-baby-ink hover:bg-white active:bg-white/90" : "bg-paper text-ink hover:bg-warm active:bg-warm-line",
            "aria-pressed:bg-navy aria-pressed:text-white aria-pressed:hover:bg-navy-mid aria-pressed:active:bg-navy-rule", i === 0 && !caption ? "border-l-0" : ""].join(" ")}>
          {text}
        </button>
      ))}
    </div>
  );
}

/** On/off switch (role=switch). */
export function Switch({ checked, onChange, ...rest }) {
  return (
    <button type="button" role="switch" aria-checked={checked} onClick={() => onChange(!checked)} data-variant="switch"
      className="relative w-12 h-7 rounded-full border-0 bg-warm-edge aria-checked:bg-navy transition-colors duration-150 hover:ring-2 hover:ring-link/40"
      {...rest}>
      <span aria-hidden="true" className={"absolute top-[3px] size-[22px] rounded-full bg-white transition-[left] duration-200 " + (checked ? "left-[23px]" : "left-[3px]")} />
    </button>
  );
}
