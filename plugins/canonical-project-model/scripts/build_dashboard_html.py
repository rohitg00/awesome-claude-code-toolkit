#!/usr/bin/env python3
"""
build_dashboard_html.py — render the Canonical Project Record into a self-contained,
animated HTML command dashboard (v2).

The Excel workbook (build_workbook.py) is the working deliverable; this is the
project's living "wall screen" — one .html file (no external requests, safe to email
or host) rendered from the same canonical-model.json single source of truth, in CSI
MasterFormat order throughout.

Layout (top to bottom):
  sync pills (manual one-way sync per connector + the Propose-Updates two-way flow)
  hero → five donut KPI infographics (slices slide around the ring and bounce closed;
  glowing value in a smooth round center) → segmented budget bar (click a segment →
  that trade's exportable ITB/budget-justification modal; flips to the Buyout Budget
  with neon-green profit once phase=project) → activity stream (JobTread photos,
  OCR4 pdf snips) → five translucent daily-report date cards with intelligence-flag
  banners → open Submittals + open RFIs beside a scrollable vertical critical-path
  plotter → a three-week look-ahead (last/this/next week) with click-to-edit cells,
  red critical path and blue deliveries → focus areas.

Health lights: green = on track · yellow = team attention · red = priority focus.
Copy stays constructive everywhere — a customer may be reading over a shoulder, so
the dashboard never makes blunt negative statements about the project's success.

Sync policy rendered into the GUI: connectors sync ONE-WAY into the knowledge base
(last five days prioritized, then backfill); the agent's suggestions are staged and
only sync outward after explicit approval in the Propose-Updates dialog. Declining
leaves this record correct and authoritative even if external tools don't align.

Deterministic rendering only — no reasoning, no pricing. Stdlib only. Categorical
palette validated (dataviz six checks, dark surface #20242c): lightness band, chroma
floor, adjacent-pair CVD ΔE≥12, contrast ≥3:1; 2px slice/segment gaps + legends give
secondary encoding. Two modes: full document (default) or --fragment.
"""

import argparse
import datetime as _dt
import html
import json
import math
import random
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent
DIVISIONS_FILE = PLUGIN_DIR / "resources" / "masterformat-divisions.json"

DEFAULT_COMPANY = "NTXP"

# Validated categorical palette — no yellow/ochre/olive hues (brand: navy + platinum
# + blue). dataviz validator, --mode dark --surface #141a24: lightness band, chroma
# floor, contrast all PASS; worst adjacent CVD ΔE 10.3 (floor band — legal with our
# 2px slice gaps + legends as secondary encoding). Fixed order, assigned to the
# project's divisions in ascending order, never cycled; 9th+ divisions fold to OTHER.
CAT = ["#3f78b5", "#bd6428", "#17948a", "#7e58c2", "#1d7fa8", "#a44e94", "#5563cc", "#b85c6e"]
CAT_OTHER = "#5f6a78"
NEON_PROFIT = "#3be08f"   # buyout profit — used only for profit, with icon+label

R = 44.0                   # donut radius
CIRC = 2 * math.pi * R     # ≈ 276.46
GAP = 3.0                  # px gap between slices (2px spec + stroke rounding)


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


def div_of(obj):
    if not isinstance(obj, dict):
        return "99"
    csi = obj.get("csi")
    if isinstance(csi, dict) and csi.get("masterformat_division"):
        return str(csi["masterformat_division"])
    if obj.get("masterformat_division"):
        return str(obj["masterformat_division"])
    divs = obj.get("csi_divisions")
    if isinstance(divs, list) and divs:
        return str(divs[0])
    return "99"


def div_key(obj):
    d = div_of(obj)
    try:
        return (int(d), d)
    except (ValueError, TypeError):
        return (99, "99")


def money(obj):
    if isinstance(obj, dict) and isinstance(obj.get("amount"), (int, float)):
        return obj["amount"]
    return None


def qty_value(q):
    if isinstance(q, dict) and isinstance(q.get("value"), (int, float)):
        return q["value"]
    return None


def qty_uom(q):
    if isinstance(q, dict):
        return q.get("uom") or q.get("as_written") or ""
    return ""


def esc(v):
    return html.escape("" if v is None else str(v))


def fmt_money(amount):
    return f"${amount:,.0f}" if isinstance(amount, (int, float)) else "—"


def constellation(n, seed, w=1500, h=1050, link=170, bright=False):
    """A tileable-enough field of faint interlinked stars (the brand board's
    blueprint-node feel) as a self-contained SVG data URI. Seeded RNG keeps the
    render deterministic; nearby stars are joined by hairline links."""
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


def parse_date(s):
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def fmt_day(d):
    return d.strftime("%b %d") if d else "TBD"


# --------------------------------------------------------------------- styles

