#!/usr/bin/env python3
"""
build_atlas_html.py — render the Canonical Project Record's plans_atlas section into
NTXP Plans Atlas: a self-contained, offline, animated HTML plan-navigation viewer.

Adapts the "Interactive Drawing Atlas" concept (offline viewer, pan/zoom, discipline
tabs, callout hyperlinks with Back navigation, punctuation-insensitive search) into
NTXP's brand system (same design tokens, fonts, constellation background, reveal and
toast patterns as build_dashboard_html.py — this is meant to read as its sibling
page) and interlinks it with the canonical model: trades/specs/phases/areas navigate
straight to sheets, spec PDFs, the budget page, and Summary QTO rows.

Layout:
  top bar — brand + project chip + "Command Dashboard" pill + global search
  left rail — TRADES / SPECS / PHASES / AREAS concept tabs (the point of the tool:
    navigate by concept fast, not by scrolling a drawing index)
  center — discipline tabs over a sheet grid; clicking a sheet opens the VIEWER
    (pan/zoom, glowing callout hotspots, Back-navigation breadcrumb stack)
  right rail — sheet info, divisions, outbound links grouped by kind, staged/ready
    renders, and two "Stage ..." buttons that queue a render REQUEST only (this
    layer never draws or generates imagery itself; ntxp-pdf-markups-and-redlines and
    construction-scope-visualizer produce it, this just records the ask)

Deterministic rendering only — no reasoning, no pricing, no generation. Stdlib only.
Zero external network requests: sheet images referenced by relative path are inlined
as base64 data URIs when present and reasonably sized, otherwise a branded
placeholder panel renders (sheet number + title on a faint grid) so the atlas is
useful the moment sheets are indexed, images or not.

Two modes: full document (default) or --fragment (body only, styles scoped, no
<html> wrapper — same convention as build_dashboard_html.py).
"""

import argparse
import base64
import html
import json
import math
import mimetypes
import random
import re
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent
sys.path.insert(0, str(HERE))
import atlas_shell  # noqa: E402  (NTXP Document Engine shell: header, page strip, drawers, overlays)
DIVISIONS_FILE = PLUGIN_DIR / "resources" / "masterformat-divisions.json"

DEFAULT_COMPANY = "NTXP"

# Same validated categorical palette as build_dashboard_html.py — fixed order,
# assigned to this project's divisions ascending, never cycled; 9th+ fold to OTHER.
CAT = ["#3f78b5", "#bd6428", "#17948a", "#7e58c2", "#1d7fa8", "#a44e94", "#5563cc", "#b85c6e"]
CAT_OTHER = "#5f6a78"

MAX_INLINE_BYTES = int(2.5 * 1024 * 1024)   # per-file cap for base64 inlining
TOTAL_INLINE_BYTES = 12 * 1024 * 1024        # whole-viewer budget; past it, inline the thumbnail
_inlined = [0]
MAX_WORDS_PER_SHEET = 4000                   # search-index cap per sheet

KIND_LABELS = {
    "detail": "Details", "section": "Sections", "elevation": "Elevations",
    "schedule": "Schedules", "spec": "Specs", "sheet": "Sheet refs",
    "qto": "QTO", "trade": "Trade", "external": "External",
}
GROUP_ORDER = ["detail", "section", "elevation", "schedule", "spec", "sheet", "qto", "trade", "external"]
DISC_PRIORITY = ["G", "C", "A", "S", "M", "E", "P", "FP", "EL", "T", "ID", "L", "SP"]

_NORM_RE = re.compile(r"[^A-Z0-9]+")


def log(msg):
    sys.stderr.write(msg + "\n")


# --------------------------------------------------------------- data helpers

def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception as e:  # noqa: BLE001
        log(f"could not read {path}: {e}")
        return None


def load_division_titles():
    data = load_json(DIVISIONS_FILE) or {}
    return {d["division"]: d["title"] for d in data.get("divisions", [])}


def resolve_section(model_dir, value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return load_json(Path(model_dir) / value) or {}
    return {}


def esc(v):
    return html.escape("" if v is None else str(v))


def norm_txt(s):
    return _NORM_RE.sub("", (s or "").upper())


def sheet_divisions(sheet):
    divs = sheet.get("divisions")
    if isinstance(divs, list) and divs:
        return [str(d) for d in divs if d]
    csi = sheet.get("csi")
    if isinstance(csi, dict) and csi.get("masterformat_division"):
        return [str(csi["masterformat_division"])]
    return []


def div_sort(d):
    try:
        return (int(d), str(d))
    except (ValueError, TypeError):
        return (99, str(d))


def disc_sort_key(d):
    try:
        return (DISC_PRIORITY.index(d), d)
    except ValueError:
        return (len(DISC_PRIORITY), d)


def constellation(n, seed, w=1500, h=1050, link=170, bright=False):
    """Seeded, tileable field of faint interlinked stars — identical technique to
    build_dashboard_html.py so the atlas reads as a sibling page."""
    rng = random.Random(seed)
    pts = [(rng.uniform(0, w), rng.uniform(0, h)) for _ in range(n)]
    a = 0.42 if bright else 0.30
    parts = []
    for i, (x1, y1) in enumerate(pts):
        for x2, y2 in pts[i + 1:]:
            if math.hypot(x2 - x1, y2 - y1) < link:
                parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                             f'stroke="rgba(140,170,215,{0.10 if bright else 0.07})" stroke-width="1"/>')
    for x, y in pts:
        r = rng.uniform(0.7, 1.9)
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="rgba(190,210,240,{a})"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}">{"".join(parts)}</svg>')
    return "data:image/svg+xml," + urllib.parse.quote(svg)


def placeholder_data_uri(sheet_no, title):
    """A branded placeholder panel: sheet number + title in serif on a faint grid —
    used whenever the sheet has no rendered image yet, or the image was too large
    to inline. Returned with explicit pixel dims so the <img> reserves layout
    space instantly (no shift once decoded)."""
    w, h = 1600, 1080
    step = 46
    lines = []
    x = step
    while x < w:
        lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="rgba(150,180,225,.16)" stroke-width="1"/>')
        x += step
    y = step
    while y < h:
        lines.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="rgba(150,180,225,.16)" stroke-width="1"/>')
        y += step

    words = (title or "").split()
    line1, line2 = "", ""
    if words:
        acc = ""
        for wd in words:
            trial = (acc + " " + wd).strip()
            if len(trial) <= 30 or not acc:
                acc = trial
            else:
                break
        line1 = acc
        line2 = (title or "")[len(line1):].strip(" ,-")
        if len(line2) > 34:
            line2 = line2[:31].rsplit(" ", 1)[0] + "…"

    sheet_no_esc = html.escape(sheet_no or "—")
    line1_esc = html.escape(line1)
    line2_esc = html.escape(line2)
    grid_lines = "".join(lines)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect width="{w}" height="{h}" fill="#1c2330"/>'
        f'{grid_lines}'
        f'<rect x="10" y="10" width="{w - 20}" height="{h - 20}" fill="none" '
        f'stroke="rgba(221,229,240,.55)" stroke-width="4"/>'
        f'<rect x="10" y="10" width="{w - 20}" height="76" fill="rgba(79,150,216,.16)"/>'
        f'<text x="34" y="62" font-family="Georgia,serif" font-size="42" fill="#f2f5fa">{sheet_no_esc}</text>'
        f'<text x="{w / 2:.0f}" y="{h / 2 - 8:.0f}" text-anchor="middle" font-family="Georgia,serif" '
        f'font-size="50" fill="#c3cddd">{line1_esc}</text>'
        f'<text x="{w / 2:.0f}" y="{h / 2 + 48:.0f}" text-anchor="middle" '
        f'font-family="sans-serif" font-size="28" fill="#8ea0b8">{line2_esc}</text>'
        f'<text x="{w / 2:.0f}" y="{h - 36:.0f}" text-anchor="middle" font-family="sans-serif" '
        f'font-size="22" letter-spacing="2" fill="#5f7590">SHEET IMAGE NOT YET RENDERED</text>'
        f'</svg>'
    )
    return "data:image/svg+xml," + urllib.parse.quote(svg), w, h


def sheet_image(model_dir, sheet):
    """Inline as base64 when the referenced file exists and is small enough; keep
    the relative path when it exists but is too large; otherwise a placeholder.
    Returns (src, is_placeholder, width, height)."""
    for key in ("image", "thumbnail"):
        rel = sheet.get(key)
        if not rel:
            continue
        p = Path(model_dir) / rel
        try:
            if p.is_file():
                size = p.stat().st_size
                if size <= MAX_INLINE_BYTES and _inlined[0] + size <= TOTAL_INLINE_BYTES:
                    mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
                    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
                    _inlined[0] += size
                    return f"data:{mime};base64,{b64}", False, None, None
        except OSError:
            pass
    uri, w, h = placeholder_data_uri(sheet.get("sheet_no", ""), sheet.get("title", ""))
    return uri, True, w, h


def load_words(model_dir, search_cfg):
    wf = (search_cfg or {}).get("words_file")
    if not wf:
        return {}
    data = load_json(Path(model_dir) / wf)
    return data if isinstance(data, dict) else {}


# --------------------------------------------------------------------- styles

