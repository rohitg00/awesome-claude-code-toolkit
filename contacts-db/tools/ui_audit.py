#!/usr/bin/env python3
"""Front-end design audit for the NTXP Contacts live page.

Mechanical, repeatable checks against (a) NTXP-DOC-STANDARD 2.1 and (b) WCAG 2.2 AA:
  standard  header geometry, font, caps/weight, accent fade, palette tokens, retired colours
  palette   every solid colour painted in the default theme must be a declared token
  contrast  WCAG contrast of all visible text, in every theme x palette
  align     doctrine: cells centred, paragraph columns left, cells top-aligned
  wrap      emails / phones never wrap mid-string (the doc engine's own audit rule)
  targets   interactive controls >= 24x24 CSS px (WCAG 2.5.8)
  layout    no page-level horizontal scroll 360..1920; export buttons never cover data
  keyboard  Tab reaches the key controls, each with a visible focus indicator
  axe       axe-core ruleset across table / drawer / settings / report / mobile states

Usage:  python tools/ui_audit.py http://127.0.0.1:8099 out_dir
Needs:  playwright (+chromium), axe-playwright-python.  Exit 1 on any failure.
"""
import json, os, sys
from playwright.sync_api import sync_playwright
from axe_playwright_python.sync_playwright import Axe

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099"
OUT = sys.argv[2] if len(sys.argv) > 2 else "ui_audit_out"
os.makedirs(OUT, exist_ok=True)

STD = {  # NTXP-DOC-STANDARD 2.1 tokens (+ owner-directed baby blue for the REPORTS drawer)
    "#1b2a4e", "#182746", "#16224a", "#46567d", "#35446b", "#c8102e", "#d0353c", "#b92a32",
    "#f6f3ef", "#e2dad0", "#cdc0b2", "#2f529b", "#1f2a3d", "#5a6880", "#ffffff", "#bfe0f5", "#10304a"}
RETIRED = {"#c9a227", "#e3c866", "#ffd700", "#d4a843"}
RESULTS = []


def rec(area, name, ok, detail=""):
    RESULTS.append({"area": area, "check": name, "pass": bool(ok), "detail": str(detail)[:400]})
    print(("PASS " if ok else "FAIL ") + f"[{area}] {name}" + (f" — {detail}" if detail and not ok else ""))


JS_CONTRAST = """() => {
 const P=c=>{const m=c.match(/rgba?\\(([^)]+)\\)/);const p=m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number);return{r:p[0],g:p[1],b:p[2],a:p[3]===undefined?1:p[3]}};
 const over=(f,b)=>({r:f.r*f.a+b.r*(1-f.a),g:f.g*f.a+b.g*(1-f.a),b:f.b*f.a+b.b*(1-f.a),a:1});
 const L=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b)};
 const bg=el=>{const st=[];for(let e=el;e;e=e.parentElement){const c=P(getComputedStyle(e).backgroundColor);if(c.a>0)st.push(c);if(c.a>=1)break}
   let base={r:255,g:255,b:255,a:1};for(let i=st.length-1;i>=0;i--)base=over(st[i],base);return base};
 const bad=[];let n=0;
 for(const el of document.querySelectorAll('body *')){
   if(el.closest('.accent,.sr,script,style,#gate[hidden]')||!el.offsetParent&&getComputedStyle(el).position!=='fixed')continue;
   const own=[...el.childNodes].some(x=>x.nodeType===3&&x.textContent.trim());if(!own)continue;
   const cs=getComputedStyle(el);if(cs.visibility==='hidden'||cs.display==='none')continue;
   if(el.disabled)continue; const r=el.getBoundingClientRect(); if(r.width===0||r.height===0)continue;
   const fg=over(P(cs.color),bg(el)),b=bg(el),l1=L(fg),l2=L(b),ratio=(Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05);
   const size=parseFloat(cs.fontSize),bold=parseInt(cs.fontWeight)>=700,large=size>=24||(size>=18.66&&bold);n++;
   if(ratio<(large?3:4.5))bad.push((el.tagName+'.'+(el.className||'')).slice(0,50)+' "'+el.textContent.trim().slice(0,24)+'" '+ratio.toFixed(2));
 }
 return {n,bad:[...new Set(bad)].slice(0,12)}}"""