STYLE = """
:root{
  /* NTXP brand board: deep navy-black ground, platinum/silver metal, one blue accent.
     --gold/--line-g keep their names for stability but now hold PLATINUM values. */
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
.cpm-root{font-family:var(--sans);color:var(--ink);line-height:1.55;background:var(--bg);
  -webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden}
.cpm-root h1,.cpm-root h2,.cpm-root h3{margin:0;font-weight:600;letter-spacing:-.01em}
.cpm-root a{color:inherit;text-decoration:none}
/* 3D ground: navy-black radial vignette + a faint diagonal sheen, with two
   constellation layers (interlinked stars) drifting slower than the foreground. */
.cpm-bg,.cpm-bg2{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
  transition:opacity 1.5s ease}
/* PROJECT phase: navy */
.cpm-bg{background:
  linear-gradient(118deg,rgba(120,150,195,.05) 0%,transparent 34%,transparent 70%,rgba(60,80,115,.05) 100%),
  radial-gradient(125% 95% at 50% -12%,#151b28 0%,#0b0f16 46%,#05070c 100%)}
/* ESTIMATE phase: black -> charcoal starry night */
.cpm-bg2{background:
  linear-gradient(118deg,rgba(160,165,175,.04) 0%,transparent 36%,transparent 72%,rgba(120,124,132,.04) 100%),
  radial-gradient(125% 95% at 50% -12%,#1b1d21 0%,#0c0d10 48%,#040405 100%)}
.phase-project .cpm-bg2{opacity:0}
.phase-estimate .cpm-bg{opacity:0}
.phase-estimate .cpm-stars.s1{opacity:.62}
.phase-estimate .cpm-stars.s2{opacity:.42}
.cpm-bg::before,.cpm-bg::after{content:"";position:absolute;width:62vmax;height:62vmax;border-radius:50%;
  filter:blur(95px);opacity:.11;will-change:transform}
.cpm-bg::before{background:radial-gradient(circle,var(--blue),transparent 60%);top:-24vmax;right:-14vmax;animation:drift1 44s ease-in-out infinite}
.cpm-bg::after{background:radial-gradient(circle,#8ea6c9,transparent 60%);bottom:-28vmax;left:-18vmax;animation:drift2 56s ease-in-out infinite}
.cpm-stars{position:fixed;inset:-8%;z-index:0;pointer-events:none;background-repeat:repeat;
  mask-image:radial-gradient(120% 100% at 50% 0%,#000 0%,rgba(0,0,0,.35) 75%,transparent 100%)}
.cpm-stars.s1{opacity:.5;animation:starDrift1 240s linear infinite alternate}
.cpm-stars.s2{opacity:.32;animation:starDrift2 160s linear infinite alternate}
@keyframes starDrift1{to{transform:translate(-70px,42px)}}
@keyframes starDrift2{to{transform:translate(55px,-38px)}}
@keyframes drift1{50%{transform:translate(-7vmax,6vmax) scale(1.12)}}
@keyframes drift2{50%{transform:translate(7vmax,-5vmax) scale(1.06)}}

.cpm-wrap{position:relative;z-index:1;max-width:1240px;margin:0 auto;padding:0 28px 110px}
.cpm-nav{position:sticky;top:0;z-index:30;display:flex;gap:6px;flex-wrap:wrap;align-items:center;
  padding:12px 28px;margin:0 -28px;backdrop-filter:blur(13px);
  background:linear-gradient(180deg,rgba(20,23,27,.92),rgba(20,23,27,.65));
  border-bottom:1px solid var(--line-w);box-shadow:0 1px 0 var(--line-g)}
.cpm-nav .brand{font:600 15px/1 var(--serif);margin-right:auto;display:flex;align-items:center;gap:11px}
.cpm-nav .dot{width:9px;height:9px;border-radius:50%;background:var(--gold);box-shadow:0 0 10px var(--gold);animation:pulse 2.8s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(195,205,221,.5)}70%{box-shadow:0 0 0 9px rgba(195,205,221,0)}100%{box-shadow:0 0 0 0 rgba(195,205,221,0)}}
.cpm-nav a{font-size:13px;color:var(--muted);padding:7px 12px;border-radius:9px;transition:.22s ease;border:1px solid transparent}
.cpm-nav a:hover{color:#fff;border-color:var(--line2);box-shadow:0 0 20px -2px rgba(79,150,216,.45);transform:translateY(-1px)}
/* phase toggle — large, glowing, top right */
.ptoggle{cursor:pointer;position:relative;display:flex;align-items:center;width:196px;height:42px;
  border-radius:999px;border:1px solid var(--line2);background:var(--panel);box-shadow:var(--raise);
  margin-left:14px;flex:0 0 auto;transition:.3s ease}
.ptoggle:hover{box-shadow:var(--raise),0 0 26px -2px rgba(79,150,216,.65)}
.ptoggle .opt{flex:1;text-align:center;font:700 11px/1 var(--mono);letter-spacing:.12em;z-index:1;
  color:var(--faint);transition:color .4s ease}
.ptoggle .knob{position:absolute;top:3px;left:3px;width:94px;height:34px;border-radius:999px;
  background:linear-gradient(180deg,#5ba4e0,var(--blue-deep));box-shadow:0 0 18px rgba(79,150,216,.75),0 1px 0 rgba(255,255,255,.25) inset;
  transition:left .45s cubic-bezier(.34,1.4,.5,1),background .45s ease}
.phase-project .ptoggle .knob{left:99px}
.phase-estimate .ptoggle .knob{background:linear-gradient(180deg,#454b56,#24282f);box-shadow:0 0 18px rgba(195,205,221,.5),0 1px 0 rgba(255,255,255,.2) inset}
.phase-estimate .ptoggle .opt.est{color:#fff}
.phase-project .ptoggle .opt.proj{color:#fff}
.ptoggle.flip .knob{animation:knobpulse .6s ease}
@keyframes knobpulse{40%{box-shadow:0 0 34px 6px rgba(79,150,216,.85)}}
.phase-estimate .segw.profit-seg{display:none}

/* ------- sync pills ------- */
.syncbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:14px 0 0}
.syncbar .cap{font:600 11px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin-right:2px}
.spill{cursor:pointer;display:inline-flex;align-items:center;gap:9px;font:600 12.5px/1 var(--sans);color:var(--muted);
  padding:9px 15px;border-radius:999px;border:1px solid var(--line-w);background:var(--panel);box-shadow:var(--raise);
  transition:.24s cubic-bezier(.2,.7,.2,1)}
.spill:hover{color:#fff;transform:translateY(-2px);box-shadow:var(--raise),0 0 22px -2px rgba(79,150,216,.6);border-color:rgba(79,150,216,.5)}
.spill .lt{width:8px;height:8px;border-radius:50%;flex:0 0 8px}
.spill .when{font:500 11px/1 var(--mono);color:var(--faint)}
.spill.propose{border-color:var(--line-g);color:var(--gold-soft)}
.spill.propose:hover{box-shadow:var(--raise),0 0 24px -2px rgba(195,205,221,.6);border-color:var(--gold)}
.spill.syncing .lt{animation:pulse 1.1s infinite}
.lt.green{background:var(--green);box-shadow:0 0 8px rgba(84,192,138,.7)}
.lt.yellow{background:var(--yellow);box-shadow:0 0 8px rgba(207,138,58,.7)}
.lt.red{background:var(--red);box-shadow:0 0 8px rgba(207,92,107,.7)}

.cpm-hero{padding:34px 0 8px}
.cpm-eyebrow{font:600 12px/1 var(--mono);letter-spacing:.24em;text-transform:uppercase;color:var(--gold)}
.cpm-hero h1{font-family:var(--serif);font-size:clamp(28px,4vw,44px);line-height:1.05;margin:14px 0 6px}
.cpm-sub{color:var(--muted);font-size:15px}
.cpm-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.cpm-chip{font:600 12px/1 var(--sans);padding:8px 13px;border-radius:999px;border:1px solid var(--line-w);
  background:var(--panel);box-shadow:var(--raise);color:var(--muted);display:inline-flex;gap:7px;align-items:center}
.cpm-chip b{color:var(--ink);font-weight:600}
.cpm-chip.joc{border-color:var(--line-g);color:var(--gold-soft)}

.cpm-section{margin-top:52px}
.cpm-section>h2{font-family:var(--serif);font-size:23px;display:flex;align-items:center;gap:13px;
  padding-bottom:12px;border-bottom:1px solid var(--line-w);
  background:linear-gradient(90deg,var(--line-g),transparent) bottom/40% 1px no-repeat}
.cpm-section>h2::before{content:"";width:20px;height:3px;background:var(--gold);border-radius:2px;box-shadow:0 0 10px var(--gold)}
.cpm-section .hint{color:var(--faint);font-size:13px;margin:10px 0 18px}
.hstat{margin-left:auto;display:inline-flex;align-items:center;gap:7px;font:600 11px/1 var(--mono);
  letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.hstat .lt{width:9px;height:9px;border-radius:50%}

/* ------- donut KPI cards ------- */
.donuts{display:grid;grid-template-columns:repeat(auto-fit,minmax(196px,1fr));gap:16px;margin-top:26px}
.dcard{position:relative;padding:18px 16px 14px;border:1px solid var(--line-w);border-radius:var(--r);
  background:var(--panel);box-shadow:var(--raise);transition:.28s cubic-bezier(.2,.7,.2,1)}
.dcard:hover{transform:translateY(-4px);border-color:rgba(79,150,216,.4);box-shadow:var(--raise-hi)}
.dcard .dl{font:600 11px/1 var(--mono);color:var(--faint);letter-spacing:.12em;text-transform:uppercase;text-align:center}
.dwrap{position:relative;width:128px;height:128px;margin:14px auto 10px}
.dwrap svg{width:128px;height:128px;display:block}
/* exploded pie: wedges roll out around the center, then the number fades in */
.wedge{transform-origin:60px 60px;transform:rotate(0) translate(var(--tx),var(--ty)) scale(1)}
.reveal.in .wedge{animation:rollout .85s cubic-bezier(.3,1.3,.45,1) both;animation-delay:var(--d)}
@keyframes rollout{from{transform:rotate(-130deg) translate(0,0) scale(.55);opacity:0}
  to{transform:rotate(0) translate(var(--tx),var(--ty)) scale(1);opacity:1}}
.reveal.in .dnum{animation:numfade .55s ease 1.05s both}
@keyframes numfade{from{opacity:0;transform:scale(.85)}}
.dcore{position:absolute;inset:37px;border-radius:50%;
  background:radial-gradient(circle at 38% 32%,#2c323c 0%,#20242c 70%,#1b1f26 100%);
  box-shadow:0 2px 10px rgba(0,0,0,.55),0 1px 0 rgba(255,255,255,.06) inset;
  display:grid;place-items:center}
.dnum{font:700 17px/1 var(--sans);font-variant-numeric:tabular-nums;color:#fff;
  text-shadow:0 0 14px rgba(79,150,216,.95),0 0 34px rgba(79,150,216,.45)}
.dnum.goldglow{text-shadow:0 0 14px rgba(216,184,120,.95),0 0 34px rgba(195,205,221,.5)}
.dleg{display:flex;flex-wrap:wrap;gap:5px 10px;justify-content:center;min-height:18px}
.dleg span{display:inline-flex;align-items:center;gap:5px;font:500 10.5px/1 var(--sans);color:var(--muted)}
.dleg i{width:8px;height:8px;border-radius:2px;flex:0 0 8px}

/* ------- segmented budget bar ------- */
.segbar{margin-top:22px}
.segrow{display:flex;gap:2px;align-items:flex-end}
.segw{display:flex;flex-direction:column;gap:6px;min-width:56px;cursor:pointer;transition:.2s ease}
.segw:hover{transform:translateY(-3px)}
.segw .amt{font:600 12px/1 var(--mono);color:var(--ink);text-align:center;white-space:nowrap}
.segw .nm{font:500 10.5px/1.2 var(--sans);color:var(--muted);text-align:center;margin-top:5px}
.segfill{height:46px;border-radius:5px;box-shadow:0 1px 0 rgba(255,255,255,.14) inset,0 -10px 16px -8px rgba(0,0,0,.5) inset;
  transition:.25s ease;transform-origin:bottom}
.segw:hover .segfill{box-shadow:0 1px 0 rgba(255,255,255,.2) inset,0 0 18px -2px rgba(79,150,216,.55)}
.segfill.profit{background:linear-gradient(180deg,#49f09d,var(--neon));box-shadow:0 0 22px -2px rgba(59,224,143,.8),0 1px 0 rgba(255,255,255,.25) inset}
.segw .amt.profit{color:var(--neon);text-shadow:0 0 12px rgba(59,224,143,.7)}
.segtotal{display:flex;justify-content:flex-end;gap:12px;align-items:baseline;margin-top:14px;padding-top:12px;
  border-top:1px solid var(--line-w)}
.segtotal .t{font:600 11px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.segtotal .v{font:700 24px/1 var(--mono);color:var(--gold-soft)}

/* ------- activity stream ------- */
.stream{display:grid;gap:10px}
.sitem{display:flex;gap:14px;align-items:flex-start;padding:13px 16px;border:1px solid var(--line-w);
  border-radius:12px;background:var(--panel);box-shadow:var(--raise);transition:.22s ease}
.sitem:hover{transform:translateX(4px);border-color:rgba(79,150,216,.35)}
.sthumb{width:58px;height:58px;border-radius:9px;object-fit:cover;flex:0 0 58px;border:1px solid var(--line2)}
.sdoc{width:58px;height:58px;border-radius:9px;flex:0 0 58px;display:grid;place-items:center;
  font:700 10px/1 var(--mono);color:var(--gold-soft);border:1px solid var(--line-g);
  background:linear-gradient(160deg,rgba(195,205,221,.12),rgba(195,205,221,.03))}
.sitem .tx{font-size:13.5px}
.sitem .meta{font:500 11px/1 var(--mono);color:var(--faint);margin-top:5px;display:flex;gap:10px;flex-wrap:wrap}
.srcchip{font:600 10px/1 var(--mono);text-transform:uppercase;letter-spacing:.08em;padding:3px 7px;border-radius:5px;
  border:1px solid var(--line-w);color:var(--muted)}

/* ------- daily report cards ------- */
.days{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:14px}
.daycard{position:relative;display:block;aspect-ratio:1/1.04;max-width:280px;border-radius:var(--r);overflow:hidden;
  border:1px solid var(--line-w);backdrop-filter:blur(8px);box-shadow:var(--raise);
  transition:.26s cubic-bezier(.2,.7,.2,1);padding:0}
.daycard:hover{transform:translateY(-4px) scale(1.015);box-shadow:var(--raise-hi)}
.daycard .flags{position:absolute;top:0;left:0;right:0;display:grid;gap:2px}
.fbanner{font:600 10px/1.1 var(--sans);padding:5px 9px;color:#fff;display:flex;gap:6px;align-items:center;
  text-shadow:0 1px 2px rgba(0,0,0,.4)}
.daycard .body{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:flex-end;padding:14px}
.daycard .dnumber{font:700 44px/1 var(--serif);color:#fff;text-shadow:0 0 18px rgba(0,0,0,.4)}
.daycard .dmeta{font:600 11px/1.4 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.75)}
.daycard .dsum{font:400 11.5px/1.45 var(--sans);color:rgba(255,255,255,.85);margin-top:7px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.daycard .go{position:absolute;top:10px;right:12px;font:600 11px/1 var(--mono);color:rgba(255,255,255,.7);opacity:0;transition:.2s}
.daycard:hover .go{opacity:1}

/* ------- blocks + plotter ------- */
.duo{display:grid;grid-template-columns:1.6fr 1fr;gap:16px}
@media (max-width:900px){.duo{grid-template-columns:1fr}}
.block{border:1px solid var(--line-w);border-radius:var(--r);background:var(--panel);box-shadow:var(--raise);overflow:hidden}
.block h3{font:600 13px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  padding:14px 16px;border-bottom:1px solid var(--line-g);display:flex;align-items:center;gap:10px;
  background:linear-gradient(180deg,rgba(255,255,255,.04),transparent)}
.block h3 .cnt{margin-left:auto;font:700 13px/1 var(--mono);color:var(--gold-soft)}
.brow{display:flex;gap:12px;align-items:baseline;padding:11px 16px;border-bottom:1px solid var(--line-w);font-size:13px;transition:background .18s}
.brow:last-child{border-bottom:0}
.brow:hover{background:rgba(79,150,216,.06)}
.brow .id{font:600 11px/1 var(--mono);color:var(--faint);flex:0 0 auto}
.brow .lead{margin-left:auto;font:600 11px/1 var(--mono);color:var(--muted);white-space:nowrap}
.brow .lead.hot{color:var(--yellow)}

.plotter{position:relative;display:flex;flex-direction:column}
.pvp{flex:1;overflow-y:auto;scrollbar-width:none;max-height:430px;padding:10px 16px}
.pvp::-webkit-scrollbar{display:none}
.pline{position:relative;padding-left:24px}
.pline::before{content:"";position:absolute;left:7px;top:6px;bottom:6px;width:2px;
  background:linear-gradient(var(--gold),var(--blue),transparent)}
.pev{position:relative;padding:0 0 18px}
.pev::before{content:"";position:absolute;left:-21px;top:5px;width:11px;height:11px;border-radius:50%;
  background:var(--bg);border:2px solid var(--blue);box-shadow:0 0 10px rgba(79,150,216,.5)}
.pev.crit::before{border-color:var(--red);box-shadow:0 0 10px rgba(207,92,107,.6)}
.pev .pd{font:600 11px/1 var(--mono);color:var(--gold-soft)}
.pev .pl{font-size:13px;margin-top:3px}
.pev .pr{font-size:11.5px;color:var(--muted);margin-top:2px}
.pbtns{display:flex;gap:8px;justify-content:center;padding:10px}
.pbtn{cursor:pointer;width:34px;height:30px;border-radius:8px;border:1px solid var(--line-w);background:var(--panel);
  color:var(--muted);font-size:13px;transition:.2s}
.pbtn:hover{color:#fff;box-shadow:0 0 14px -2px rgba(79,150,216,.6)}

/* ------- look-ahead ------- */
.la-tabs{display:flex;gap:8px;margin:0 0 14px}
.la-tab{cursor:pointer;font:600 12px/1 var(--sans);color:var(--muted);background:var(--panel);
  border:1px solid var(--line-w);box-shadow:var(--raise);padding:9px 16px;border-radius:9px;transition:.2s}
.la-tab:hover{color:#fff;box-shadow:var(--raise),0 0 16px -2px rgba(79,150,216,.5)}
.la-tab[aria-selected="true"]{color:#fff;border-color:rgba(79,150,216,.6);
  background:linear-gradient(180deg,var(--blue),var(--blue-deep));box-shadow:0 0 20px -2px rgba(79,150,216,.6)}
.la-tab[aria-selected="true"] .num{color:rgba(255,255,255,.85)!important}
.la-view{overflow:hidden;border-radius:var(--r)}
.la-track{display:flex;width:300%;transition:transform .55s cubic-bezier(.2,.7,.2,1)}
.la-panel{width:33.3334%;flex:0 0 33.3334%}
.la-panel .cpm-card{margin-right:2px}
.cpm-card{border:1px solid var(--line-w);border-radius:var(--r);background:var(--panel);box-shadow:var(--raise);overflow:hidden}
.cpm-table{width:100%;border-collapse:collapse;font-size:13.5px}
.cpm-table th{text-align:left;font:600 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--faint);
  padding:13px 14px;border-bottom:1px solid var(--line-g);background:linear-gradient(180deg,rgba(255,255,255,.04),transparent)}
.cpm-table td{padding:11px 14px;border-bottom:1px solid var(--line-w);vertical-align:top}
.cpm-table tr:last-child td{border-bottom:0}
.cpm-table tbody tr:hover{background:rgba(79,150,216,.05)}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
tr.crit td:first-child{box-shadow:3px 0 0 var(--red) inset}
tr.deliv td:first-child{box-shadow:3px 0 0 var(--blue) inset}
.typechip{font:600 10px/1 var(--mono);text-transform:uppercase;letter-spacing:.07em;padding:4px 8px;border-radius:5px;border:1px solid var(--line-w);color:var(--muted)}
.typechip.crit{color:var(--red);border-color:rgba(207,92,107,.5)}
.typechip.deliv{color:var(--blue);border-color:rgba(79,150,216,.5)}
[contenteditable="true"]{outline:none;border-bottom:1px dashed rgba(255,255,255,.18);cursor:text;min-width:40px}
[contenteditable="true"]:focus{border-bottom-color:var(--blue);background:rgba(79,150,216,.08)}

.divtag{display:inline-flex;align-items:center;gap:8px;font:600 12px/1 var(--mono);padding:5px 10px;border-radius:7px;
  background:rgba(255,255,255,.04);border:1px solid var(--line-w);white-space:nowrap}
.divtag .sw{width:9px;height:9px;border-radius:3px}

/* ------- review / focus ------- */
.review{border:1px solid var(--line2);background:var(--panel);
  border-radius:var(--r);padding:20px 22px;box-shadow:var(--raise)}
.review li{color:var(--muted);margin:4px 0}

/* ------- modal + toast ------- */
.mmask{position:fixed;inset:0;z-index:60;background:rgba(10,12,16,.66);backdrop-filter:blur(6px);
  display:none;align-items:flex-start;justify-content:center;overflow-y:auto;padding:40px 18px}
.mmask.show{display:flex}
.modal{width:min(860px,100%);border-radius:16px;border:1px solid var(--line2);background:var(--panel);
  box-shadow:0 40px 90px -30px rgba(0,0,0,.9);animation:mpop .35s cubic-bezier(.3,1.3,.4,1)}
@keyframes mpop{from{transform:translateY(26px) scale(.97);opacity:0}}
.mhead{display:flex;align-items:center;gap:14px;padding:18px 22px;border-bottom:1px solid var(--line-g)}
.mhead h3{font-family:var(--serif);font-size:19px}
.mhead .x{margin-left:auto;cursor:pointer;width:32px;height:32px;border-radius:8px;border:1px solid var(--line-w);
  background:transparent;color:var(--muted);font-size:15px}
.mhead .x:hover{color:#fff;box-shadow:0 0 14px -2px rgba(207,92,107,.6)}
.mbody{padding:20px 22px;max-height:62vh;overflow-y:auto}
.mfoot{display:flex;gap:10px;padding:16px 22px;border-top:1px solid var(--line-w);flex-wrap:wrap}
.btn{cursor:pointer;font:600 12.5px/1 var(--sans);padding:11px 18px;border-radius:9px;border:1px solid var(--line-w);
  background:var(--panel);color:var(--muted);transition:.2s}
.btn:hover{color:#fff;box-shadow:0 0 18px -2px rgba(79,150,216,.55);transform:translateY(-1px)}
.btn.primary{color:#fff;border-color:rgba(79,150,216,.6);background:linear-gradient(180deg,var(--blue),var(--blue-deep))}
.btn.gold{color:#10141b;border-color:var(--gold);background:linear-gradient(180deg,var(--gold-soft),var(--gold))}
.itb .krow{display:flex;gap:26px;flex-wrap:wrap;margin-bottom:14px}
.itb .krow div{font-size:12.5px;color:var(--muted)}
.itb .krow b{display:block;color:var(--ink);font-size:13px}
.itb h4{font:600 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--gold-soft);margin:18px 0 8px}
.itb ul{margin:0;padding-left:18px;font-size:13px;color:var(--muted)}
.itb .just{font-size:12px;color:var(--faint)}
.sugg{border:1px solid var(--line-w);border-radius:11px;padding:14px 16px;margin-bottom:10px;background:rgba(255,255,255,.02)}
.sugg .k{font:600 10px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--blue);margin-bottom:6px}
.sugg .t{font-weight:600;font-size:14px}
.sugg .rz{font-size:12.5px;color:var(--muted);margin-top:5px}
.sugg .acts{display:flex;gap:8px;margin-top:10px}
.sugg .btn{padding:7px 12px;font-size:11.5px}
.sugg.ok{border-color:rgba(84,192,138,.5)}
.sugg.hold{opacity:.55}
#followup{display:none;margin-top:14px;padding-top:14px;border-top:1px dashed var(--line-w)}
#followup.show{display:block}
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,20px);z-index:80;opacity:0;pointer-events:none;
  font:600 12.5px/1.4 var(--sans);color:var(--ink);padding:13px 20px;border-radius:11px;border:1px solid var(--line-g);
  background:linear-gradient(157deg,#2e343e,#23272f);box-shadow:0 18px 50px -12px rgba(0,0,0,.9),0 0 24px -4px rgba(140,175,220,.35);
  transition:.35s cubic-bezier(.2,.7,.2,1);max-width:520px;text-align:center}
.toast.show{opacity:1;transform:translate(-50%,0)}

#tip{position:fixed;z-index:90;pointer-events:none;opacity:0;transition:opacity .15s;
  font:600 11.5px/1.4 var(--sans);color:var(--ink);background:#14171c;border:1px solid var(--line2);
  border-radius:8px;padding:8px 11px;box-shadow:0 10px 30px rgba(0,0,0,.6);max-width:260px}

.cpm-foot{margin-top:72px;padding-top:24px;border-top:1px solid var(--line-w);
  background:linear-gradient(90deg,var(--line-g),transparent) top/30% 1px no-repeat;color:var(--faint);font-size:12.5px}

.reveal{opacity:0;transform:translateY(16px);transition:opacity .6s ease,transform .6s cubic-bezier(.2,.7,.2,1)}
.reveal.in{opacity:1;transform:none}
.is-hidden{display:none!important}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
  .reveal{opacity:1;transform:none}
}
@media print{
  body.print-modal *{visibility:hidden}
  body.print-modal .mmask.show,body.print-modal .mmask.show *{visibility:visible}
  body.print-modal .mmask.show{position:absolute;inset:0;background:#fff;padding:0}
  body.print-modal .mfoot,body.print-modal .mhead .x{display:none}
}
"""