STYLE = """
:root{
  --bg:#0b0f16; --ink:#e8edf4; --muted:#9aa7b8; --faint:#66707f;
  --blue:#4f96d8; --blue-deep:#2f6cae; --gold:#c3cddd; --gold-soft:#dde5f0; --red:#cf5c6b;
  --green:#54c08a; --yellow:#cf8a3a; --neon:#3be08f;
  --line-w:rgba(255,255,255,.08); --line-g:rgba(195,205,221,.28); --line2:rgba(255,255,255,.15);
  --panel:linear-gradient(157deg,#1e2530 0%,#171d27 52%,#11151d 100%);
  --raise:0 1px 0 rgba(255,255,255,.05) inset,0 18px 38px -20px rgba(0,0,0,.9);
  --raise-hi:0 1px 0 rgba(255,255,255,.08) inset,0 24px 52px -18px rgba(0,0,0,.95),0 0 30px -6px rgba(79,150,216,.32);
  --r:14px;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --sans:ui-sans-serif,-apple-system,"Segoe UI",Roboto,Inter,Helvetica,Arial,sans-serif;
  --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
}
*{box-sizing:border-box}
.atl-root{font-family:var(--sans);color:var(--ink);line-height:1.5;background:var(--bg);
  -webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden;min-height:100vh}
.atl-root h1,.atl-root h2,.atl-root h3,.atl-root h4,.atl-root h5{margin:0;font-weight:600;letter-spacing:-.01em}
.atl-root a{color:inherit;text-decoration:none}
.atl-root button{font:inherit;color:inherit;background:none;border:none;text-align:left}
.atl-root [hidden]{display:none!important}
.atl-root button:focus-visible,.atl-root a:focus-visible,.atl-root input:focus-visible{
  outline:2px solid rgba(79,150,216,.85);outline-offset:2px;border-radius:4px}

.atl-bg{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
  background:linear-gradient(118deg,rgba(120,150,195,.05) 0%,transparent 34%,transparent 70%,rgba(60,80,115,.05) 100%),
  radial-gradient(125% 95% at 50% -12%,#151b28 0%,#0b0f16 46%,#05070c 100%)}
.atl-bg::before,.atl-bg::after{content:"";position:absolute;width:60vmax;height:60vmax;border-radius:50%;
  filter:blur(95px);opacity:.11;will-change:transform}
.atl-bg::before{background:radial-gradient(circle,var(--blue),transparent 60%);top:-24vmax;right:-14vmax;animation:adrift1 46s ease-in-out infinite}
.atl-bg::after{background:radial-gradient(circle,#8ea6c9,transparent 60%);bottom:-28vmax;left:-18vmax;animation:adrift2 58s ease-in-out infinite}
@keyframes adrift1{50%{transform:translate(-7vmax,6vmax) scale(1.12)}}
@keyframes adrift2{50%{transform:translate(7vmax,-5vmax) scale(1.06)}}
.atl-stars{position:fixed;inset:-8%;z-index:0;pointer-events:none;background-repeat:repeat;
  mask-image:radial-gradient(120% 100% at 50% 0%,#000 0%,rgba(0,0,0,.35) 75%,transparent 100%)}
.atl-stars.s1{opacity:.5;animation:astar1 240s linear infinite alternate}
.atl-stars.s2{opacity:.32;animation:astar2 160s linear infinite alternate}
@keyframes astar1{to{transform:translate(-70px,42px)}}
@keyframes astar2{to{transform:translate(55px,-38px)}}

.atl-shell{position:relative;z-index:1;display:flex;flex-direction:column;min-height:100vh}

/* ---- top bar ---- */
.atl-nav{position:sticky;top:0;z-index:40;display:flex;gap:14px;flex-wrap:wrap;align-items:center;
  padding:12px 24px;backdrop-filter:blur(13px);
  background:linear-gradient(180deg,rgba(20,23,27,.94),rgba(20,23,27,.7));
  border-bottom:1px solid var(--line-w);box-shadow:0 1px 0 var(--line-g)}
.atl-nav .brand{font:600 15px/1.3 var(--serif);display:flex;align-items:center;gap:10px;white-space:nowrap}
.atl-nav .dot{width:8px;height:8px;border-radius:50%;background:var(--gold);box-shadow:0 0 10px var(--gold);
  animation:apulse 2.8s infinite;flex:0 0 auto}
@keyframes apulse{0%{box-shadow:0 0 0 0 rgba(195,205,221,.5)}70%{box-shadow:0 0 0 9px rgba(195,205,221,0)}100%{box-shadow:0 0 0 0 rgba(195,205,221,0)}}
.chip{display:inline-flex;align-items:center;gap:7px;font:600 12px/1 var(--sans);padding:8px 12px;
  border-radius:999px;border:1px solid var(--line-w);background:var(--panel);box-shadow:var(--raise);color:var(--muted)}
.pill{cursor:pointer;display:inline-flex;align-items:center;gap:8px;font:600 12.5px/1 var(--sans);color:var(--muted);
  padding:9px 15px;border-radius:999px;border:1px solid var(--line-w);background:var(--panel);box-shadow:var(--raise);
  transition:.22s cubic-bezier(.2,.7,.2,1)}
.pill:hover{color:#fff;transform:translateY(-2px);box-shadow:var(--raise),0 0 22px -2px rgba(79,150,216,.6);border-color:rgba(79,150,216,.5)}
.atl-search{position:relative;margin-left:auto;flex:1 1 280px;max-width:420px;min-width:200px}
.atl-search input{width:100%;font:500 13px/1 var(--sans);color:var(--ink);padding:10px 14px;border-radius:11px;
  border:1px solid var(--line-w);background:rgba(255,255,255,.03);box-shadow:var(--raise);outline:none;
  transition:.2s ease}
.atl-search input::placeholder{color:var(--faint)}
.atl-search input:focus{border-color:rgba(79,150,216,.55);box-shadow:var(--raise),0 0 0 3px rgba(79,150,216,.18)}
.sr-panel{position:absolute;top:calc(100% + 8px);left:0;right:0;max-height:64vh;overflow-y:auto;
  border-radius:12px;border:1px solid var(--line2);background:#161b23;box-shadow:0 26px 60px -18px rgba(0,0,0,.85);
  display:none;padding:6px;z-index:50}
.sr-panel.show{display:block}
.sr-group h6{font:700 10px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--faint);
  padding:10px 10px 6px}
.sr-row{display:block;width:100%;padding:8px 10px;border-radius:8px;font-size:13px;color:var(--ink);cursor:pointer}
.sr-row:hover{background:rgba(79,150,216,.12)}
.sr-note{padding:0 10px 6px;font-size:11px;color:var(--faint);font-style:italic}
.sr-sheet{border-top:1px dashed var(--line-w);padding-top:4px;margin-top:4px}
.sr-sheethead{font-weight:600}
.sr-snips{display:flex;flex-wrap:wrap;gap:6px;padding:2px 10px 8px}
.sr-snip{font:600 11px/1 var(--mono);color:var(--blue);background:rgba(79,150,216,.1);
  border:1px solid rgba(79,150,216,.3);padding:4px 8px;border-radius:6px;cursor:pointer}
.sr-snip:hover{background:rgba(79,150,216,.22)}
.sr-empty{padding:14px 10px;color:var(--faint);font-size:12.5px}

/* ---- three-column shell ---- */
.atl-wrap{flex:1;display:grid;grid-template-columns:262px minmax(0,1fr);gap:18px;
  max-width:1440px;margin:0 auto;width:100%;padding:20px 24px 60px;align-items:start}
.atl-wrap.with-right{grid-template-columns:262px minmax(0,1fr) 300px}
@media (max-width:980px){
  .atl-wrap,.atl-wrap.with-right{grid-template-columns:1fr}
  .rail-left{position:static;order:2}
  .atl-center{order:1}
  #rail-right{order:3}
}

/* ---- left concept rail ---- */
.rail-left{position:sticky;top:76px;max-height:calc(100vh - 96px);overflow-y:auto;scrollbar-width:thin;
  display:flex;flex-direction:column;gap:12px;border:1px solid var(--line-w);border-radius:var(--r);
  background:var(--panel);box-shadow:var(--raise);padding:14px}
.rail-tabs{display:flex;gap:4px;flex-wrap:wrap}
.rail-tab{flex:1 1 auto;cursor:pointer;font:700 10.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);background:rgba(255,255,255,.03);border:1px solid var(--line-w);border-radius:8px;
  padding:9px 6px;text-align:center;transition:.2s ease}
.rail-tab:hover{color:#fff}
.rail-tab[aria-selected="true"]{color:#fff;border-color:rgba(79,150,216,.6);
  background:linear-gradient(180deg,var(--blue),var(--blue-deep));box-shadow:0 0 16px -2px rgba(79,150,216,.6)}
.rail-panel{display:none;flex-direction:column;gap:10px}
.rail-panel.active{display:flex}
.rail-list{display:flex;flex-direction:column;gap:4px}
.rail-row{display:flex;align-items:center;gap:9px;padding:9px 10px;border-radius:9px;font-size:12.5px;
  color:var(--muted);cursor:pointer;transition:.16s ease;border:1px solid transparent}
.rail-row:hover{color:#fff;background:rgba(79,150,216,.08)}
.rail-row.active{color:#fff;background:rgba(79,150,216,.14);border-color:rgba(79,150,216,.4)}
.rail-row .sw{width:9px;height:9px;border-radius:3px;flex:0 0 9px}
.rail-row .lbl{flex:1}
.rail-row .cnt{font:700 11px/1 var(--mono);color:var(--faint)}
.rail-row.active .cnt{color:var(--gold-soft)}
.div-details{display:flex;flex-direction:column;gap:8px}
.div-detail{border-top:1px dashed var(--line-w);padding-top:10px}
.div-detail h5{font:700 11px/1 var(--mono);letter-spacing:.06em;color:var(--gold-soft);margin-bottom:8px}
.chiprow{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11px;padding:6px 9px}
.chip.inert{color:var(--faint);cursor:default}
.chip.sheetchip,button.chip,a.chip{cursor:pointer}
.chip.pdfchip{color:var(--gold-soft);border-color:var(--gold)}
.spec-row{border-top:1px dashed var(--line-w);padding-top:10px}
.spec-row:first-child{border-top:none;padding-top:0}
.spec-row.flash,.concept-row.flash,.rail-row.flash{animation:aflash 1.1s ease}
@keyframes aflash{0%,100%{background:transparent}30%{background:rgba(195,205,221,.16)}}
.spec-head{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.spec-head .mono{font:700 12px/1 var(--mono);color:var(--ink)}
.spec-head .sw{width:9px;height:9px;border-radius:3px}
.spec-head .t{font-size:12.5px;color:var(--muted)}
.concept-row{border-top:1px dashed var(--line-w);padding-top:10px}
.concept-row:first-child{border-top:none;padding-top:0}
.concept-row h5{font-size:13px;margin-bottom:6px}
.csum{font-size:12px;color:var(--muted);margin:0 0 8px}
.empty-note{color:var(--faint);font-size:12px;font-style:italic;margin:4px 0}

/* ---- center: discipline tabs + sheet grid ---- */
.atl-center{display:flex;flex-direction:column;gap:16px;min-height:70vh}
.disc-tabs{display:flex;gap:6px;flex-wrap:wrap}
.disc-tab{cursor:pointer;font:600 12px/1 var(--sans);color:var(--muted);background:var(--panel);
  border:1px solid var(--line-w);box-shadow:var(--raise);padding:8px 14px;border-radius:9px;
  display:inline-flex;gap:7px;align-items:center;transition:.2s ease}
.disc-tab:hover{color:#fff;box-shadow:var(--raise),0 0 16px -2px rgba(79,150,216,.5)}
.disc-tab.active{color:#fff;border-color:rgba(79,150,216,.6);
  background:linear-gradient(180deg,var(--blue),var(--blue-deep));box-shadow:0 0 18px -2px rgba(79,150,216,.6)}
.disc-tab .cnt{font:700 11px/1 var(--mono);color:rgba(255,255,255,.7)}
.disc-tab:not(.active) .cnt{color:var(--faint)}

.sheet-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:14px}
.sheet-card{display:flex;flex-direction:column;border:1px solid var(--line-w);border-radius:var(--r);
  background:var(--panel);box-shadow:var(--raise);overflow:hidden;cursor:pointer;transition:.24s cubic-bezier(.2,.7,.2,1)}
.sheet-card:hover{transform:translateY(-4px);border-color:rgba(79,150,216,.45);box-shadow:var(--raise-hi)}
.sheet-card.is-hidden{display:none}
.sheet-card .thumb{aspect-ratio:4/3;overflow:hidden;background:#10141b;display:flex;align-items:center;justify-content:center}
.sheet-card .thumb-img{display:block;width:100%;height:100%;background-size:cover;background-position:center;
  background-repeat:no-repeat;transform:translateZ(0)}
.cardmeta{position:relative;padding:10px 12px 12px;display:flex;flex-direction:column;gap:6px}
.cardmeta .no{font:700 12.5px/1 var(--mono);color:var(--gold-soft)}
.cardmeta .ttl{font-size:12.5px;color:var(--muted);line-height:1.3;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.dots{display:flex;gap:5px;flex-wrap:wrap}
.dots .dot{width:8px;height:8px;border-radius:2px}
.badge-ns{align-self:flex-start;font:600 9.5px/1 var(--mono);letter-spacing:.05em;text-transform:uppercase;
  color:var(--faint);border:1px solid var(--line-w);padding:3px 6px;border-radius:5px}
.empty-grid{grid-column:1/-1;color:var(--faint);font-size:13px;padding:30px 8px;text-align:center}

/* ---- viewer ---- */
.viewer{display:flex;flex-direction:column;gap:12px;height:72vh}
.viewer-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.btn{cursor:pointer;font:600 12.5px/1 var(--sans);padding:10px 16px;border-radius:9px;border:1px solid var(--line-w);
  background:var(--panel);color:var(--muted);transition:.2s}
.btn:hover{color:#fff;box-shadow:0 0 18px -2px rgba(79,150,216,.55);transform:translateY(-1px)}
.btn:disabled{opacity:.35;cursor:default;transform:none;box-shadow:none}
.btn.primary{color:#fff;border-color:rgba(79,150,216,.6);background:linear-gradient(180deg,var(--blue),var(--blue-deep))}
.breadcrumb{display:flex;flex-wrap:wrap;align-items:center;gap:4px;font:600 12px/1 var(--mono);color:var(--faint);flex:1}
.breadcrumb button{color:var(--muted);cursor:pointer;padding:4px 6px;border-radius:6px}
.breadcrumb button:hover{color:#fff;background:rgba(79,150,216,.1)}
.breadcrumb button.cur{color:var(--gold-soft);cursor:default}
.breadcrumb button.cur:hover{background:none}
.v-zoom{display:flex;gap:6px;margin-left:auto}
.v-zoom button{width:36px;height:36px;border-radius:8px;border:1px solid var(--line-w);background:var(--panel);
  color:var(--muted);font-size:15px;cursor:pointer;transition:.2s}
.v-zoom button:hover{color:#fff;box-shadow:0 0 14px -2px rgba(79,150,216,.6)}
.viewer-canvas{position:relative;flex:1;min-height:0;border-radius:var(--r);overflow:hidden;
  border:1px solid var(--line-w);cursor:grab;
  background:
    linear-gradient(rgba(140,170,215,.05) 1px,transparent 1px) 0 0/42px 42px,
    linear-gradient(90deg,rgba(140,170,215,.05) 1px,transparent 1px) 0 0/42px 42px,
    radial-gradient(120% 100% at 50% 0%,#171d27 0%,#10141b 60%,#0b0e14 100%)}
.viewer-canvas.dragging{cursor:grabbing}
#viewer-panels{position:relative;width:100%;height:100%}
.viewer-panel{position:absolute;inset:0;display:none;align-items:center;justify-content:center}
.viewer-panel.active{display:flex}
.stage{position:relative;transform-origin:center center;background-size:contain;
  background-position:center;background-repeat:no-repeat;border-radius:4px;
  box-shadow:0 10px 44px rgba(0,0,0,.55);transform:translateZ(0)}
.viewer-canvas.dragging .stage{transition:none!important}
.hotspots{position:absolute;inset:0}
.hotspot{position:absolute;box-sizing:border-box;border:2px solid var(--blue);border-radius:5px;
  background:rgba(79,150,216,.16);box-shadow:0 0 14px rgba(79,150,216,.55);cursor:pointer;
  display:flex;align-items:flex-end;padding:2px;transition:.18s ease}
.hotspot:hover{background:rgba(79,150,216,.34);box-shadow:0 0 22px rgba(79,150,216,.9);transform:scale(1.03)}
.hotspot.inert{border-color:var(--line-g);background:rgba(195,205,221,.07);box-shadow:none;cursor:default}
.hotspot.inert:hover{transform:none;background:rgba(195,205,221,.12)}
.hs-tag{font:700 9px/1 var(--mono);color:#eef2f8;background:rgba(8,11,16,.72);padding:2px 5px;border-radius:3px;
  white-space:nowrap;pointer-events:none}
.hl-pulse{position:absolute;border:2px solid var(--gold);border-radius:6px;pointer-events:none;
  animation:ahlpulse 1.15s ease-out 2}
@keyframes ahlpulse{0%{box-shadow:0 0 0 0 rgba(195,205,221,.8)}100%{box-shadow:0 0 26px 12px rgba(195,205,221,0)}}
.ph-note{position:absolute;left:12px;bottom:12px;font:600 10px/1 var(--mono);letter-spacing:.04em;color:var(--faint);
  background:rgba(10,14,20,.6);padding:6px 9px;border-radius:6px;pointer-events:none;border:1px solid var(--line-w)}

/* ---- right rail ---- */
#rail-right{display:none;flex-direction:column;gap:14px;position:sticky;top:76px;
  max-height:calc(100vh - 96px);overflow-y:auto;scrollbar-width:thin}
.atl-wrap.with-right #rail-right{display:flex}
.rr-panel{display:none;flex-direction:column;gap:14px;border:1px solid var(--line-w);border-radius:var(--r);
  background:var(--panel);box-shadow:var(--raise);padding:16px}
.rr-panel.active{display:flex}
.rr-head{display:flex;flex-direction:column;gap:3px;border-bottom:1px solid var(--line-g);padding-bottom:10px}
.rr-head .no{font:700 15px/1 var(--mono);color:var(--gold-soft)}
.rr-head .ttl{font:600 15px/1.3 var(--serif);color:var(--ink)}
.rr-block h4{font:700 10.5px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin-bottom:8px}
.inforow{display:flex;justify-content:space-between;gap:10px;font-size:12.5px;padding:5px 0;
  border-bottom:1px solid var(--line-w)}
.inforow:last-child{border-bottom:none}
.inforow .k{color:var(--faint)}
.inforow .v{color:var(--ink);text-align:right}
.linkgroup{margin-bottom:10px}
.linkgroup h5{font:700 10px/1 var(--mono);letter-spacing:.06em;color:var(--muted);margin-bottom:6px}
.linkrow{display:block;width:100%;padding:7px 9px;border-radius:8px;font-size:12px;color:var(--ink);
  cursor:pointer;transition:.16s ease;display:flex;justify-content:space-between;gap:8px}
.linkrow:hover{background:rgba(79,150,216,.1);color:#fff}
.linkrow.inert{color:var(--faint);cursor:default}
.linkrow.inert:hover{background:none}
.linkrow .arrow{color:var(--faint);font:600 11px/1 var(--mono)}
.render-ready{display:flex;align-items:center;gap:10px;padding:7px;border-radius:9px;margin-bottom:6px;
  border:1px solid var(--line-w);cursor:pointer;transition:.18s ease}
.render-ready:hover{border-color:rgba(79,150,216,.5);background:rgba(79,150,216,.06)}
.rr-thumb{display:block;width:44px;height:32px;background-size:cover;background-position:center;
  background-repeat:no-repeat;border-radius:5px;flex:0 0 44px;transform:translateZ(0)}
.render-ready span{font-size:11.5px;color:var(--muted)}
.render-pending{display:flex;align-items:center;gap:8px;font-size:11.5px;color:var(--faint);padding:7px 2px;margin-bottom:4px}
.pulse-dot{width:8px;height:8px;border-radius:50%;background:var(--blue);flex:0 0 8px}
.render-pending.generating .pulse-dot{animation:apulse2 1.3s infinite;background:var(--gold)}
.render-pending.staged .pulse-dot{animation:apulse2 2.2s infinite}
@keyframes apulse2{0%{box-shadow:0 0 0 0 rgba(79,150,216,.55)}70%{box-shadow:0 0 0 7px rgba(79,150,216,0)}100%{box-shadow:0 0 0 0 rgba(79,150,216,0)}}
.rr-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.rr-actions .btn{flex:1;text-align:center;font-size:11.5px;padding:9px 8px}

.stage-queue{border:1px solid var(--line-w);border-radius:var(--r);background:var(--panel);box-shadow:var(--raise);padding:16px}
.stage-queue h4{font:700 10.5px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin-bottom:10px}
.sq-item{display:flex;justify-content:space-between;gap:8px;font-size:12px;padding:8px 0;border-bottom:1px solid var(--line-w)}
.sq-item:last-child{border-bottom:none}
.sq-item .k{color:var(--gold-soft);font:600 11px/1 var(--mono)}
.sq-item .w{color:var(--faint);font-size:10.5px}

/* ---- toast + tooltip ---- */
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,20px);z-index:80;opacity:0;pointer-events:none;
  font:600 12.5px/1.4 var(--sans);color:var(--ink);padding:13px 20px;border-radius:11px;border:1px solid var(--line-g);
  background:linear-gradient(157deg,#2e343e,#23272f);box-shadow:0 18px 50px -12px rgba(0,0,0,.9),0 0 24px -4px rgba(140,175,220,.35);
  transition:.35s cubic-bezier(.2,.7,.2,1);max-width:520px;text-align:center}
.toast.show{opacity:1;transform:translate(-50%,0)}
#tip{position:fixed;z-index:90;pointer-events:none;opacity:0;transition:opacity .15s;
  font:600 11.5px/1.4 var(--sans);color:var(--ink);background:#14171c;border:1px solid var(--line2);
  border-radius:8px;padding:8px 11px;box-shadow:0 10px 30px rgba(0,0,0,.6);max-width:260px}

.reveal{opacity:0;transform:translateY(14px);transition:opacity .55s ease,transform .55s cubic-bezier(.2,.7,.2,1)}
.reveal.in{opacity:1;transform:none}
.is-hidden{display:none!important}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
  .reveal{opacity:1;transform:none}
}
"""