JS_PALETTE = """() => {
 const hex=c=>{const m=c.match(/rgba?\\(([^)]+)\\)/);const p=m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number);if(p[3]!==undefined&&p[3]<1)return null;
   return '#'+p.slice(0,3).map(v=>Math.round(v).toString(16).padStart(2,'0')).join('')};
 const seen={};
 for(const el of document.querySelectorAll('body *')){
   if(el.closest('.accent,.sr,#gate,.doc,.toast')||!el.offsetParent&&getComputedStyle(el).position!=='fixed')continue;
   const cs=getComputedStyle(el),use=(c,k)=>{const h=hex(c);if(h)(seen[h]=seen[h]||new Set()).add(k)};
   const own=[...el.childNodes].some(x=>x.nodeType===3&&x.textContent.trim());
   if(own)use(cs.color,'text:'+el.tagName.toLowerCase()+'.'+(el.className||'').toString().split(' ')[0]);
   use(cs.backgroundColor,'bg:'+el.tagName.toLowerCase()+'.'+(el.className||'').toString().split(' ')[0]);
   if(parseFloat(cs.borderTopWidth)>0)use(cs.borderTopColor,'border:'+el.tagName.toLowerCase()+'.'+(el.className||'').toString().split(' ')[0]);
 }
 return Object.fromEntries(Object.entries(seen).map(([k,v])=>[k,[...v].slice(0,3)]))}"""


def settle(pg):
    pg.wait_for_selector("#tb tr[data-id]")
    pg.wait_for_timeout(300)


def set_theme(pg, theme, palette):
    pg.evaluate("([t,p])=>{document.documentElement.dataset.theme=t;document.documentElement.dataset.palette=p}", [theme, palette])
    pg.wait_for_timeout(120)


def axe_run(pg, label):
    r = Axe().run(pg).response
    v = r["violations"]
    serious = [x for x in v if x["impact"] in ("serious", "critical")]
    rec("axe", f"{label}: no serious/critical violations", not serious,
        "; ".join(f"{x['id']}({len(x['nodes'])}) {x['nodes'][0]['html'][:70]}" for x in serious))
    rest = [x for x in v if x["impact"] not in ("serious", "critical")]
    rec("axe", f"{label}: no moderate/minor violations", not rest,
        "; ".join(f"{x['id']}({x['impact']}) {x['nodes'][0]['html'][:70]}" for x in rest))