# Light, paper-friendly stylesheet embedded into the downloadable ITB export.
ITB_EXPORT_CSS = """
body{font-family:Georgia,serif;color:#1c2126;margin:40px auto;max-width:760px;line-height:1.5}
h1{font-size:22px;border-bottom:2px solid #c8a050;padding-bottom:10px}
h4{font:600 11px/1 ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:#8a6a20;margin:20px 0 6px}
.krow{display:flex;gap:30px;flex-wrap:wrap}.krow div{font-size:12px;color:#555}.krow b{display:block;color:#111;font-size:13px}
ul{padding-left:18px;font-size:13px}table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;font:600 10px/1 ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;color:#777;border-bottom:1.5px solid #c8a050;padding:8px 6px}
td{padding:7px 6px;border-bottom:1px solid #e2ddd2}.num{font-family:ui-monospace,monospace}
.just{font-size:11px;color:#8a8378}.note{font-weight:700;color:#a33;margin-top:18px;font-size:12.5px}
"""

SCRIPT = """
(function(){
  var rm = window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches;

  function countUp(el){
    if(el.getAttribute('data-done'))return; el.setAttribute('data-done','1');
    var t=parseFloat(el.getAttribute('data-target')||'0'),
        pre=el.getAttribute('data-pre')||'', suf=el.getAttribute('data-suf')||'',
        dec=parseInt(el.getAttribute('data-dec')||'0',10),
        fmt=function(v){return pre+v.toLocaleString(undefined,{minimumFractionDigits:dec,maximumFractionDigits:dec})+suf;};
    if(rm){el.textContent=fmt(t);return;}
    var s=null,dur=1100;
    function step(ts){ s=s||ts; var p=Math.min((ts-s)/dur,1); var e=1-Math.pow(1-p,3);
      el.textContent=fmt(t*e); if(p<1)requestAnimationFrame(step);}
    requestAnimationFrame(step);
  }
  function fire(el){
    el.classList.add('in');
    el.querySelectorAll('[data-target]').forEach(countUp);
    el.querySelectorAll('[data-w]').forEach(function(b){ b.style.width=b.getAttribute('data-w'); });
  }
  var io = ('IntersectionObserver' in window) && !rm ? new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){
      var el=e.target, d=parseInt(el.getAttribute('data-delay')||'0',10);
      setTimeout(function(){fire(el);},d); io.unobserve(el);
    }});
  },{threshold:.12}) : null;
  document.querySelectorAll('.reveal').forEach(function(el){ io?io.observe(el):fire(el); });
  setTimeout(function(){
    document.querySelectorAll('.reveal:not(.in)').forEach(function(el){ el.classList.add('in'); });
    document.querySelectorAll('[data-target]:not([data-done])').forEach(countUp);
    document.querySelectorAll('[data-w]').forEach(function(b){ if(!b.style.width)b.style.width=b.getAttribute('data-w'); });
  }, 2600);

  // division filter
  document.querySelectorAll('.cpm-filter').forEach(function(bar){
    bar.addEventListener('click',function(ev){
      var b=ev.target.closest('.fbtn'); if(!b)return;
      var d=b.getAttribute('data-div'), scope=bar.getAttribute('data-scope');
      bar.querySelectorAll('.fbtn').forEach(function(x){x.setAttribute('aria-pressed', x===b?'true':'false');});
      document.querySelectorAll('[data-filterable="'+scope+'"]').forEach(function(row){
        row.classList.toggle('is-hidden', !(d==='all' || row.getAttribute('data-div')===d));
      });
    });
  });

  // tooltip
  var tip=document.getElementById('tip');
  document.addEventListener('mousemove',function(e){
    var t=e.target.closest('[data-tip]');
    if(t&&tip){ tip.innerHTML=t.getAttribute('data-tip'); tip.style.opacity=1;
      tip.style.left=Math.min(e.clientX+14,window.innerWidth-280)+'px'; tip.style.top=(e.clientY+16)+'px';
    } else if(tip){ tip.style.opacity=0; }
  });

  // toast
  var toastEl=document.getElementById('toast'), toastT=null;
  window.cpmToast=function(msg){ if(!toastEl)return; toastEl.textContent=msg; toastEl.classList.add('show');
    clearTimeout(toastT); toastT=setTimeout(function(){toastEl.classList.remove('show');},4200); };

  // sync pills — one-way inbound sync, last five days prioritized
  document.querySelectorAll('.spill[data-sync]').forEach(function(p){
    p.addEventListener('click',function(){
      p.classList.add('syncing'); var nm=p.getAttribute('data-sync');
      cpmToast('Sync queued: '+nm+' \\u2192 knowledge base (one-way). Last 5 days first, then backfill.');
      setTimeout(function(){p.classList.remove('syncing');},2400);
    });
  });

  // modals
  function openM(id){ var m=document.getElementById(id); if(m){ m.classList.add('show'); document.body.style.overflow='hidden'; } }
  function closeM(m){ m.classList.remove('show'); document.body.style.overflow=''; }
  window.cpmOpen=openM;
  document.querySelectorAll('.mmask').forEach(function(m){
    m.addEventListener('click',function(e){ if(e.target===m||e.target.closest('.x'))closeM(m); });
  });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape')document.querySelectorAll('.mmask.show').forEach(closeM); });
  document.querySelectorAll('[data-modal]').forEach(function(el){
    el.addEventListener('click',function(){ openM(el.getAttribute('data-modal')); });
  });

  // ITB export: print + download
  document.querySelectorAll('[data-print]').forEach(function(b){
    b.addEventListener('click',function(){
      document.body.classList.add('print-modal'); window.print();
      setTimeout(function(){document.body.classList.remove('print-modal');},400);
    });
  });
  document.querySelectorAll('[data-download]').forEach(function(b){
    b.addEventListener('click',function(){
      var m=b.closest('.modal'), body=m.querySelector('.mbody').innerHTML, ttl=m.querySelector('.mhead h3').textContent;
      var css=document.getElementById('itb-export-css').textContent;
      var doc='<!doctype html><html><head><meta charset="utf-8"><title>'+ttl+'</title><style>'+css+'</style></head><body><h1>'+ttl+'</h1>'+body+'</body></html>';
      var a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([doc],{type:'text/html'}));
      a.download=(b.getAttribute('data-download')||'ITB')+'.html'; a.click();
      setTimeout(function(){URL.revokeObjectURL(a.href);},2000);
      cpmToast('ITB exported \\u2014 open the file and print to PDF to send.');
    });
  });

  // suggestions flow — two-way sync only on explicit approval
  document.querySelectorAll('.sugg .approve').forEach(function(b){
    b.addEventListener('click',function(){ var s=b.closest('.sugg'); s.classList.add('ok'); s.classList.remove('hold'); });
  });
  document.querySelectorAll('.sugg .hold').forEach(function(b){
    b.addEventListener('click',function(){ var s=b.closest('.sugg'); s.classList.add('hold'); s.classList.remove('ok'); });
  });
  var q=document.getElementById('queue-sync');
  if(q)q.addEventListener('click',function(){
    var n=document.querySelectorAll('.sugg.ok').length;
    cpmToast(n?('Queued: '+n+' approved update'+(n>1?'s':'')+' will sync back to your tools on the next agent run.')
             :'Nothing approved yet \\u2014 approve the moves you want, then queue the sync.');
  });
  var notNow=document.getElementById('not-now');
  if(notNow)notNow.addEventListener('click',function(){ document.getElementById('followup').classList.add('show'); });
  document.querySelectorAll('#followup .btn').forEach(function(b){
    b.addEventListener('click',function(){
      var v=b.getAttribute('data-scope-sync');
      cpmToast(v==='none' ? 'Understood \\u2014 no outbound sync. This record stays your single source of truth, and it is current.'
                          : 'Queued a limited sync: '+v+' only. Everything else stays as-is here.');
    });
  });

  // phase toggle — flips the view and stages the change for approved two-way sync
  var root=document.querySelector('.cpm-root')||document.body;
  var pt=document.getElementById('ptoggle');
  function setTexts(){
    var proj=root.classList.contains('phase-project'), k=proj?'proj':'est';
    ['bt-title','bt-hint','bt-total'].forEach(function(id){
      var el=document.getElementById(id); if(el)el.textContent=el.getAttribute('data-'+k);
    });
    var chip=document.getElementById('phase-chip'); if(chip)chip.textContent=proj?'Project':'Estimate';
  }
  if(pt){
    var flip=function(){
      var toProj=!root.classList.contains('phase-project');
      root.classList.toggle('phase-project',toProj);
      root.classList.toggle('phase-estimate',!toProj);
      pt.classList.remove('flip'); void pt.offsetWidth; pt.classList.add('flip');
      setTexts();
      cpmToast(toProj?'Phase set to Project — buyout view on. Staged for two-way sync approval.'
                     :'Phase set to Estimate — bid view on. Staged for two-way sync approval.');
    };
    pt.addEventListener('click',flip);
    pt.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();flip();}});
  }

  // critical-path plotter scroll
  document.querySelectorAll('.pbtn').forEach(function(b){
    b.addEventListener('click',function(){
      var vp=document.getElementById(b.getAttribute('data-scroll'));
      if(vp)vp.scrollBy({top:(b.getAttribute('data-dir')==='up'?-170:170),behavior:'smooth'});
    });
  });

  // look-ahead tabs
  document.querySelectorAll('.la-tab').forEach(function(t,i,all){
    t.addEventListener('click',function(){
      document.querySelectorAll('.la-tab').forEach(function(x){x.setAttribute('aria-selected','false');});
      t.setAttribute('aria-selected','true');
      var track=document.getElementById('la-track');
      if(track)track.style.transform='translateX(-'+(parseInt(t.getAttribute('data-idx'),10)*33.3334)+'%)';
    });
  });
  var edited=false;
  document.querySelectorAll('[contenteditable="true"]').forEach(function(c){
    c.addEventListener('input',function(){ if(!edited){edited=true;
      cpmToast('Edit noted here. It flows to the schedule tools with the next approved sync.');} });
  });
})();
"""