SCRIPT = """
(function(){
  var rm = window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  var root = document.querySelector('.atl-root');

  function fire(el){ el.classList.add('in'); }
  var io = ('IntersectionObserver' in window) && !rm ? new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ fire(e.target); io.unobserve(e.target); } });
  },{threshold:.1}) : null;
  document.querySelectorAll('.reveal').forEach(function(el){ io?io.observe(el):fire(el); });
  setTimeout(function(){ document.querySelectorAll('.reveal:not(.in)').forEach(fire); }, 2600);

  var tip=document.getElementById('tip');
  document.addEventListener('mousemove',function(e){
    var t=e.target.closest('[data-tip]');
    if(t&&tip){ tip.innerHTML=t.getAttribute('data-tip'); tip.style.opacity=1;
      tip.style.left=Math.min(e.clientX+14,window.innerWidth-280)+'px'; tip.style.top=(e.clientY+16)+'px';
    } else if(tip){ tip.style.opacity=0; }
  });

  var toastEl=document.getElementById('toast'), toastT=null;
  function toast(msg){ if(!toastEl)return; toastEl.textContent=msg; toastEl.classList.add('show');
    clearTimeout(toastT); toastT=setTimeout(function(){toastEl.classList.remove('show');},4200); }

  function escHtml(s){ return String(s==null?'':s).replace(/[&<>"']/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function normTxt(s){ return (s||'').toUpperCase().replace(/[^A-Z0-9]+/g,''); }
  function cssEsc(s){ return (window.CSS && CSS.escape) ? CSS.escape(s) : String(s).replace(/["\\\\]/g,'\\\\$&'); }

  // ---------------------------------------------------------------- data
  var DATA = {items: [], sheetMeta: {}};
  var dataEl = document.getElementById('atlas-search-data');
  if(dataEl){ try{ DATA = JSON.parse(dataEl.textContent); }catch(e){} }

  // ---------------------------------------------------------------- rail tabs
  function activateRailTab(tab){
    document.querySelectorAll('.rail-tab').forEach(function(t){
      t.setAttribute('aria-selected', t.getAttribute('data-tab')===tab ? 'true':'false'); });
    document.querySelectorAll('.rail-panel').forEach(function(p){
      p.classList.toggle('active', p.getAttribute('data-tab')===tab); });
  }
  document.querySelectorAll('.rail-tab').forEach(function(t){
    t.addEventListener('click', function(){ activateRailTab(t.getAttribute('data-tab')); });
  });

  // ---------------------------------------------------------------- filters
  var currentDiv='all', currentDisc='all';
  function applyFilters(){
    document.querySelectorAll('.sheet-card').forEach(function(c){
      var divs=(c.getAttribute('data-divs')||'').split(',').filter(Boolean);
      var okDiv = currentDiv==='all' || divs.indexOf(currentDiv)>-1;
      var okDisc = currentDisc==='all' || c.getAttribute('data-disc')===currentDisc;
      c.classList.toggle('is-hidden', !(okDiv && okDisc));
    });
  }
  function selectDivision(d){
    currentDiv = (currentDiv===d && d!=='all') ? 'all' : d;
    document.querySelectorAll('.rail-row[data-action=\\"filter-div\\"]').forEach(function(r){
      r.classList.toggle('active', r.getAttribute('data-div')===currentDiv); });
    document.querySelectorAll('.div-detail').forEach(function(p){
      p.hidden = p.getAttribute('data-division')!==currentDiv; });
    applyFilters();
  }
  document.querySelectorAll('.rail-row[data-action=\\"filter-div\\"]').forEach(function(r){
    r.addEventListener('click', function(){ selectDivision(r.getAttribute('data-div')); });
  });
  document.querySelectorAll('.disc-tab').forEach(function(t){
    t.addEventListener('click', function(){
      currentDisc = t.getAttribute('data-disc');
      document.querySelectorAll('.disc-tab').forEach(function(x){ x.classList.toggle('active', x===t); });
      applyFilters();
    });
  });

  function gotoDivision(d){ activateRailTab('trades'); selectDivision(d);
    var row=document.querySelector('.rail-row[data-div=\\"'+cssEsc(d)+'\\"]');
    if(row) row.scrollIntoView({block:'center', behavior: rm?'auto':'smooth'});
  }
  function gotoSpec(sec){
    activateRailTab('specs');
    var el=document.querySelector('.spec-row[data-spec=\\"'+cssEsc(sec)+'\\"]');
    if(el){ el.scrollIntoView({block:'center', behavior: rm?'auto':'smooth'});
      el.classList.add('flash'); setTimeout(function(){el.classList.remove('flash');},1150); }
  }
  function gotoConcept(tab, target){
    if(tab==='trades'){ gotoDivision(target); return; }
    activateRailTab(tab);
    var el=document.querySelector('.concept-row[data-key=\\"'+cssEsc(target)+'\\"]');
    if(el){ el.scrollIntoView({block:'center', behavior: rm?'auto':'smooth'});
      el.classList.add('flash'); setTimeout(function(){el.classList.remove('flash');},1150); }
  }

  // ---------------------------------------------------------------- viewer
  var sheetGrid=document.getElementById('sheet-grid'), discTabs=document.getElementById('disc-tabs'),
      viewerEl=document.getElementById('viewer'), wrap=document.getElementById('atl-wrap'),
      crumbEl=document.getElementById('v-crumb'), backBtn=document.getElementById('v-back'),
      canvas=document.getElementById('viewer-canvas');
  var stack=[], panState={};

  function stageOf(id){ var p=document.getElementById('vp-'+id); return p ? p.querySelector('.stage') : null; }
  function applyTransform(id){
    var st=panState[id]||{x:0,y:0,s:1}; panState[id]=st;
    var stage=stageOf(id);
    if(stage) stage.style.transform='translate('+st.x+'px,'+st.y+'px) scale('+st.s+') translateZ(0)';
  }
  function renderCrumb(){
    if(!crumbEl) return;
    crumbEl.innerHTML = stack.map(function(id,i){
      var meta=DATA.sheetMeta[id]||{no:id};
      var cls = i===stack.length-1 ? 'cur' : '';
      return '<button type=\\"button\\" class=\\"'+cls+'\\" data-crumb-idx=\\"'+i+'\\">'+escHtml(meta.no)+'</button>'
        + (i<stack.length-1 ? '<span>&nbsp;\\u203a&nbsp;</span>' : '');
    }).join('');
    if(backBtn) backBtn.disabled = stack.length<=1;
  }
  function showSheetOnly(id){
    document.querySelectorAll('.viewer-panel').forEach(function(p){ p.classList.toggle('active', p.id==='vp-'+id); });
    document.querySelectorAll('.rr-panel').forEach(function(p){ p.classList.toggle('active', p.id==='rr-'+id); });
    applyTransform(id);
    renderCrumb();
  }
  function openSheet(id, opts){
    opts = opts||{};
    if(!document.getElementById('vp-'+id)) return;
    if(opts.push && stack.length && stack[stack.length-1]!==id){ stack.push(id); }
    else if(!opts.push){ stack=[id]; }
    else if(!stack.length){ stack=[id]; }
    sheetGrid.hidden=true; discTabs.hidden=true; viewerEl.hidden=false;
    if(wrap) wrap.classList.add('with-right');
    showSheetOnly(id);
    if(opts.toBox) pulseHighlight(id, opts.toBox);
  }
  function closeViewer(){
    viewerEl.hidden=true; sheetGrid.hidden=false; discTabs.hidden=false;
    if(wrap) wrap.classList.remove('with-right');
    stack=[];
  }
  function pulseHighlight(id, box){
    var panel=document.getElementById('vp-'+id); if(!panel) return;
    var hs=panel.querySelector('.hotspots'); if(!hs) return;
    var el=document.createElement('div'); el.className='hl-pulse';
    el.style.left=(box[0]*100)+'%'; el.style.top=(box[1]*100)+'%';
    el.style.width=Math.max((box[2]-box[0])*100,1.2)+'%'; el.style.height=Math.max((box[3]-box[1])*100,1.2)+'%';
    hs.appendChild(el);
    setTimeout(function(){ if(el.parentNode) el.parentNode.removeChild(el); }, rm?400:2400);
  }

  document.querySelectorAll('.sheet-card').forEach(function(c){
    c.addEventListener('click', function(){ openSheet(c.getAttribute('data-sheet'), {push:false}); });
  });
  document.addEventListener('click', function(e){
    var chip=e.target.closest('.sheetchip[data-open-sheet]');
    if(chip){ openSheet(chip.getAttribute('data-open-sheet'), {push:false}); return; }
    var spec=e.target.closest('[data-goto-spec]');
    if(spec){ gotoSpec(spec.getAttribute('data-goto-spec')); return; }
  });
  if(crumbEl) crumbEl.addEventListener('click', function(e){
    var b=e.target.closest('[data-crumb-idx]'); if(!b) return;
    var idx=parseInt(b.getAttribute('data-crumb-idx'),10);
    stack=stack.slice(0, idx+1); showSheetOnly(stack[stack.length-1]);
  });
  if(backBtn) backBtn.addEventListener('click', function(){
    if(stack.length>1){ stack.pop(); showSheetOnly(stack[stack.length-1]); }
  });
  var closeBtn=document.getElementById('v-close');
  if(closeBtn) closeBtn.addEventListener('click', closeViewer);
  document.addEventListener('keydown', function(e){
    if(e.key==='Escape' && viewerEl && !viewerEl.hidden) closeViewer();
  });

  // hotspot / outbound-link navigation (pushes onto the back-stack)
  document.addEventListener('click', function(e){
    var hs=e.target.closest('.hotspot[data-nav-sheet]');
    if(hs){
      var tb=hs.getAttribute('data-to-box');
      openSheet(hs.getAttribute('data-nav-sheet'), {push:true, toBox: tb ? tb.split(',').map(Number) : null});
      return;
    }
    var lr=e.target.closest('.linkrow[data-open-sheet]');
    if(lr){ openSheet(lr.getAttribute('data-open-sheet'), {push:true}); return; }
    var dc=e.target.closest('[data-goto-div]');
    if(dc){ gotoDivision(dc.getAttribute('data-goto-div')); return; }
  });

  // ---------------------------------------------------------------- pan / zoom
  var scaleMin=0.4, scaleMax=6, drag=null;
  if(canvas){
    canvas.addEventListener('pointerdown', function(e){
      if(e.target.closest('.hotspot')) return;   // let hotspot clicks through untouched
      var active=document.querySelector('.viewer-panel.active'); if(!active) return;
      var id=active.getAttribute('data-sheet'); var st=panState[id]||{x:0,y:0,s:1}; panState[id]=st;
      drag={id:id, sx:e.clientX, sy:e.clientY, ox:st.x, oy:st.y};
      canvas.classList.add('dragging');
      try{ canvas.setPointerCapture(e.pointerId); }catch(err){}
    });
    canvas.addEventListener('pointermove', function(e){
      if(!drag) return;
      var st=panState[drag.id];
      st.x = drag.ox + (e.clientX - drag.sx);
      st.y = drag.oy + (e.clientY - drag.sy);
      applyTransform(drag.id);
    });
    function endDrag(){ drag=null; canvas.classList.remove('dragging'); }
    canvas.addEventListener('pointerup', endDrag);
    canvas.addEventListener('pointerleave', endDrag);
    canvas.addEventListener('wheel', function(e){
      var active=document.querySelector('.viewer-panel.active'); if(!active) return;
      e.preventDefault();
      var id=active.getAttribute('data-sheet'); var st=panState[id]||{x:0,y:0,s:1}; panState[id]=st;
      st.s = Math.min(scaleMax, Math.max(scaleMin, st.s * (e.deltaY<0 ? 1.12 : 1/1.12)));
      applyTransform(id);
    }, {passive:false});
  }
  document.querySelectorAll('.v-zoom button').forEach(function(b){
    b.addEventListener('click', function(){
      var active=document.querySelector('.viewer-panel.active'); if(!active) return;
      var id=active.getAttribute('data-sheet'); var st=panState[id]||{x:0,y:0,s:1}; panState[id]=st;
      var act=b.getAttribute('data-zoom');
      if(act==='in') st.s=Math.min(scaleMax, st.s*1.25);
      else if(act==='out') st.s=Math.max(scaleMin, st.s/1.25);
      else { st.s=1; st.x=0; st.y=0; }
      applyTransform(id);
    });
  });

  // ---------------------------------------------------------------- stage queue
  function loadQueue(){ try{ return JSON.parse(localStorage.getItem('ntxpAtlasStageQueue')||'[]'); }catch(e){ return []; } }
  function saveQueue(q){ try{ localStorage.setItem('ntxpAtlasStageQueue', JSON.stringify(q)); }catch(e){} }
  function renderQueue(){
    var el=document.getElementById('stage-queue-list'); if(!el) return;
    var q=loadQueue();
    if(!q.length){ el.innerHTML='<p class=\\"empty-note\\">No staged requests yet.</p>'; return; }
    el.innerHTML = q.slice(-8).reverse().map(function(it){
      var meta=DATA.sheetMeta[it.sheet]||{no:it.sheet};
      var kindLabel = it.kind==='phase_image' ? 'Phase image' : 'Markup';
      return '<div class=\\"sq-item\\"><span><span class=\\"k\\">'+escHtml(meta.no)+'</span> — '+kindLabel+'</span>'
        + '<span class=\\"w\\">staged</span></div>';
    }).join('');
  }
  document.addEventListener('click', function(e){
    var b=e.target.closest('.stagebtn[data-stage-kind]'); if(!b) return;
    var kind=b.getAttribute('data-stage-kind'), sheet=b.getAttribute('data-sheet');
    var q=loadQueue(); q.push({sheet:sheet, kind:kind, ts:new Date().toISOString()}); saveQueue(q); renderQueue();
    toast(kind==='phase_image'
      ? 'Staged for generation \\u2014 construction-scope-visualizer will render this phase view for approval.'
      : 'Staged for generation \\u2014 ntxp-pdf-markups-and-redlines will produce this markup for approval.');
  });
  renderQueue();

  // ---------------------------------------------------------------- search
  var searchInput=document.getElementById('atl-search'), resultsEl=document.getElementById('atl-search-results');
  function runSearch(q){
    var nq=normTxt(q);
    if(!nq){ resultsEl.classList.remove('show'); resultsEl.innerHTML=''; return; }
    var sheets=[], concepts=[], specs=[], words=[];
    DATA.items.forEach(function(it){
      if(!it.norm || it.norm.indexOf(nq)===-1) return;
      if(it.type==='sheet') sheets.push(it);
      else if(it.type==='concept') concepts.push(it);
      else if(it.type==='spec') specs.push(it);
      else if(it.type==='word') words.push(it);
    });
    var out='';
    if(sheets.length||concepts.length||specs.length){
      out+='<div class=\\"sr-group\\"><h6>Sheets &amp; Concepts</h6>';
      sheets.slice(0,8).forEach(function(it){
        out+='<button type=\\"button\\" class=\\"sr-row\\" data-open-sheet=\\"'+it.id+'\\">'+escHtml(it.label)+'</button>';
        if(it.searchable===false) out+='<div class=\\"sr-note\\">'+escHtml(it.id)+' \\u2014 drawing text not indexed on this sheet</div>';
      });
      concepts.slice(0,6).forEach(function(it){
        out+='<button type=\\"button\\" class=\\"sr-row\\" data-goto-concept=\\"'+it.tab+'\\" data-target=\\"'+escHtml(it.target)+'\\">'+escHtml(it.label)+'</button>';
      });
      specs.slice(0,6).forEach(function(it){
        out+='<button type=\\"button\\" class=\\"sr-row\\" data-goto-spec=\\"'+escHtml(it.section)+'\\">'+escHtml(it.label)+'</button>';
      });
      out+='</div>';
    }
    if(words.length){
      var bySheet={};
      words.forEach(function(w){ (bySheet[w.id]=bySheet[w.id]||[]).push(w); });
      out+='<div class=\\"sr-group\\"><h6>In Drawings</h6>';
      Object.keys(bySheet).slice(0,10).forEach(function(sid){
        var meta=DATA.sheetMeta[sid]||{no:sid,title:''};
        out+='<div class=\\"sr-sheet\\"><button type=\\"button\\" class=\\"sr-row sr-sheethead\\" data-open-sheet=\\"'+sid+'\\">'
          +escHtml(meta.no+' \\u2014 '+meta.title)+'</button><div class=\\"sr-snips\\">';
        bySheet[sid].slice(0,6).forEach(function(w){
          var boxAttr = w.box ? ' data-box=\\"'+w.box.join(',')+'\\"' : '';
          out+='<button type=\\"button\\" class=\\"sr-snip\\" data-open-sheet=\\"'+sid+'\\"'+boxAttr+'>'+escHtml(w.label)+'</button>';
        });
        out+='</div></div>';
      });
      out+='</div>';
    }
    resultsEl.innerHTML = out || '<div class=\\"sr-empty\\">No matches. Try a sheet number, division, or spec section.</div>';
    resultsEl.classList.add('show');
  }
  if(searchInput){
    searchInput.addEventListener('input', function(){ runSearch(searchInput.value); });
    searchInput.addEventListener('focus', function(){ if(searchInput.value) runSearch(searchInput.value); });
    searchInput.addEventListener('keydown', function(e){
      if(e.key==='Escape'){ resultsEl.classList.remove('show'); searchInput.blur(); }
      if(e.key==='Enter'){
        var first=resultsEl.querySelector('.sr-row,.sr-snip'); if(first) first.click();
      }
    });
    document.addEventListener('click', function(e){
      if(!e.target.closest('.atl-search')) resultsEl.classList.remove('show');
    });
  }
  if(resultsEl) resultsEl.addEventListener('click', function(e){
    var sn=e.target.closest('.sr-snip[data-open-sheet]');
    if(sn){ var box=sn.getAttribute('data-box'); openSheet(sn.getAttribute('data-open-sheet'), {push:false,
      toBox: box ? box.split(',').map(Number) : null}); resultsEl.classList.remove('show'); return; }
    var row=e.target.closest('.sr-row');
    if(!row) return;
    if(row.hasAttribute('data-open-sheet')){ openSheet(row.getAttribute('data-open-sheet'), {push:false}); }
    else if(row.hasAttribute('data-goto-spec')){ gotoSpec(row.getAttribute('data-goto-spec')); }
    else if(row.hasAttribute('data-goto-concept')){ gotoConcept(row.getAttribute('data-goto-concept'), row.getAttribute('data-target')); }
    resultsEl.classList.remove('show');
  });
  /* Deep links from the project knowledge base: plans-atlas.html#sheet=<sheet_id>[&box=x0,y0,x1,y1] */
  function openFromHash(){
    var m=/[#&]sheet=([^&]+)(?:&box=([-0-9.,]+))?/.exec(location.hash||'');
    if(!m) return;
    var id; try{ id=decodeURIComponent(m[1]); }catch(e){ id=m[1]; }
    openSheet(id, {push:false, toBox: m[2] ? m[2].split(',').map(Number) : null});
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();
})();
"""