with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_context(viewport={"width": 1440, "height": 900}).new_page()
    pg.goto(BASE + "/"); settle(pg)

    # ---------- standard ----------
    g = pg.evaluate("""()=>{const b=document.querySelector('.band'),a=document.querySelector('.accent'),h=document.querySelector('.lockup h1'),
      cs=getComputedStyle,R=e=>e.getBoundingClientRect(),root=cs(document.documentElement);
      return {band:R(b).height,accent:R(a).height,accBg:cs(a).backgroundImage,font:cs(document.body).fontFamily,
      tt:cs(h).textTransform,fw:cs(h).fontWeight,ta:cs(h.parentElement).textAlign,
      tok:['--navy','--navy-mid','--accent','--warm','--warm-line','--warm-edge','--link','--ink','--red','--red-ink'].map(k=>[k,root.getPropertyValue(k).trim().toLowerCase()]),
      bar:cs(document.querySelector('.bar')).textTransform,barA:cs(document.querySelector('.bar')).textAlign,
      rowB:cs(document.querySelector('#tb tr:nth-child(2) td')).backgroundColor,rowA:cs(document.querySelector('#tb tr:nth-child(1) td')).backgroundColor}}""")
    rec("standard", "navy band is 1.00in (96px)", abs(g["band"] - 96) <= 1, g["band"])
    rec("standard", "accent band is 0.085in (~8px) with a red fade over navy", 7 <= g["accent"] <= 9 and "linear-gradient" in g["accBg"] and "200, 16, 46" in g["accBg"], f'{g["accent"]} {g["accBg"][:60]}')
    rec("standard", "Open Sans is the type", "Open Sans" in g["font"], g["font"][:40])
    rec("standard", "title: bold, upright, ALL CAPS, centred lockup", g["tt"] == "uppercase" and int(g["fw"]) >= 700 and g["ta"] == "center", f'{g["tt"]} {g["fw"]} {g["ta"]}')
    rec("standard", "section bar: white caps, centred", g["bar"] == "uppercase" and g["barA"] == "center")
    want = {"--navy": "#1b2a4e", "--navy-mid": "#46567d", "--accent": "#c8102e", "--warm": "#f6f3ef", "--warm-line": "#e2dad0", "--warm-edge": "#cdc0b2", "--link": "#2f529b", "--ink": "#1f2a3d", "--red": "#d0353c", "--red-ink": "#b92a32"}
    bad = [f"{k}={v}" for k, v in g["tok"] if want[k] != v]
    rec("standard", "default palette tokens equal the engine's exactly", not bad, bad)
    rec("standard", "two-tone rows: row A transparent (the paper), row B warm #F6F3EF", g["rowA"] in ("rgb(255, 255, 255)", "rgba(0, 0, 0, 0)") and g["rowB"] == "rgb(246, 243, 239)", f'{g["rowA"]} / {g["rowB"]}')

    # ---------- palette audit (default theme) ----------
    seen = pg.evaluate(JS_PALETTE)
    retired = {k: v for k, v in seen.items() if k in RETIRED}
    rogue = {k: v for k, v in seen.items() if k not in STD}
    rec("palette", "no retired colours (gold is not an NTXP colour)", not retired, retired)
    rec("palette", "every solid colour painted is a declared token", not rogue, {k: v for k, v in list(rogue.items())[:6]})

    # ---------- alignment doctrine ----------
    al = pg.evaluate("""()=>{const bad=[];document.querySelectorAll('#tb tr[data-id]:nth-child(-n+6) td').forEach(td=>{const cs=getComputedStyle(td),para=td.classList.contains('para');
      if(cs.verticalAlign!=='top')bad.push('valign '+td.dataset.col);
      if(para&&cs.textAlign!=='left'&&cs.textAlign!=='start')bad.push('para not left '+td.dataset.col);
      if(!para&&cs.textAlign!=='center'&&!td.querySelector('.nm'))bad.push('not centred '+td.dataset.col)});
      document.querySelectorAll('#thr th').forEach(th=>{if(getComputedStyle(th.firstElementChild).justifyContent!=='center')bad.push('header not centred')});return bad}""")
    rec("align", "cells centred, paragraph columns left, all top-aligned, headers centred", not al, al[:5])

    # ---------- link wraps ----------
    for v in ("1", "3", "5"):
        pg.click(f'.seg [data-v="{v}"]')
        w = pg.evaluate("""()=>[...document.querySelectorAll('#tb a[href^="mailto:"],#tb a[href^="tel:"]')].filter(a=>a.getClientRects().length>1).map(a=>a.textContent)""")
        rec("wrap", f"VIEW {v}: no email/phone wraps mid-string", not w, w[:3])
    pg.click('.seg [data-v="1"]')

    # ---------- tap targets ----------
    tt = pg.evaluate("""()=>[...document.querySelectorAll('button,input:not([type=hidden]),select,[role=button],[role=switch]')].filter(e=>e.offsetParent&&!e.closest('[hidden]')&&!e.closest('.sr')).map(e=>{const r=e.getBoundingClientRect();return[(e.id||e.className||e.tagName).toString().slice(0,30),r.width,r.height]}).filter(x=>x[1]<24||x[2]<24)""")
    rec("targets", "all controls are at least 24x24 CSS px (WCAG 2.5.8)", not tt, tt[:5])

    # ---------- keyboard (fresh page: a prior click would move the Tab origin) ----------
    pg.goto(BASE + "/"); settle(pg)
    reached, nofocus = set(), []
    for _ in range(45):
        pg.keyboard.press("Tab")
        info = pg.evaluate("""()=>{const e=document.activeElement,cs=getComputedStyle(e);return{id:e.id||(e.dataset&&(e.dataset.sort||e.dataset.acc||e.dataset.v))||e.tagName,
          ring:(cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>0)||cs.boxShadow!=='none'}}""")
        reached.add(str(info["id"]))
        if not info["ring"]:
            nofocus.append(info["id"])
    need = {"ham", "railToggle", "q", "name", "company"}
    rec("keyboard", "Tab reaches menu, filters, search and sortable headers", need <= reached, f"missing {need - reached}")
    rec("keyboard", "every focused control shows a visible focus indicator", not nofocus, nofocus[:4])

    # ---------- contrast: every theme x palette ----------
    for theme, pal in [("light", "ntxp"), ("dark", "ntxp"), ("light", "field"), ("light", "slate"), ("light", "graphite"), ("dark", "graphite"), ("dark", "slate")]:
        set_theme(pg, theme, pal)
        c = pg.evaluate(JS_CONTRAST)
        rec("contrast", f"{theme}/{pal}: all {c['n']} text runs meet WCAG AA", not c["bad"], c["bad"][:4])
    set_theme(pg, "light", "ntxp")

    # ---------- axe across states ----------
    axe_run(pg, "table (desktop, light)")
    set_theme(pg, "dark", "ntxp"); axe_run(pg, "table (desktop, dark)"); set_theme(pg, "light", "ntxp")
    pg.click("#ham"); pg.wait_for_timeout(400); axe_run(pg, "reports drawer open")
    pg.click("#gear"); pg.wait_for_selector("#panel:not([hidden])"); axe_run(pg, "settings panel open")
    pg.screenshot(path=f"{OUT}/settings.png"); pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    pg.click("#ham"); pg.wait_for_timeout(400); pg.click('[data-rep="directory"]'); pg.wait_for_selector("#doc .d-card"); pg.wait_for_timeout(300)
    axe_run(pg, "report view"); pg.screenshot(path=f"{OUT}/report.png"); pg.click("#rvBack")

    # ---------- layout / responsive ----------
    for w in (360, 390, 768, 1024, 1280, 1440, 1920):
        pgw = br.new_context(viewport={"width": w, "height": 900}).new_page(); pgw.goto(BASE + "/"); settle(pgw)
        ov = pgw.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        rec("layout", f"{w}px: no page-level horizontal scroll", ov <= 0, f"{ov}px")
        if w > 900:
            hit = pgw.evaluate("""()=>{const t=document.querySelector('#tableView .card').getBoundingClientRect();return [...document.querySelectorAll('.exports .btn')].some(b=>{const r=b.getBoundingClientRect();return !(r.right<=t.left||r.left>=t.right||r.bottom<=t.top||r.top>=t.bottom)})}""")
            rec("layout", f"{w}px: floating export buttons never cover the table", not hit)
        if w <= 390:
            pgw.screenshot(path=f"{OUT}/mobile_{w}.png")
            axe_run(pgw, f"{w}px mobile table")
            pgw.click("#railToggle"); axe_run(pgw, f"{w}px mobile, filters open")
        pgw.context.close()
    pg.screenshot(path=f"{OUT}/desktop.png")
    br.close()

fails = [r for r in RESULTS if not r["pass"]]
json.dump(RESULTS, open(f"{OUT}/audit.json", "w"), indent=1)
print(f"\nAUDIT: {len(RESULTS) - len(fails)}/{len(RESULTS)} checks pass")
sys.exit(1 if fails else 0)