# ------------------------------------------------------------------ builders

def health_dot(health, key, default="green"):
    h = health.get(key, {}) if isinstance(health, dict) else {}
    st = h.get("status", default)
    label = {"green": "On track", "yellow": "Attention", "red": "Priority"}.get(st, "On track")
    note = esc(h.get("note", ""))
    tipattr = f' data-tip="{note}"' if note else ""
    return f'<span class="hstat"{tipattr}><span class="lt {st}"></span>{label}</span>'


def divtag(div, titles, colors):
    t = titles.get(div, "")
    return (f'<span class="divtag"><span class="sw" style="background:{colors.get(div, CAT_OTHER)}"></span>'
            f'{esc(div)}{(" · " + esc(t)) if t else ""}</span>')


def reveal(inner, delay=0, cls=""):
    return f'<div class="reveal {cls}" data-delay="{delay}">{inner}</div>'


def donut_card(label, center_html, slices, glow="blue"):
    """Exploded pie: filled wedges offset outward along their mid-angle, rolling out
    around the center on reveal; the value fades in on a small round core after."""
    total = sum(v for _, v, _ in slices if v) or 1
    R2 = 52.0
    wedges, legend, start = [], [], 0.0
    for i, (name, val, color) in enumerate(slices):
        frac = min(max(val, 0) / total, 0.9999)
        if frac <= 0:
            legend.append(f'<span><i style="background:{color}"></i>{esc(name)}</span>')
            continue
        a0 = 2 * math.pi * start - math.pi / 2
        a1 = 2 * math.pi * (start + frac) - math.pi / 2
        mid = (a0 + a1) / 2
        tx, ty = math.cos(mid) * 5.5, math.sin(mid) * 5.5
        x0, y0 = 60 + R2 * math.cos(a0), 60 + R2 * math.sin(a0)
        x1, y1 = 60 + R2 * math.cos(a1), 60 + R2 * math.sin(a1)
        laf = 1 if frac > 0.5 else 0
        wedges.append(
            f'<path class="wedge" d="M60 60 L{x0:.2f} {y0:.2f} A{R2:g} {R2:g} 0 {laf} 1 {x1:.2f} {y1:.2f} Z" '
            f'fill="{color}" stroke="#12161d" stroke-width="2" '
            f'style="--tx:{tx:.2f}px;--ty:{ty:.2f}px;--d:{0.1 * i:.2f}s" '
            f'data-tip="<b>{esc(name)}</b><br>{esc(f"{val:,.0f}" if isinstance(val, (int, float)) else val)}"/>')
        legend.append(f'<span><i style="background:{color}"></i>{esc(name)}</span>')
        start += frac
    gcls = "goldglow" if glow == "gold" else ""
    return f'''<div class="dcard">
      <div class="dl">{esc(label)}</div>
      <div class="dwrap"><svg viewBox="0 0 120 120" aria-hidden="true">{"".join(wedges)}</svg>
        <div class="dcore"><span class="dnum {gcls}">{center_html}</span></div>
      </div>
      <div class="dleg">{"".join(legend[:4])}</div>
    </div>'''