# ------------------------------------------------------------------ builders

def divtag_chip(d, colors, titles):
    return (f'<button type="button" class="chip divchip" data-goto-div="{esc(d)}" '
            f'title="Open in Trades — Div {esc(d)}"><span class="sw" style="background:{colors.get(d, CAT_OTHER)}">'
            f'</span>Div {esc(d)} · {esc(titles.get(d, ""))}</button>')


def sheet_card_html(sheet, colors, titles):
    sid = sheet["sheet_id"]
    no = sheet.get("sheet_no", sid)
    title = sheet.get("title", "")
    divs = sheet_divisions(sheet)
    dot_spans = "".join(
        f'<span class="dot" style="background:{colors.get(d, CAT_OTHER)}" '
        f'data-tip="Div {esc(d)} · {esc(titles.get(d, ""))}"></span>' for d in divs
    ) or '<span class="dot" style="background:var(--faint)" data-tip="General / no division tagged"></span>'
    thumb_src, _is_ph, _w, _h = sheet.get("_thumb")
    thumb_src_esc = esc(thumb_src)
    badge = ('<span class="badge-ns" data-tip="Drawing text not indexed on this sheet">not searchable</span>'
             if sheet.get("searchable") is False else "")
    disc = esc(sheet.get("discipline", "") or "")
    divs_attr = esc(",".join(divs))
    # A CSS background-image div, not <img>, renders reliably under forced
    # prefers-reduced-motion emulation for data-URI SVGs in some browsers.
    return f'''<button type="button" class="sheet-card reveal" data-sheet="{esc(sid)}" data-disc="{disc}" data-divs="{divs_attr}">
      <span class="thumb"><span class="thumb-img" role="img" aria-label="{esc(title)}"
        style="background-image:url('{thumb_src_esc}')"></span></span>
      <span class="cardmeta"><span class="no">{esc(no)}</span><span class="ttl">{esc(title)}</span>
        <span class="dots">{dot_spans}</span>{badge}</span>
    </button>'''


