# NTXP Contacts — front end (React + Tailwind)

Vite + React 18 + Tailwind CSS v4. Builds to `../ntxp_contacts/web/dist` (git-ignored); the Python server serves it
at `/` and `/app/*`. If `dist/` is absent the dependency-free legacy page (`ntxp_contacts/web/index.html`) is served,
so a plain source checkout still works.

```
npm ci
npm test            # vitest: button system, logo fallback, query/edit helpers
npm run build       # → ntxp_contacts/web/dist
npm run dev         # vite on :5173, proxying /api, /assets, /config.js to a server on :8099
```

## Document Engine format (NTXP-DOC-STANDARD 2.1)
Tokens live in `src/index.css` (`:root`, palettes, dark) and are exposed to Tailwind with `@theme inline`, so
`bg-navy`, `text-ink-soft`, `border-warm-edge`… follow palette/dark changes at runtime. Navy band 1.00in, accent fade
0.085in over `#182746`, centred ALL-CAPS title lockup, tag line, navy section bars, warm two-tone rows, centred cells /
left paragraph columns, Open Sans.

## Logo
The page uses the Document Engine's own `ntxp_logo_reversed.png`, served from `/assets` (mounted at deploy time, never
in git or the image): fixed 1.55in zone, 0.82in tall, never recoloured. If the asset is missing **no substitute mark is
drawn** — only a text alternative — and the console says why. The favicon is the engine's `icon_small.png`.

## Buttons
Every clickable control goes through `components/ui/Button.jsx` (`Button`, `IconButton`, `Seg`, `Switch`): rest · hover ·
active · focus-visible (3px ring) · disabled (dimmed, `not-allowed`) · loading (`aria-busy`) · `aria-pressed`.
`md` = 44px, `sm` = 32px, inline pills ≥ 24px. Non-interactive column headers are plain text, not disabled buttons.
`tools/ui_audit.py` enforces all of it in every screen state (table, drawer, settings, report).

## Audit
```
python tools/ui_audit.py http://127.0.0.1:8099 out_dir     # 144 checks incl. axe-core; exit 1 on any failure
NTXP_LOGO_REF=<skill>/ntxp-branded-document-2/assets/ntxp_logo_reversed.png  # also verifies the logo is byte-identical
```