def itb_modal(mid, t, ident, contacts, budget_rows, trade_total, company, titles, colors):
    d = div_of(t)
    est = next((c for c in contacts if isinstance(c, dict) and c.get("role") == "ntxp_estimator"), {})
    dates = "".join(
        f'<div><b>{esc(k.get("label",""))}</b>{esc(k.get("date") or k.get("as_written") or "TBD")}</div>'
        for k in sorted([k for k in ident.get("key_dates", []) if isinstance(k, dict)],
                        key=lambda k: k.get("date") or "9999")[:5])
    def lis(items):
        return "".join(f"<li>{esc(x)}</li>" for x in items) or "<li>(none captured)</li>"
    specs = "".join(
        f'<li>[{esc(sn.get("kind",""))}] {esc(sn.get("text",""))}'
        f'{(" — " + esc(sn.get("spec_section"))) if sn.get("spec_section") else ""}</li>'
        for sn in t.get("spec_notes", []) if isinstance(sn, dict)) or "<li>(none captured)</li>"
    rows = []
    for b in budget_rows:
        qv = qty_value(b.get("quantity")); uc = money(b.get("unit_cost"))
        ext = money(b.get("extended_cost"))
        if ext is None and qv is not None and uc is not None:
            ext = qv * uc
        just = f'Quantity from Summary QTO {esc(b.get("qto_takeoff_id",""))}' if b.get("qto_takeoff_id") else "Stated in documents"
        rows.append(f'''<tr><td>{esc(b.get("cost_code",""))}</td>
          <td>{esc(b.get("description",""))}<div class="just">{just}</div></td>
          <td class="num">{esc(f"{qv:,.0f}" if isinstance(qv,(int,float)) else "")}</td>
          <td class="num">{esc(qty_uom(b.get("quantity")))}</td>
          <td class="num">{f"${uc:,.2f}" if isinstance(uc, (int, float)) else "—"}</td>
          <td class="num">{fmt_money(ext)}</td></tr>''')
    return f'''<div class="mmask" id="{mid}"><div class="modal">
      <div class="mhead">{divtag(d, titles, colors)}<h3>{esc(company)} ITB — {esc(t.get("name",""))}</h3>
        <button class="x" aria-label="Close">✕</button></div>
      <div class="mbody itb">
        <div class="krow"><div><b>Project</b>{esc(ident.get("title",""))}</div>
          <div><b>Project #</b>{esc(ident.get("number","") or "—")}</div>
          <div><b>{esc(company)} Contact</b>{esc(est.get("name","(assign)"))} · {esc(est.get("email",""))}</div></div>
        <h4>Key Dates</h4><div class="krow">{dates}</div>
        <h4>Scope Summary</h4><p style="font-size:13.5px;margin:0">{esc(t.get("scope_summary",""))}</p>
        <h4>Exclusions</h4><ul>{lis(t.get("exclusions", []))}</ul>
        <h4>Clarifications</h4><ul>{lis(t.get("clarifications", []))}</ul>
        <h4>Specification Requirements</h4><ul>{specs}</ul>
        <h4>Budget Basis & Justification</h4>
        <table class="cpm-table"><thead><tr><th>Code</th><th>Item</th><th>Qty</th><th>UOM</th><th>Unit</th><th>Extended</th></tr></thead>
        <tbody>{"".join(rows) or '<tr><td colspan="6">(line detail pending)</td></tr>'}
        <tr><td colspan="5" style="text-align:right;font-weight:700">TRADE BUDGET</td>
        <td class="num" style="font-weight:700;color:var(--gold-soft)">{fmt_money(trade_total)}</td></tr></tbody></table>
        <p class="note" style="color:var(--red);font-weight:700;font-size:12.5px;margin-top:16px">
        Subcontractors are responsible to verify all quantities, dimensions, and information herein against the contract documents.</p>
      </div>
      <div class="mfoot"><button class="btn gold" data-print="1">Print / Save PDF</button>
        <button class="btn" data-download="ITB-{esc(t.get("trade_id",""))}">Download ITB</button>
        <button class="btn x" style="margin-left:auto">Close</button></div>
    </div></div>'''


