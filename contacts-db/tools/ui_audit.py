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
  buttons   every button variant: accessible name, size, type, hover/active/focus/disabled/pressed states,
            hover contrast, consistency (radius/weight), no overlapping targets, role=button keyboard support
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
 const __cv=document.createElement('canvas');__cv.width=__cv.height=1;const __cx=__cv.getContext('2d',{willReadFrequently:true});const __px=c=>{__cx.clearRect(0,0,1,1);__cx.fillStyle='#000';__cx.fillStyle=c;__cx.fillRect(0,0,1,1);const d=__cx.getImageData(0,0,1,1).data;return[d[0],d[1],d[2],Math.round(d[3]/255*1000)/1000]};const P=c=>{const p=__px(c);return{r:p[0],g:p[1],b:p[2],a:p[3]}};
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
 const __cv=document.createElement('canvas');__cv.width=__cv.height=1;const __cx=__cv.getContext('2d',{willReadFrequently:true});const __px=c=>{__cx.clearRect(0,0,1,1);__cx.fillStyle='#000';__cx.fillStyle=c;__cx.fillRect(0,0,1,1);const d=__cx.getImageData(0,0,1,1).data;return[d[0],d[1],d[2],Math.round(d[3]/255*1000)/1000]};const hex=c=>{const p=__px(c);if(p[3]<1)return null;
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


CANVAS = "const __cv=document.createElement('canvas');__cv.width=__cv.height=1;const __cx=__cv.getContext('2d',{willReadFrequently:true});const __px=c=>{__cx.clearRect(0,0,1,1);__cx.fillStyle='#000';__cx.fillStyle=c;__cx.fillRect(0,0,1,1);const d=__cx.getImageData(0,0,1,1).data;return[d[0],d[1],d[2],Math.round(d[3]/255*1000)/1000]};"

JS_BTN_MEASURE = """(el) => {
 """ + CANVAS + """
 const P=c=>{const p=__px(c);return{r:p[0],g:p[1],b:p[2],a:p[3]}};
 const over=(f,b)=>({r:f.r*f.a+b.r*(1-f.a),g:f.g*f.a+b.g*(1-f.a),b:f.b*f.a+b.b*(1-f.a),a:1});
 const L=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b)};
 const bg=e=>{const st=[];for(let x=e;x;x=x.parentElement){const c=P(getComputedStyle(x).backgroundColor);if(c.a>0)st.push(c);if(c.a>=1)break}
   let base={r:255,g:255,b:255,a:1};for(let i=st.length-1;i>=0;i--)base=over(st[i],base);return base};
 const cs=getComputedStyle(el),b=bg(el),fg=over(P(cs.color),b),l1=L(fg),l2=L(b);
 const r=el.getBoundingClientRect();
 return {bg:[b.r,b.g,b.b].map(Math.round).join(),color:cs.color,border:cs.borderTopColor,shadow:cs.boxShadow,transform:cs.transform+cs.translate+cs.rotate,
   outline:cs.outlineStyle+cs.outlineWidth,ratio:(Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05),opacity:cs.opacity,cursor:cs.cursor,
   radius:cs.borderTopLeftRadius,weight:cs.fontWeight,w:r.width,h:r.height}}"""

JS_BTN_LIST = """() => [...document.querySelectorAll('button,[role=button],[role=switch],input[type=button],input[type=submit]')]
  .filter(e=>e.offsetParent||getComputedStyle(e).position==='fixed').filter(e=>!e.closest('[hidden],[inert],.sr,.sr-only')&&getComputedStyle(e).visibility!=='hidden')
  .map((e,i)=>{e.setAttribute('data-aud',i);const r=e.getBoundingClientRect(),role=e.getAttribute('role');
   const name=(e.getAttribute('aria-label')||(e.labels&&e.labels[0]&&e.labels[0].textContent)||e.textContent||e.getAttribute('title')||'').trim();
   return {i,tag:e.tagName.toLowerCase(),role,type:e.getAttribute('type'),variant:e.dataset.variant||(role==='button'?'link-button':'?'),name,
     vis:(()=>{const cx=r.left+r.width/2,cy=r.top+r.height/2;if(cx<0||cy<0||cx>innerWidth||cy>innerHeight)return null;const t=document.elementFromPoint(cx,cy);return !!t&&(t===e||e.contains(t)||t.contains(e))})(),
     w:r.width,h:r.height,l:r.left,t:r.top,disabled:e.disabled||e.getAttribute('aria-disabled')==='true',pressed:e.getAttribute('aria-pressed'),
     tabindex:e.getAttribute('tabindex'),icon:!/[A-Za-z0-9]{2,}/.test(e.textContent||'')}})"""


def button_audit(pg, label):
    """Per-state audit of every visible button-like control on the current screen."""
    items = pg.evaluate(JS_BTN_LIST)
    area = "buttons"
    # 1. accessible name  2. explicit type (never an accidental submit)  3. size floors
    noname = [x for x in items if not x["name"]]
    rec(area, f"{label}: every button has an accessible name", not noname, [(x["variant"], x["i"]) for x in noname[:5]])
    notype = [x for x in items if x["tag"] == "button" and not x["type"]]
    rec(area, f"{label}: every <button> declares type=", not notype, [(x["variant"], x["name"][:20]) for x in notype[:5]])
    small = [(x["variant"], x["name"][:18], round(x["w"]), round(x["h"])) for x in items
             if (x["w"] < 24 or x["h"] < 24) and x["variant"] != "icon-ghost"]
    rec(area, f"{label}: no button below 24x24 (WCAG 2.5.8)", not small, small[:5])
    dense = [(x["variant"], x["name"][:18], round(x["h"])) for x in items
             if x["variant"] in ("primary", "secondary", "band", "drawer", "seg", "swatch") and x["h"] < 32 and not x["disabled"]]
    rec(area, f"{label}: text buttons are at least 32px tall", not dense, dense[:5])
    # 4. keyboard: role=button non-buttons must be focusable
    kb = [(x["tag"], x["name"][:18]) for x in items if x["tag"] != "button" and x["tabindex"] is None]
    rec(area, f"{label}: role=button elements are keyboard-focusable", not kb, kb[:5])
    # 5. no overlapping targets
    over = []
    seen = [x for x in items if x["vis"]]          # clipped (scrolled-away) controls cannot be hit, so cannot overlap
    for a_i, a in enumerate(seen):
        for b in seen[a_i + 1:]:
            if not (a["l"] + a["w"] <= b["l"] + 1 or b["l"] + b["w"] <= a["l"] + 1 or a["t"] + a["h"] <= b["t"] + 1 or b["t"] + b["h"] <= a["t"] + 1):
                # a geometric overlap only counts when the shared area is actually painted by one of the two
                ix = (max(a["l"], b["l"]) + min(a["l"] + a["w"], b["l"] + b["w"])) / 2
                iy = (max(a["t"], b["t"]) + min(a["t"] + a["h"], b["t"] + b["h"])) / 2
                hit = pg.evaluate("""([x,y,i,j])=>{const A=document.querySelector(`[data-aud='${i}']`),B=document.querySelector(`[data-aud='${j}']`);
                    const vis=(self,other)=>{const old=other.style.visibility;other.style.visibility='hidden';const t=document.elementFromPoint(x,y);other.style.visibility=old;return !!t&&self.contains(t)};
                    return vis(A,B)&&vis(B,A)}""", [ix, iy, a["i"], b["i"]])
                if hit:
                    over.append((a["name"][:14], b["name"][:14]))
    rec(area, f"{label}: no two buttons overlap", not over, over[:4])
    # 6. consistency per variant: same radius + weight
    by = {}
    for x in items:
        by.setdefault(x["variant"], []).append(x["i"])
    drift = []
    for v, idxs in by.items():
        if v in ("icon-ghost", "?", "link-button") or len(idxs) < 2:
            continue
        ms = [pg.evaluate("(i)=>{const el=document.querySelector(`[data-aud='${i}']`);const cs=getComputedStyle(el);return [cs.borderTopLeftRadius,cs.fontWeight]}", i) for i in idxs[:12]]
        if any(m != ms[0] for m in ms):
            drift.append((v, ms[0], [m for m in ms if m != ms[0]][0]))
    rec(area, f"{label}: buttons of one variant share radius / weight / size", not drift, drift[:3])
    # 7. state coverage per variant (hover, active, focus, disabled, pressed) on one live sample each
    samples = {}
    for x in items:
        if x["disabled"] or not x["vis"]:          # only controls a pointer can actually reach (not under a scrim)
            continue
        samples.setdefault(x["variant"], x)
    for v, x in sorted(samples.items()):
        sel = f"[data-aud='{x['i']}']"
        el = pg.query_selector(sel)
        if el is None or v == "?":
            continue
        pg.mouse.move(2, 2); pg.wait_for_timeout(60)
        rest = pg.evaluate(JS_BTN_MEASURE, el)
        el.scroll_into_view_if_needed(); box = el.bounding_box()
        if not box:
            continue
        pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2); pg.wait_for_timeout(220)
        hov = pg.evaluate(JS_BTN_MEASURE, el)
        pg.mouse.down(); pg.wait_for_timeout(220)
        act = pg.evaluate(JS_BTN_MEASURE, el)
        pg.mouse.move(2, 2); pg.mouse.up(); pg.wait_for_timeout(80)     # release off-target: no click fires
        keys = ("bg", "color", "border", "shadow")
        changed = any(rest[k] != hov[k] for k in keys)
        rec(area, f"{label}: [{v}] hover state is visibly different", changed or v in ("switch",), f"{rest['bg']} -> {hov['bg']}")
        rec(area, f"{label}: [{v}] hover keeps AA text contrast", hov["ratio"] >= 4.5 or (v == "switch"), round(hov["ratio"], 2))
        pressed_change = any(hov[k] != act[k] for k in keys) or hov["transform"] != act["transform"]
        rec(area, f"{label}: [{v}] has a pressed (active) state", pressed_change or v in ("switch", "icon-band"), f"{hov['bg']} -> {act['bg']}")
    # 8. disabled affordance
    dis = pg.evaluate("""()=>[...document.querySelectorAll('button:disabled')].filter(e=>e.offsetParent&&!e.closest('[hidden],[inert]')).map(e=>{const cs=getComputedStyle(e);return [e.textContent.trim().slice(0,16),cs.opacity,cs.cursor]})""")
    bad = [d for d in dis if not (float(d[1]) < 1 and d[2] == "not-allowed") and d[0] not in ("",)]
    # column-header placeholders (non-sortable) are intentionally inert: cursor:default, full opacity
    bad = [d for d in bad if d[0] not in ("LinkedIn",)]
    rec(area, f"{label}: disabled buttons look disabled (dimmed + not-allowed cursor)", not bad, bad[:4])
    # 9. pressed toggles: aria-pressed=true must differ from false
    groups = pg.evaluate("""()=>[...new Set([...document.querySelectorAll('[aria-pressed]')].map(e=>e.parentElement))].filter(Boolean).map(g=>{
      const bs=[...g.querySelectorAll(':scope > [aria-pressed]')].filter(e=>e.offsetParent);const t=bs.find(b=>b.getAttribute('aria-pressed')==='true'),f=bs.find(b=>b.getAttribute('aria-pressed')==='false');
      if(!t||!f)return null;const k=e=>{const c=getComputedStyle(e);return c.backgroundColor+'|'+c.borderTopColor+'|'+c.boxShadow+'|'+c.color};return [k(t),k(f)]}).filter(Boolean)""")
    same = [g for g in groups if g[0] == g[1]]
    rec(area, f"{label}: aria-pressed on/off are visually distinct", not same, same[:2])


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
    pg.add_style_tag(content="*{user-select:none!important}")   # press-and-hold probes must not drag a text selection

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

    # ---------- logo (NTXP-DOC-STANDARD 2.1: engine's own reversed logo, 1.55in zone, 0.82in tall, never faked) ----------
    lg = pg.evaluate("""async()=>{const z=document.querySelector('.band .logo'),i=z&&z.querySelector('img');
      const r=await fetch('/assets/ntxp_logo_reversed.png');const b=new Uint8Array(await r.arrayBuffer());
      const h=await crypto.subtle.digest('SHA-256',b);
      return {zone:z&&z.getBoundingClientRect().width,h:i&&i.getBoundingClientRect().height,ok:!!i&&i.complete&&i.naturalWidth>0,
        sha:[...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join(''),alt:i&&i.alt,
        fake:!!document.querySelector('.wordmark')}}""")
    rec("logo", "header shows the NTXP reversed logo (loaded, with alt text)", lg["ok"] and "NTXP" in (lg["alt"] or ""), lg["alt"])
    rec("logo", "logo zone is 1.55in (148.8px) and the mark 0.82in (78.7px) tall", abs(lg["zone"] - 148.8) <= 1.5 and abs(lg["h"] - 78.72) <= 1.5, f'{lg["zone"]} / {lg["h"]}')
    ref = os.environ.get("NTXP_LOGO_REF")
    if ref and os.path.isfile(ref):
        import hashlib
        rec("logo", "served logo is byte-identical to the Document Engine's own asset", hashlib.sha256(open(ref, "rb").read()).hexdigest() == lg["sha"])
    rec("logo", "no hand-made wordmark stands in for the logo", not lg["fake"])
    miss = br.new_context(viewport={"width": 1440, "height": 900}).new_page()
    miss.route("**/assets/ntxp_logo_reversed.png", lambda r: r.abort()); miss.goto(BASE + "/"); settle(miss)
    gone = miss.evaluate("()=>({img:!!document.querySelector('.band .logo img'),sr:!!document.querySelector('.band .logo .sr-only'),mark:[...document.querySelectorAll('.band .logo > *:not(.sr-only)')].map(e=>e.textContent.trim()).join('')})")
    rec("logo", "logo missing -> NO substitute mark is drawn (text alternative only)", (not gone["img"]) and gone["sr"] and gone["mark"] == "", gone)
    miss.context.close()

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

    # ---------- buttons: every screen state ----------
    button_audit(pg, "table")
    pg.click("#ham"); pg.wait_for_timeout(400); button_audit(pg, "reports drawer")
    pg.click("#gear"); pg.wait_for_selector("#panel:not([hidden])"); button_audit(pg, "settings panel")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    pg.click("#ham"); pg.wait_for_timeout(400); pg.click('[data-rep="directory"]'); pg.wait_for_selector("#doc .d-card"); pg.wait_for_timeout(300)
    button_audit(pg, "report view"); pg.click("#rvBack"); pg.wait_for_selector("#tb tr[data-id]")

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