def hotspot_html(link):
    box = link.get("from_box")
    if not (isinstance(box, list) and len(box) == 4):
        return ""
    x0, y0, x1, y1 = (float(v) for v in box)
    left, top = x0 * 100, y0 * 100
    w, h = max((x1 - x0) * 100, 1.4), max((y1 - y0) * 100, 1.4)
    kind = link.get("kind", "sheet")
    tag = link.get("tag") or KIND_LABELS.get(kind, kind).rstrip("s")
    to_sheet = link.get("to_sheet")
    to_href = link.get("to_href")
    to_box = link.get("to_box")
    pos_style = f'left:{left:.2f}%;top:{top:.2f}%;width:{w:.2f}%;height:{h:.2f}%'
    tip = f"{esc(KIND_LABELS.get(kind, kind.title()))} · {esc(tag)}"
    tag_esc = esc(tag)
    if to_sheet:
        tobox_attr = (f' data-to-box="{",".join(str(v) for v in to_box)}"'
                      if isinstance(to_box, list) and len(to_box) == 4 else "")
        return (f'<button type="button" class="hotspot" style="{pos_style}" data-nav-sheet="{esc(to_sheet)}"'
                f'{tobox_attr} data-tip="{tip}"><span class="hs-tag">{tag_esc}</span></button>')
    if to_href:
        return (f'<a class="hotspot" href="{esc(to_href)}" target="_blank" rel="noopener" style="{pos_style}" '
                f'data-tip="{tip}"><span class="hs-tag">{tag_esc}</span></a>')
    inert_tip = tip + " — carried in the canonical record"
    return (f'<span class="hotspot inert" style="{pos_style}" data-tip="{inert_tip}" '
            f'title="carried in the canonical record"><span class="hs-tag">{tag_esc}</span></span>')