def week_bounds(anchor):
    monday = anchor - _dt.timedelta(days=anchor.weekday())
    return [(monday - _dt.timedelta(days=7), monday - _dt.timedelta(days=1)),
            (monday, monday + _dt.timedelta(days=6)),
            (monday + _dt.timedelta(days=7), monday + _dt.timedelta(days=13))]


FLAG_COLORS = {"meeting": "#7e58c2", "intel": "#1d7fa8", "safety": "#cf5c6b",
               "weather": "#3f78b5", "delivery": "#3f78b5", "inspection": "#17948a", "other": "#5f6a78"}


def build_body(model, model_dir, company, titles):
    S = lambda k: resolve_section(model_dir, model.get("sections", {}).get(k, {}))
    proj = model.get("project", {})
    health = model.get("health", {}) or {}
    ident = S("project_identity")
    contacts = S("contacts").get("contacts", [])
    trades = sorted([t for t in S("trades").get("trades", []) if isinstance(t, dict)], key=div_key)
    qto = sorted([q for q in S("quantity_takeoff").get("items", []) if isinstance(q, dict)], key=div_key)
    budget = S("budget")
    blog = S("bid_log")
    crit = S("critical_path")
    subm = sorted([s for s in S("submittal_log").get("entries", []) if isinstance(s, dict)], key=div_key)
    rfis = [r for r in S("rfi_log").get("entries", []) if isinstance(r, dict)]
    sched = S("schedule")
    stream = [e for e in S("activity_stream").get("entries", []) if isinstance(e, dict)]
    reports = [r for r in S("daily_reports").get("reports", []) if isinstance(r, dict)]
    suggestions = [s for s in S("suggestions").get("items", []) if isinstance(s, dict)]
    connectors = [c for c in S("connectors").get("sources", []) if isinstance(c, dict)]
    phase = proj.get("phase") or ident.get("phase") or "estimate"
    is_project = phase in ("project", "closeout")

    # fixed-order categorical assignment: ascending divisions -> slots; 9th+ = Other
    all_divs = sorted({div_of(x) for x in trades} | {div_of(q) for q in qto},
                      key=lambda d: int(d) if d.isdigit() else 99)
    colors = {d: (CAT[i] if i < len(CAT) else CAT_OTHER) for i, d in enumerate(all_divs)}

    # trade estimates (stated, else derived from budget lines = qty x unit cost)
    budget_lines = [b for b in budget.get("lines", []) if isinstance(b, dict)]
    derived = {}
    for b in budget_lines:
        tid = b.get("trade_id")
        qv, uc, ext = qty_value(b.get("quantity")), money(b.get("unit_cost")), money(b.get("extended_cost"))
        amt = ext if ext is not None else ((qv * uc) if (qv is not None and uc is not None) else None)
        if tid and amt is not None:
            derived[tid] = derived.get(tid, 0) + amt
    def trade_est(tid):
        stated = money(next((t.get("estimated_value") for t in trades if t.get("trade_id") == tid), None))
        return stated if stated is not None else derived.get(tid)
    total_est = sum(v for v in (trade_est(t["trade_id"]) for t in trades) if v) or 0
    profit = money((budget.get("summary") or {}).get("profit"))

    anchor = parse_date(model.get("generated_at")) or _dt.date.today()

    out = []

    # ---------- nav ----------
    nav = [f'<div class="brand"><span class="dot"></span>{esc(company)} · Canonical Project Record</div>']
    for nm, href in [("Overview", "#overview"), ("Budget", "#budget"), ("Activity", "#activity"),
                     ("Daily", "#daily"), ("Open Items", "#openitems"), ("Look-ahead", "#lookahead")]:
        nav.append(f'<a href="{href}">{nm}</a>')
    nav.append('<div class="ptoggle" id="ptoggle" role="switch" tabindex="0" '
               'data-tip="Flip this record between Estimate and Project (buyout) view — the change stages for two-way sync approval">'
               '<span class="opt est">ESTIMATE</span><span class="opt proj">PROJECT</span><span class="knob"></span></div>')
    out.append(f'<nav class="cpm-nav">{"".join(nav)}</nav>')
    out.append('<div class="cpm-wrap">')

    # ---------- sync pills ----------
    pills = ['<span class="cap">Sync</span>']
    default_sources = [{"name": "JobTread"}, {"name": "OCR4 Docs"}, {"name": "Schedule"}, {"name": "Contacts"}]
    for c in (connectors or default_sources):
        nm = c.get("name", "Source")
        st = c.get("health", "green")
        when = ""
        ls = parse_date(c.get("last_sync"))
        if ls:
            days = (anchor - ls).days
            when = "today" if days <= 0 else (f"{days}d ago")
        pills.append(f'<button class="spill" data-sync="{esc(nm)}" '
                     f'data-tip="One-way into the knowledge base · last {c.get("window_days", 5)} days prioritized, then backfill">'
                     f'<span class="lt {st}"></span>{esc(nm)}'
                     f'{f"<span class=&quot;when&quot;>{when}</span>" if when else ""}</button>')
    pills.append('<button class="spill propose" data-modal="m-suggest" '
                 'data-tip="Review the agent&#39;s suggested moves, then approve a two-way sync — nothing writes outward without you">'
                 'Propose updates</button>')
    out.append(f'<div class="syncbar">{"".join(pills)}</div>')

    # ---------- hero ----------
    chips = []
    if proj.get("number"): chips.append(f'<span class="cpm-chip">No. <b>{esc(proj["number"])}</b></span>')
    if proj.get("location"): chips.append(f'<span class="cpm-chip">Location <b>{esc(proj["location"])}</b></span>')
    chips.append(f'<span class="cpm-chip">Phase <b id="phase-chip">{esc(str(phase).title())}</b></span>')
    if proj.get("is_joc"):
        joc = ident.get("joc", {}) if isinstance(ident.get("joc"), dict) else {}
        chips.append(f'<span class="cpm-chip joc">JOC coeff. <b>{esc(joc.get("coefficient", "—"))}</b></span>')
    out.append(f'''<header class="cpm-hero" id="overview">
      <div class="cpm-eyebrow">Single Source of Truth · CSI MasterFormat</div>
      <h1>{esc(proj.get("title", "Untitled Project"))}</h1>
      <div class="cpm-sub">{esc(proj.get("owner", ""))}</div>
      <div class="cpm-chips">{"".join(chips)}</div></header>''')

    # ---------- donut KPI row ----------
    by_div_val = {}
    for t in trades:
        v = trade_est(t["trade_id"]) or 0
        by_div_val[div_of(t)] = by_div_val.get(div_of(t), 0) + v
    val_slices = [(f"Div {d} {titles.get(d,'')}".strip(), v, colors.get(d, CAT_OTHER))
                  for d, v in sorted(by_div_val.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99) if v]
    qto_by_div = {}
    for q in qto:
        qto_by_div[div_of(q)] = qto_by_div.get(div_of(q), 0) + 1
    qto_slices = [(f"Div {d}", n, colors.get(d, CAT_OTHER)) for d, n in sorted(qto_by_div.items())]
    OPEN_SUB = ("required", "submitted", "under_review", "revise_resubmit")
    sub_open = [s for s in subm if s.get("status") in OPEN_SUB]
    sub_slices = [("Open", len(sub_open), CAT[1]), ("Approved / closed", max(len(subm) - len(sub_open), 0), CAT[0])]
    bids = [b for b in blog.get("bids", []) if isinstance(b, dict)]
    n_resp = sum(1 for b in bids if b.get("responded"))
    n_wait = max(len(bids) - n_resp, 0)
    bid_slices = [("Responded", n_resp, CAT[2]), ("Awaiting", n_wait, CAT_OTHER)]
    conf = (model.get("confidence") or {}).get("overall") or 0
    conf_slices = [("Confidence", round(conf * 100), CAT[0]), ("To verify", max(100 - round(conf * 100), 0), "rgba(255,255,255,.10)")]

    donuts = [
        donut_card("Budget by trade", f'<span class="num" data-target="{total_est}" data-pre="$">${total_est:,.0f}</span>',
                   val_slices or [("Pending", 1, CAT_OTHER)], glow="gold"),
        donut_card("Takeoff coverage", f'<span class="num" data-target="{len(qto)}">{len(qto)}</span>',
                   qto_slices or [("Pending", 1, CAT_OTHER)]),
        donut_card("Submittals", f'<span class="num" data-target="{len(sub_open)}">{len(sub_open)}</span>', sub_slices),
        donut_card("Bid responses", f'<span class="num" data-target="{n_resp}">{n_resp}</span>', bid_slices),
        donut_card("Confidence", f'<span class="num" data-target="{round(conf*100)}" data-suf="%">{round(conf*100)}%</span>',
                   conf_slices),
    ]
    out.append('<div class="donuts">' + "".join(reveal(dc, delay=i * 70) for i, dc in enumerate(donuts)) + '</div>')

    # ---------- segmented budget bar ----------
    seg_title = "Buyout Budget" if is_project else "Budget by Trade"
    seg_hint = ("Committed buyout by trade — profit shown in green. Click a segment for that trade's "
                "budget basis and exportable ITB." if is_project else
                "Click a segment for that trade's budget justification and exportable ITB.")
    segs, modals = [], []
    seg_total = total_est + ((profit or 0) if is_project else 0)
    denom = seg_total or 1
    for t in trades:
        tid = t["trade_id"]; est = trade_est(tid) or 0
        if est <= 0:
            continue
        d = div_of(t); pct = max(est / denom * 100, 4)
        mid = f"m-itb-{tid}"
        segs.append(f'''<div class="segw" style="width:{pct:.2f}%" data-modal="{mid}"
            data-tip="<b>Div {d} — {esc(t.get("name",""))}</b><br>{fmt_money(est)} · click for budget basis / ITB">
          <span class="amt">{fmt_money(est)}</span>
          <div class="segfill" style="background:linear-gradient(180deg,{colors.get(d, CAT_OTHER)}dd,{colors.get(d, CAT_OTHER)})"></div>
          <span class="nm">Div {esc(d)} · {esc(t.get("name",""))}</span></div>''')
        modals.append(itb_modal(mid, t, ident, contacts,
                                [b for b in budget_lines if b.get("trade_id") == tid],
                                est, company, titles, colors))
    if is_project and profit:
        pct = max(profit / denom * 100, 4)
        segs.append(f'''<div class="segw profit-seg" style="width:{pct:.2f}%" data-tip="<b>Profit</b><br>{fmt_money(profit)} held in the buyout">
          <span class="amt profit">▲ {fmt_money(profit)}</span>
          <div class="segfill profit"></div><span class="nm">Profit</span></div>''')
    out.append(f'''<section class="cpm-section" id="budget">
      <h2><span id="bt-title" data-est="Budget by Trade" data-proj="Buyout Budget">{seg_title}</span>{health_dot(health, "budget")}</h2>
      <div class="hint" id="bt-hint" data-est="Click a segment for that trade's budget justification and exportable ITB."
        data-proj="Committed buyout by trade — profit shown in green. Click a segment for that trade's budget basis and exportable ITB.">{seg_hint}</div>
      {reveal(f'<div class="segbar"><div class="segrow">{"".join(segs)}</div>'
              f'<div class="segtotal"><span class="t" id="bt-total" data-est="Total estimate" data-proj="Contract total">{"Contract total" if is_project else "Total estimate"}</span>'
              f'<span class="v num" data-target="{seg_total}" data-pre="$">${seg_total:,.0f}</span></div></div>')}
    </section>''')

    # ---------- activity stream ----------
    if stream:
        stream.sort(key=lambda e: e.get("ts") or "", reverse=True)
        items = []
        for i, e in enumerate(stream[:8]):
            if e.get("image"):
                thumb = f'<img class="sthumb" src="{esc(e["image"])}" alt="">'
            elif e.get("kind") == "pdf_snip":
                thumb = '<div class="sdoc">PDF<br>SNIP</div>'
            elif e.get("kind") == "email_summary":
                thumb = '<div class="sdoc" style="color:var(--blue);border-color:rgba(79,150,216,.45);background:linear-gradient(160deg,rgba(79,150,216,.12),rgba(79,150,216,.03))">EMAIL</div>'
            elif e.get("kind") == "meeting_minutes":
                thumb = '<div class="sdoc" style="color:#a98fd8;border-color:rgba(126,88,194,.5);background:linear-gradient(160deg,rgba(126,88,194,.14),rgba(126,88,194,.04))">MTG<br>MIN</div>'
            else:
                thumb = '<div class="sdoc" style="color:var(--blue);border-color:rgba(79,150,216,.4)">LOG</div>'
            ts = esc(str(e.get("ts", ""))[:16].replace("T", " · "))
            items.append(reveal(f'''<div class="sitem">{thumb}<div>
              <div class="tx">{esc(e.get("text",""))}</div>
              <div class="meta"><span class="srcchip">{esc(e.get("source","sync"))}</span>
              <span>{ts}</span>{f'<span>{esc(e.get("doc_ref"))}</span>' if e.get("doc_ref") else ""}</div>
            </div></div>''', delay=i * 45))
        out.append(f'''<section class="cpm-section" id="activity">
          <h2>Activity Stream{health_dot(health, "activity")}</h2>
          <div class="hint">Synced one-way from JobTread and the document set — photos, PDF snips, and field notes, newest first.</div>
          <div class="stream">{"".join(items)}</div></section>''')

    # ---------- daily report cards ----------
    if reports:
        reports.sort(key=lambda r: r.get("date") or "")
        cards = []
        for i, r in enumerate(reports[-5:]):
            d = parse_date(r.get("date"))
            tint = "#3f78b5"  # one steel-blue glass tint — flags carry the color meaning
            banners = "".join(
                f'<div class="fbanner" style="background:linear-gradient(90deg,{FLAG_COLORS.get(f.get("kind","other"), CAT_OTHER)}e6,{FLAG_COLORS.get(f.get("kind","other"), CAT_OTHER)}99)">'
                f'{esc(f.get("kind","")).upper()} · {esc(f.get("text",""))}</div>'
                for f in r.get("flags", []) if isinstance(f, dict))
            meta_parts = [esc(x) for x in [d.strftime("%a %b") if d else "", r.get("weather", "")] if x]
            if r.get("crew_count"):
                meta_parts.append(f'crew&nbsp;{esc(r["crew_count"])}')
            meta = " · ".join(meta_parts)
            cards.append(reveal(
                f'''<a class="daycard" href="{esc(r.get("url") or "#")}" {'target="_blank" rel="noopener"' if r.get("url") else ""}
                    style="background:linear-gradient(165deg,{tint}2e,{tint}14 45%,rgba(20,23,28,.72))"
                    data-tip="Open the JobTread daily report — summary, photos, and crew log">
                  <div class="flags">{banners}</div><span class="go">open ↗</span>
                  <div class="body"><div class="dnumber">{d.day if d else "–"}</div>
                    <div class="dmeta">{meta}</div>
                    <div class="dsum">{esc(r.get("summary",""))}</div></div></a>''', delay=i * 60))
        out.append(f'''<section class="cpm-section" id="daily">
          <h2>Daily Reports{health_dot(health, "daily_reports")}</h2>
          <div class="hint">The last five field days — flags at the top come from meeting and workplace intelligence. Click through for the full JobTread report.</div>
          <div class="days">{"".join(cards)}</div></section>''')

    # ---------- open submittals + RFIs | critical path plotter ----------
    def sub_row(s):
        lead = s.get("lead_time_weeks")
        hot = ' hot' if isinstance(lead, (int, float)) and lead >= 8 else ''
        return (f'<div class="brow"><span class="id">{esc(s.get("spec_section",""))}</span>'
                f'<span>{esc(s.get("description",""))}</span>'
                f'<span class="lead{hot}">{f"{lead:g} wks lead" if isinstance(lead,(int,float)) else esc(s.get("status",""))}</span></div>')
    open_rfis = [r for r in rfis if r.get("status", "open") in ("open", "unknown")]
    def rfi_row(r):
        return (f'<div class="brow"><span class="id">{esc(r.get("rfi_id",""))}</span>'
                f'<span>{esc(r.get("subject",""))}</span>'
                f'<span class="lead">{esc(r.get("ball_in_court","") or r.get("status",""))}</span></div>')
    citems = sorted([c for c in crit.get("items", []) if isinstance(c, dict)], key=lambda c: c.get("rank", 999))
    pev = []
    for c in citems:
        crit_cls = " crit" if c.get("driver") in ("long_lead", "permit", "design_gap", "owner_decision") else ""
        pev.append(f'''<div class="pev{crit_cls}"><div class="pd">#{esc(c.get("rank",""))} · Div {esc(div_of(c))}</div>
          <div class="pl">{esc(c.get("description",""))}</div><div class="pr">{esc(c.get("reason",""))}</div></div>''')
    for m in sorted([m for m in sched.get("milestones", []) if isinstance(m, dict)], key=lambda m: m.get("date") or "9999"):
        pev.append(f'''<div class="pev"><div class="pd">{esc(m.get("date") or m.get("relative_to") or "TBD")}</div>
          <div class="pl">{esc(m.get("label",""))}</div></div>''')
    sub_rows = "".join(sub_row(s) for s in sub_open) or '<div class="brow">All submittals are in a good place.</div>'
    rfi_rows = "".join(rfi_row(r) for r in open_rfis) or '<div class="brow">No open RFIs — nicely done.</div>'
    sub_lt = (health.get("submittals") or {}).get("status", "green")
    rfi_lt = (health.get("rfis") or {}).get("status", "green")
    sub_block = reveal(f'<div class="block"><h3><span class="lt {sub_lt}"></span>Open Submittals'
                       f'<span class="cnt">{len(sub_open)}</span></h3>{sub_rows}</div>')
    rfi_block = reveal(f'<div class="block"><h3><span class="lt {rfi_lt}"></span>Open RFIs'
                       f'<span class="cnt">{len(open_rfis)}</span></h3>{rfi_rows}</div>', delay=80)
    plotter = reveal('<div class="block plotter"><h3>Critical Path Plotter</h3>'
                     f'<div class="pvp" id="pvp"><div class="pline">{"".join(pev)}</div></div>'
                     '<div class="pbtns"><button class="pbtn" data-scroll="pvp" data-dir="up">&#9650;</button>'
                     '<button class="pbtn" data-scroll="pvp" data-dir="down">&#9660;</button></div></div>', delay=140)
    out.append(f'''<section class="cpm-section" id="openitems">
      <h2>Open Items &amp; Critical Path{health_dot(health, "open_items")}</h2>
      <div class="duo" style="margin-top:20px">
        <div style="display:grid;gap:16px;align-content:start">{sub_block}{rfi_block}</div>
        {plotter}
      </div></section>''')

    # ---------- three-week look-ahead ----------
    la = [x for x in sched.get("lookahead", []) if isinstance(x, dict)]
    weeks = week_bounds(anchor)
    week_names = ["Last Week", "This Week", "Next Week"]
    panels = []
    for wi, (w0, w1) in enumerate(weeks):
        rows = []
        for x in sorted(la, key=lambda x: x.get("start") or ""):
            s = parse_date(x.get("start")); e = parse_date(x.get("end")) or s
            if not s or e < w0 or s > w1:
                continue
            is_crit = bool(x.get("is_critical"))
            is_del = x.get("type") == "delivery"
            cls = "crit" if is_crit else ("deliv" if is_del else "")
            chip = ('<span class="typechip crit">Critical</span>' if is_crit else
                    ('<span class="typechip deliv">Delivery</span>' if is_del else
                     f'<span class="typechip">{esc(x.get("type","task"))}</span>'))
            rows.append(f'''<tr class="{cls}"><td>{esc(x.get("label",""))}</td>
              <td>{divtag(div_of(x), titles, colors)}</td><td>{chip}</td>
              <td class="num" contenteditable="true">{fmt_day(s)}</td>
              <td class="num" contenteditable="true">{fmt_day(e)}</td>
              <td contenteditable="true">{esc(x.get("status",""))}</td>
              <td contenteditable="true">{esc(x.get("notes",""))}</td></tr>''')
        body = "".join(rows) or f'<tr><td colspan="7" style="color:var(--faint)">Nothing scheduled {week_names[wi].lower()} — a good window to get ahead.</td></tr>'
        panels.append(f'''<div class="la-panel"><div class="cpm-card"><table class="cpm-table">
          <thead><tr><th>Item</th><th>Div</th><th>Type</th><th>Start</th><th>End</th><th>Status</th><th>Notes</th></tr></thead>
          <tbody>{body}</tbody></table></div></div>''')
    tabs = "".join(f'<button class="la-tab" data-idx="{i}" aria-selected="{"true" if i == 1 else "false"}">{n}'
                   f'<span class="num" style="margin-left:8px;color:var(--faint)">{fmt_day(weeks[i][0])}–{fmt_day(weeks[i][1])}</span></button>'
                   for i, n in enumerate(week_names))
    out.append(f'''<section class="cpm-section" id="lookahead">
      <h2>Three-Week Look-ahead{health_dot(health, "schedule")}</h2>
      <div class="hint">Red stripe = critical path · blue stripe = deliveries. Click any date, status, or note to edit — edits stay local until the next approved sync.</div>
      <div class="la-tabs">{tabs}</div>
      {reveal(f'<div class="la-view"><div class="la-track" id="la-track" style="transform:translateX(-33.3334%)">{"".join(panels)}</div></div>')}
    </section>''')

    # ---------- focus areas (constructive) ----------
    nr = model.get("needs_human_review", [])
    if nr:
        lis = "".join(f"<li>{esc(x)}</li>" for x in nr[:30])
        out.append(f'''<section class="cpm-section"><h2>Focus Areas{health_dot(health, "focus", "yellow")}</h2>
          <div class="hint">Worth a look when you have a minute — verifying these keeps the record airtight.</div>
          {reveal(f'<div class="review"><ul style="margin:0;padding-left:18px">{lis}</ul></div>')}</section>''')

    # ---------- suggestions modal ----------
    KIND_LABEL = {"meeting": "Suggested meeting", "schedule_change": "Schedule move",
                  "budget_adjustment": "Budget adjustment", "change_order": "Change-order candidate",
                  "constraint_solution": "Constraint solution", "alternate": "Alternate spec / supplier"}
    scards = "".join(
        f'''<div class="sugg"><div class="k">{esc(KIND_LABEL.get(s.get("kind"), "Suggestion"))}</div>
          <div class="t">{esc(s.get("title",""))}</div><div class="rz">{esc(s.get("rationale",""))}</div>
          <div class="acts"><button class="btn approve">Approve</button><button class="btn hold">Hold</button></div></div>'''
        for s in suggestions) or '<p style="color:var(--muted)">No pending suggestions — the record is settled. New ones appear here after each sync.</p>'
    out.append(f'''<div class="mmask" id="m-suggest"><div class="modal">
      <div class="mhead"><h3>Recommended next moves</h3><button class="x" aria-label="Close">✕</button></div>
      <div class="mbody">
        <p style="font-size:13px;color:var(--muted);margin:0 0 16px">Here's what I'd do next, with the reasoning laid out —
        nothing here is urgent-by-surprise, and none of it syncs to your tools until you approve it. Take what's useful.</p>
        {scards}
        <div id="followup"><p style="font-size:13px;color:var(--muted)">No problem. Want a narrower sync instead?</p>
          <div class="acts" style="display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn" data-scope-sync="schedule">Schedule only</button>
            <button class="btn" data-scope-sync="documents">Documents only</button>
            <button class="btn" data-scope-sync="contacts">Contacts only</button>
            <button class="btn" data-scope-sync="none">No sync — keep it here</button></div></div>
      </div>
      <div class="mfoot"><button class="btn primary" id="queue-sync">Approve &amp; queue two-way sync</button>
        <button class="btn" id="not-now">Not now</button>
        <button class="btn x" style="margin-left:auto">Close</button></div></div></div>''')

    out.extend(modals)

    # ---------- footer ----------
    gen = esc(model.get("generated_at", ""))
    out.append(f'''<footer class="cpm-foot">Rendered from <span class="num">canonical-model.json</span> ·
      classification: CSI MasterFormat · connectors sync one-way in (last five days first); outbound changes only
      through approved suggestions · this view organizes and presents — pricing, leveling, and award decisions
      stay with your team.{(" · generated " + gen) if gen else ""}</footer>''')
    out.append('</div>')
    out.append('<div id="tip"></div><div class="toast" id="toast"></div>')
    out.append(f'<script type="text/template" id="itb-export-css">{ITB_EXPORT_CSS}</script>')
    return "".join(out)