def viewer_panel_html(sheet, links_by_from):
    sid = sheet["sheet_id"]
    src, is_ph, w, h = sheet.get("_thumb")
    src_esc = esc(src)
    if is_ph and w and h:
        ar = w / h
    else:
        wi, hi = sheet.get("width_in"), sheet.get("height_in")
        ar = (wi / hi) if isinstance(wi, (int, float)) and isinstance(hi, (int, float)) and hi else 1.5
    # width = min(max-width, max-height * aspect-ratio) reproduces object-fit:contain
    # in pure CSS, so the stage box exactly matches the rendered image — no letterbox
    # gap, so hotspot percentages (children of .stage) line up precisely.
    stage_style = f'aspect-ratio:{ar:.6g};width:min(70vw,960px,calc(64vh * {ar:.6g}));background-image:url(\'{src_esc}\')'
    hs = "".join(hotspot_html(l) for l in links_by_from.get(sid, []))
    ph_note = '<div class="ph-note">PLACEHOLDER · sheet image not yet rendered into the atlas</div>' if is_ph else ""
    return f'''<div class="viewer-panel" id="vp-{esc(sid)}" data-sheet="{esc(sid)}">
      <div class="stage" id="stage-{esc(sid)}" style="{stage_style}" role="img" aria-label="{esc(sheet.get("title", ""))}">
        <div class="hotspots">{hs}</div>
      </div>{ph_note}
    </div>'''


def render_chip_html(r):
    status = r.get("status", "staged")
    kind = r.get("kind", "markup")
    label = esc(kind.replace("_", " ").title())
    if status == "ready" and (r.get("output") or r.get("thumbnail")):
        src = r.get("thumbnail") or r.get("output")
        href = r.get("output") or src
        return (f'<a class="render-ready" href="{esc(href)}" target="_blank" rel="noopener" '
                f'data-tip="{esc(r.get("request", ""))}">'
                f'<span class="rr-thumb" role="img" aria-label="{label} thumbnail" '
                f'style="background-image:url(\'{esc(src)}\')"></span>'
                f'<span>{label} · ready</span></a>')
    dot_cls = "generating" if status == "generating" else "staged"
    return (f'<div class="render-pending {dot_cls}" data-tip="{esc(r.get("request", ""))}">'
            f'<span class="pulse-dot"></span>{label} · {esc(status)}</div>')


def rail_right_panel_html(sheet, colors, links_by_from, renders_by_sheet):
    sid = sheet["sheet_id"]
    divs = sheet_divisions(sheet)
    div_chip_html = "".join(f'<button type="button" class="chip divchip" data-goto-div="{esc(d)}" '
                             f'title="Open in Trades — Div {esc(d)}"><span class="sw" '
                             f'style="background:{colors.get(d, CAT_OTHER)}"></span>{esc(d)}</button>' for d in divs)
    div_chip_html = div_chip_html or '<span class="chip inert">General</span>'

    rows = []
    def add_row(label, value):
        if value:
            rows.append(f'<div class="inforow"><span class="k">{esc(label)}</span><span class="v">{esc(value)}</span></div>')

    add_row("Sheet", sheet.get("sheet_no"))
    add_row("Revision", sheet.get("revision"))
    add_row("Scale", sheet.get("declared_scale"))
    size = None
    if isinstance(sheet.get("width_in"), (int, float)) and isinstance(sheet.get("height_in"), (int, float)):
        size = f'{sheet["width_in"]:g}" x {sheet["height_in"]:g}"'
    add_row("Sheet size", size)
    src_bits = [b for b in [sheet.get("source_doc"), (f'p.{sheet["page"]}' if sheet.get("page") else "")] if b]
    add_row("Source", " · ".join(src_bits))
    info_html = "".join(rows) or '<div class="inforow"><span class="v" style="color:var(--faint)">No sheet metadata captured yet.</span></div>'

    groups = {}
    for l in links_by_from.get(sid, []):
        groups.setdefault(l.get("kind", "external"), []).append(l)
    group_blocks = []
    for k in GROUP_ORDER:
        items = groups.get(k)
        if not items:
            continue
        link_rows = []
        for l in items:
            tag = esc(l.get("tag") or l.get("to_sheet") or l.get("to_spec_section") or "link")
            if l.get("to_sheet"):
                link_rows.append(f'<button type="button" class="linkrow" data-open-sheet="{esc(l["to_sheet"])}">'
                                  f'{tag}<span class="arrow">→ {esc(l["to_sheet"])}</span></button>')
            elif l.get("to_href"):
                link_rows.append(f'<a class="linkrow" href="{esc(l["to_href"])}" target="_blank" rel="noopener">'
                                  f'{tag}<span class="arrow">↗</span></a>')
            else:
                link_rows.append(f'<span class="linkrow inert" title="carried in the canonical record">{tag}</span>')
        group_blocks.append(f'<div class="linkgroup"><h5>{esc(KIND_LABELS.get(k, k.title()))}</h5>{"".join(link_rows)}</div>')
    links_html = "".join(group_blocks) or '<p class="empty-note">No outbound links captured for this sheet yet.</p>'

    renders_html = "".join(render_chip_html(r) for r in renders_by_sheet.get(sid, [])) \
        or '<p class="empty-note">No render requests staged for this sheet yet.</p>'

    sid_esc = esc(sid)
    return f'''<div class="rr-panel" id="rr-{sid_esc}" data-sheet="{sid_esc}">
      <div class="rr-head"><span class="no">{esc(sheet.get("sheet_no", sid))}</span>
        <span class="ttl">{esc(sheet.get("title", ""))}</span></div>
      <div class="rr-block"><h4>Sheet Info</h4>{info_html}</div>
      <div class="rr-block"><h4>Divisions</h4><div class="chiprow">{div_chip_html}</div></div>
      <div class="rr-block"><h4>Outbound Links</h4>{links_html}</div>
      <div class="rr-block"><h4>Renders</h4>{renders_html}
        <div class="rr-actions">
          <button type="button" class="btn stagebtn" data-stage-kind="markup" data-sheet="{sid_esc}">Stage markup</button>
          <button type="button" class="btn stagebtn" data-stage-kind="phase_image" data-sheet="{sid_esc}">Stage phase image</button>
        </div>
      </div>
    </div>'''


def trades_tab_html(trades, colors, titles, total_sheets):
    if not trades:
        return ('<p class="empty-note">No trade index carried yet — build the atlas once trades and '
                'the Summary QTO are linked.</p>')
    rows = ['<button type="button" class="rail-row active" data-action="filter-div" data-div="all">'
            f'<span class="lbl">All divisions</span><span class="cnt">{total_sheets}</span></button>']
    details = []
    for t in sorted(trades, key=lambda x: div_sort(x.get("division", "99"))):
        d = str(t.get("division", "99"))
        label = t.get("label") or titles.get(d, f"Division {d}")
        sheet_ids = t.get("sheet_ids") or []
        rows.append(f'''<button type="button" class="rail-row" data-action="filter-div" data-div="{esc(d)}">
          <span class="sw" style="background:{colors.get(d, CAT_OTHER)}"></span>
          <span class="lbl">Div {esc(d)} · {esc(label)}</span><span class="cnt">{len(sheet_ids)}</span></button>''')
        chips = []
        href = t.get("trade_href")
        if href:
            chips.append(f'<a class="chip" href="{esc(href)}" target="_blank" rel="noopener">Budget page</a>')
        else:
            chips.append('<span class="chip inert" title="carried in the canonical record">Budget page</span>')
        tk = t.get("takeoff_ids") or []
        qto_tip = esc(", ".join(tk)) if tk else "carried in the canonical record"
        chips.append(f'<span class="chip inert" title="{qto_tip}">Summary QTO rows'
                     f'{(" · " + str(len(tk))) if tk else ""}</span>')
        for sec in (t.get("spec_sections") or []):
            chips.append(f'<button type="button" class="chip" data-goto-spec="{esc(sec)}">{esc(sec)}</button>')
        sheet_chips = "".join(f'<button type="button" class="chip sheetchip" data-open-sheet="{esc(s)}">{esc(s)}</button>'
                               for s in sheet_ids) or '<span class="empty-note">No sheets tagged yet.</span>'
        details.append(f'''<div class="div-detail" id="dd-{esc(d)}" data-division="{esc(d)}" hidden>
          <h5>Div {esc(d)} · {esc(label)}</h5>
          <div class="chiprow">{"".join(chips)}</div>
          <div class="chiprow" style="margin-top:8px">{sheet_chips}</div>
        </div>''')
    return f'<div class="rail-list">{"".join(rows)}</div><div class="div-details">{"".join(details)}</div>'


def specs_tab_html(specs, colors):
    if not specs:
        return '<p class="empty-note">No spec index carried yet — run specs-skill to interlink per-section PDFs.</p>'
    rows = []
    for s in sorted(specs, key=lambda x: x.get("section", "")):
        sec, d = s.get("section", ""), s.get("division", "")
        pdf = s.get("pdf")
        pdf_chip = (f'<a class="chip pdfchip" href="{esc(pdf)}" target="_blank" rel="noopener">Open PDF ↗</a>' if pdf
                    else '<span class="chip inert" title="carried in the canonical record">PDF pending</span>')
        sheet_chips = "".join(f'<button type="button" class="chip sheetchip" data-open-sheet="{esc(x)}">{esc(x)}</button>'
                               for x in (s.get("sheet_ids") or []))
        rows.append(f'''<div class="spec-row" data-spec="{esc(sec)}">
          <div class="spec-head"><span class="mono">{esc(sec)}</span>
            <span class="sw" style="background:{colors.get(d, CAT_OTHER)}"></span>
            <span class="t">{esc(s.get("title", ""))}</span></div>
          <div class="chiprow">{pdf_chip}{sheet_chips}</div></div>''')
    return f'<div class="rail-list specs">{"".join(rows)}</div>'


def phases_tab_html(phases):
    if not phases:
        return '<p class="empty-note">No phase index carried yet.</p>'
    rows = []
    for p in phases:
        nm = p.get("phase", "")
        chips = "".join(f'<button type="button" class="chip sheetchip" data-open-sheet="{esc(x)}">{esc(x)}</button>'
                         for x in (p.get("sheet_ids") or [])) or '<span class="empty-note">No sheets tagged yet.</span>'
        rows.append(f'''<div class="concept-row" data-key="{esc(nm)}"><h5>{esc(nm)}</h5>
          <p class="csum">{esc(p.get("summary", ""))}</p><div class="chiprow">{chips}</div></div>''')
    return f'<div class="rail-list">{"".join(rows)}</div>'


def areas_tab_html(areas):
    if not areas:
        return '<p class="empty-note">No area index carried yet.</p>'
    rows = []
    for a in areas:
        nm = a.get("area", "")
        chips = "".join(f'<button type="button" class="chip sheetchip" data-open-sheet="{esc(x)}">{esc(x)}</button>'
                         for x in (a.get("sheet_ids") or [])) or '<span class="empty-note">No sheets tagged yet.</span>'
        rows.append(f'''<div class="concept-row" data-key="{esc(nm)}"><h5>{esc(nm)}</h5>
          <div class="chiprow">{chips}</div></div>''')
    return f'<div class="rail-list">{"".join(rows)}</div>'


def discipline_tabs_html(sheets):
    discs = sorted({(s.get("discipline") or "").strip() for s in sheets if s.get("discipline")}, key=disc_sort_key)
    btns = [f'<button type="button" class="disc-tab active" data-disc="all">All<span class="cnt">{len(sheets)}</span></button>']
    for d in discs:
        n = sum(1 for s in sheets if (s.get("discipline") or "").strip() == d)
        btns.append(f'<button type="button" class="disc-tab" data-disc="{esc(d)}">{esc(d)}<span class="cnt">{n}</span></button>')
    return "".join(btns)


def build_search_payload(sheets, concepts, words_by_sheet):
    items = []
    sheet_meta = {}
    for s in sheets:
        sid = s["sheet_id"]
        no, title = s.get("sheet_no", sid), s.get("title", "")
        sheet_meta[sid] = {"no": no, "title": title}
        label = f'{no} — {title}' if title else no
        items.append({"type": "sheet", "id": sid, "label": label, "norm": norm_txt(f"{no} {title}"),
                      "searchable": s.get("searchable", True) is not False})
    for t in concepts.get("trades", []) or []:
        d = t.get("division", "")
        label = f'Div {d} · {t.get("label", "")}'
        items.append({"type": "concept", "tab": "trades", "target": d, "label": label, "norm": norm_txt(label)})
    for p in concepts.get("phases", []) or []:
        nm = p.get("phase", "")
        items.append({"type": "concept", "tab": "phases", "target": nm, "label": nm, "norm": norm_txt(nm)})
    for a in concepts.get("areas", []) or []:
        nm = a.get("area", "")
        items.append({"type": "concept", "tab": "areas", "target": nm, "label": nm, "norm": norm_txt(nm)})
    for sp in concepts.get("specs", []) or []:
        sec, title = sp.get("section", ""), sp.get("title", "")
        label = f'{sec} — {title}' if title else sec
        items.append({"type": "spec", "section": sec, "label": label, "norm": norm_txt(label)})
    for sid, words in (words_by_sheet or {}).items():
        if not isinstance(words, list):
            continue
        for w in words[:MAX_WORDS_PER_SHEET]:
            if isinstance(w, list) and len(w) == 5:  # build_atlas_data form: [x0,y0,x1,y1,"WORD"]
                txt, box = str(w[4]), list(w[:4])
            elif isinstance(w, dict):
                txt = w.get("t") or w.get("text") or ""
                box = w.get("b") or w.get("box")
            else:
                continue
            if not txt:
                continue
            item = {"type": "word", "id": sid, "label": txt, "norm": norm_txt(txt)}
            if isinstance(box, list) and len(box) == 4:
                item["box"] = box
            items.append(item)
    return {"items": items, "sheetMeta": sheet_meta}


# ------------------------------------------------------------------ assembly