# ------------------------------------------------------------------ assembly

def build(args):
    model = load_json(args.model)
    if not model:
        log(f"could not load model: {args.model}"); sys.exit(2)
    model_dir = Path(args.model).resolve().parent

    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "project": model.get("project", {}),
            "layout": ["sync pills", "hero", "5 donut KPI cards", "segmented budget bar (click → ITB modal; buyout+profit when phase=project)",
                       "activity stream", "5 daily-report cards", "open submittals + open RFIs | critical-path plotter",
                       "3-week look-ahead (editable)", "focus areas", "suggestions modal (two-way sync approval)"],
            "palette": CAT, "note": "stdlib only; fully self-contained output",
        }, indent=2))
        return

    titles = load_division_titles()
    body = build_body(model, model_dir, args.company, titles)
    bg = ('<div class="cpm-bg"></div><div class="cpm-bg2"></div>'
          f'<div class="cpm-stars s1" style="background-image:url(\'{constellation(72, seed=7)}\')"></div>'
          f'<div class="cpm-stars s2" style="background-image:url(\'{constellation(44, seed=23, bright=True)}\')"></div>')
    noscript = ('<noscript><style>.reveal{opacity:1!important;transform:none!important}'
                '.la-track{transform:translateX(-33.3334%)!important}</style></noscript>')

    phase_cls = "phase-project" if (model.get("project", {}).get("phase") in ("project", "closeout")) else "phase-estimate"
    if args.fragment:
        doc = f'<style>{STYLE}</style>{noscript}\n<div class="cpm-root {phase_cls}">{bg}{body}</div>\n<script>{SCRIPT}</script>'
    else:
        title = esc(model.get("project", {}).get("title", "Project Dashboard"))
        doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
               f'<meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>{title} · {esc(args.company)}</title>'
               f'<style>{STYLE}</style>{noscript}</head>'
               f'<body class="cpm-root {phase_cls}">{bg}{body}<script>{SCRIPT}</script></body></html>')

    out = Path(args.out) if args.out else model_dir / f'{model.get("project", {}).get("slug", "project")}.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc)
    log(f"wrote dashboard: {out}  ({len(doc):,} bytes, {'fragment' if args.fragment else 'standalone'})")
    print(json.dumps({"dashboard": str(out), "bytes": len(doc),
                      "mode": "fragment" if args.fragment else "standalone"}, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Render the Canonical Project Record to an animated HTML dashboard (v2).")
    ap.add_argument("--model", required=True, help="Path to canonical-model.json.")
    ap.add_argument("--out", help="Output .html path (default <model_dir>/<slug>.html).")
    ap.add_argument("--company", default=DEFAULT_COMPANY, help="Branding/company name (default NTXP).")
    ap.add_argument("--fragment", action="store_true", help="Emit body content only for embedding.")
    ap.add_argument("--dry-run", action="store_true", help="Print the planned layout without rendering.")
    build(ap.parse_args())


if __name__ == "__main__":
    main()