def build_body(model, model_dir, company, titles):
    proj = model.get("project", {}) or {}
    atlas = resolve_section(model_dir, model.get("sections", {}).get("plans_atlas", {}))
    sheets = [s for s in (atlas.get("sheets") or []) if isinstance(s, dict) and s.get("sheet_id")]
    links = [l for l in (atlas.get("links") or []) if isinstance(l, dict) and l.get("from_sheet")]
    concepts = atlas.get("concepts") or {}
    renders = [r for r in (atlas.get("renders") or []) if isinstance(r, dict)]
    words_by_sheet = load_words(model_dir, atlas.get("search"))
    needs_review = atlas.get("needs_review") or []

    sheets.sort(key=lambda s: (div_sort(sheet_divisions(s)[0] if sheet_divisions(s) else "99"), s.get("sheet_no", "")))
    for s in sheets:
        s["_thumb"] = sheet_image(model_dir, s)

    all_divs = sorted({d for s in sheets for d in sheet_divisions(s)}
                      | {str(t.get("division")) for t in (concepts.get("trades") or []) if t.get("division")},
                      key=div_sort)
    colors = {d: (CAT[i] if i < len(CAT) else CAT_OTHER) for i, d in enumerate(all_divs)}

    links_by_from = {}
    for l in links:
        links_by_from.setdefault(l["from_sheet"], []).append(l)

    renders_by_sheet = {}
    for r in renders:
        for sid in (r.get("sheet_ids") or []):
            renders_by_sheet.setdefault(sid, []).append(r)

    out = []

    # ---------- header band + page strip (NTXP Document Engine) ----------
    scope_path = model_dir / "sections" / "scope_index.json"
    scope = (load_json(scope_path) or None) if scope_path.is_file() else None
    sub_bits = [str(x) for x in (proj.get("number"), proj.get("location") if isinstance(proj.get("location"), str) else None) if x]
    proj_sub = f' <span style="opacity:.8">| {esc(" | ".join(sub_bits))}</span>' if sub_bits else ""
    title_txt = ((scope or {}).get("project_index") or {}).get("title") or proj.get("title", "Untitled Project")
    out.append(atlas_shell.header_html(company, title_txt, proj_sub))
    out.append(atlas_shell.strip_html(sheets))

    # ---------- rail: left ----------
    trades = concepts.get("trades") or []
    specs = concepts.get("specs") or []
    phases = concepts.get("phases") or []
    areas = concepts.get("areas") or []
    left_rail = f'''<aside class="rail-left" id="de-left" aria-label="Trades, spec numbers, areas and phases">
      <div class="rail-tabs">
        <button type="button" class="rail-tab" data-tab="trades" aria-selected="true">Trades</button>
        <button type="button" class="rail-tab" data-tab="specs" aria-selected="false">Spec #</button>
        <button type="button" class="rail-tab" data-tab="areas" aria-selected="false">Areas</button>
        <button type="button" class="rail-tab" data-tab="phases" aria-selected="false">Phases</button>
      </div>
      <div class="rail-panel active" data-tab="trades">{trades_tab_html(trades, colors, titles, len(sheets))}</div>
      <div class="rail-panel" data-tab="specs">{specs_tab_html(specs, colors)}</div>
      <div class="rail-panel" data-tab="phases">{phases_tab_html(phases)}</div>
      <div class="rail-panel" data-tab="areas">{areas_tab_html(areas)}</div>
    </aside>'''

    # ---------- center: discipline tabs + sheet grid + viewer ----------
    disc_tabs_html_ = discipline_tabs_html(sheets)
    grid_cards = "".join(sheet_card_html(s, colors, titles) for s in sheets) \
        or '<div class="empty-grid">No sheets indexed yet — run the atlas builder once the drawing set is parsed.</div>'
    viewer_panels = "".join(viewer_panel_html(s, links_by_from) for s in sheets)

    center = f'''<main class="atl-center">
      <div class="disc-tabs" id="disc-tabs">{disc_tabs_html_}</div>
      <div class="sheet-grid" id="sheet-grid">{grid_cards}</div>
      <div class="viewer" id="viewer" hidden>
        <div class="viewer-toolbar">
          <button type="button" class="btn" id="v-back">‹ Back</button>
          <div class="breadcrumb" id="v-crumb"></div>
          <div class="v-zoom">
            <button type="button" data-zoom="out" title="Zoom out">−</button>
            <button type="button" data-zoom="fit" title="Fit to view">Fit</button>
            <button type="button" data-zoom="in" title="Zoom in">+</button>
          </div>
          <button type="button" class="btn" id="v-close">Close ✕</button>
        </div>
        {atlas_shell.layer_bar_html()}
        <div class="viewer-canvas" id="viewer-canvas">
          <div id="viewer-panels">{viewer_panels}</div>
        </div>
      </div>
    </main>'''

    # ---------- right rail ----------
    rr_panels = "".join(rail_right_panel_html(s, colors, links_by_from, renders_by_sheet) for s in sheets)
    def crop_src(rel):
        """Schedule and elevation crops: inlined while the page stays inside its size budget, else a relative path."""
        p = model_dir / rel
        try:
            size = p.stat().st_size
        except OSError:
            return rel
        if size <= MAX_INLINE_BYTES and _inlined[0] + size <= TOTAL_INLINE_BYTES:
            _inlined[0] += size
            return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
        return rel

    detail = atlas_shell.detail_panels_html(atlas, scope, crop_src)
    right_rail = f'''<aside id="de-right" aria-label="Details for the selected item">
      <p class="dd-empty" id="dd-empty">Pick a trade, spec number, area or phase on the left to see its details here.</p>
      {detail}
      <div id="rail-right">
        {rr_panels}
        <div class="stage-queue"><h4>Staged Requests</h4><div id="stage-queue-list"></div></div>
      </div>
    </aside>'''

    out.append(f'<div class="atl-wrap" id="atl-wrap">{left_rail}{center}{right_rail}</div><div class="de-scrim"></div>')

    # ---------- footer + focus areas ----------
    if needs_review:
        lis = "".join(f"<li>{esc(x)}</li>" for x in needs_review[:20])
        out.append(f'''<div class="atl-wrap" style="padding-top:0">
          <div></div>
          <div class="reveal" style="border:1px solid var(--line2);background:var(--panel);border-radius:var(--r);
              padding:18px 20px;box-shadow:var(--raise)">
            <h4 style="font:700 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--gold-soft);
                margin-bottom:8px">Worth a look</h4>
            <ul style="margin:0;padding-left:18px;color:var(--muted);font-size:13px">{lis}</ul>
          </div></div>''')

    out.append('<div id="tip"></div><div class="toast" id="toast"></div>')
    search_payload = build_search_payload(sheets, concepts, words_by_sheet)
    out.append(f'<script id="atlas-search-data" type="application/json">{json.dumps(search_payload)}</script>')
    marks, problems = atlas_shell.markup_overlays(model_dir, sheets)
    overlays = atlas_shell.merge_overlays(marks, atlas_shell.index_overlays(scope))
    live = atlas_shell.payload(overlays, problems).replace("</", "<\\/")
    out.append(f'<script id="atlas-live-data" type="application/json">{live}</script>')

    return "".join(out)


def build(args):
    model = load_json(args.model)
    if not model:
        log(f"could not load model: {args.model}")
        sys.exit(2)
    model_dir = Path(args.model).resolve().parent

    if args.dry_run:
        atlas_preview = resolve_section(model_dir, model.get("sections", {}).get("plans_atlas", {}))
        print(json.dumps({
            "dry_run": True, "project": model.get("project", {}),
            "sheets": len(atlas_preview.get("sheets") or []),
            "links": len(atlas_preview.get("links") or []),
            "layout": ["top bar (brand + project chip + Command Dashboard pill + search)",
                       "left concept rail (Trades / Specs / Phases / Areas)",
                       "center: discipline tabs + sheet grid, or the pan/zoom viewer with hotspots + back-stack",
                       "right rail: sheet info, divisions, outbound links, renders, stage-markup / stage-phase-image",
                       "focus areas (needs_review)"],
            "palette": CAT, "note": "stdlib only; fully self-contained output",
        }, indent=2))
        return

    titles = load_division_titles()
    body = build_body(model, model_dir, args.company, titles)
    bg = ('<div class="atl-bg"></div>'
          f'<div class="atl-stars s1" style="background-image:url(\'{constellation(70, seed=11)}\')"></div>'
          f'<div class="atl-stars s2" style="background-image:url(\'{constellation(42, seed=29, bright=True)}\')"></div>')
    noscript = '<noscript><style>.reveal{opacity:1!important;transform:none!important}</style></noscript>'

    if args.fragment:
        doc = (f'<style>{STYLE}{atlas_shell.STYLE}</style>{noscript}\n'
               f'<div class="atl-root"><div class="atl-shell">{bg}{body}</div></div>\n'
               f'<script>{SCRIPT}</script><script>{atlas_shell.SCRIPT}</script>')
    else:
        title = esc(model.get("project", {}).get("title", "Plans Atlas"))
        doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
               f'<meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>{title} · {esc(args.company)} Plans Atlas</title>'
               f'<style>{STYLE}{atlas_shell.STYLE}</style>{noscript}</head>'
               f'<body class="atl-root"><div class="atl-shell">{bg}{body}</div>'
               f'<script>{SCRIPT}</script><script>{atlas_shell.SCRIPT}</script></body></html>')

    default_name = f'{model.get("project", {}).get("slug", "project")}-plans-atlas.html'
    out = Path(args.out) if args.out else model_dir / default_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc)
    log(f"wrote plans atlas: {out}  ({len(doc):,} bytes, {'fragment' if args.fragment else 'standalone'})")
    print(json.dumps({"atlas": str(out), "bytes": len(doc),
                      "mode": "fragment" if args.fragment else "standalone"}, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Render the Canonical Project Record's plans_atlas into NTXP Plans Atlas.")
    ap.add_argument("--model", required=True, help="Path to canonical-model.json.")
    ap.add_argument("--out", help="Output .html path (default <model_dir>/<slug>-plans-atlas.html).")
    ap.add_argument("--company", default=DEFAULT_COMPANY, help="Branding/company name (default NTXP).")
    ap.add_argument("--fragment", action="store_true", help="Emit body content only for embedding.")
    ap.add_argument("--dry-run", action="store_true", help="Print the planned layout without rendering.")
    build(ap.parse_args())


if __name__ == "__main__":
    main()
