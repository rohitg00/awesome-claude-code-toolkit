#!/usr/bin/env python3
"""NTXP Document Engine shell for the Plans Atlas viewer.

build_atlas_html.py owns the drawing viewer (pan, zoom, callout hotspots, search,
deep links). This module wraps it in the NTXP Document Engine look and adds the
live layers, and is imported by it. It never changes how a drawing is shown:
the sheet image, the viewer canvas and the pop-up cards (search results, toast,
tooltip) keep their original styling.

  header band     navy band, NTXP logo, title lockup, Accent Red band (persistent)
  page strip      second line: every page number and title, swipeable
  left drawer     trades, spec numbers, areas, phases (hamburger, header left)
  right drawer    the selected item's bottom level: trade scope summary,
                  schedules, takeoffs, spec chapter, notes (hamburger, header right)
  live overlays   schedules, notes, rooms, door marks and markup manifests drawn
                  over the sheet in the NTXP markup trade colours, animated
  export, print   markup manifest (schema 3.0 JSON), sheet PNG, browser print

Stdlib only. No network.
"""
import base64
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

# NTXP construction markup standard (ntxp-pdf-markups-and-redlines, references/trade-color-standards.md).
# Hue carries trade only; demolition is dotted with a 25% fill, new work solid with a 40% fill; measurements are red.
STYLE_COLORS = {
    "revision": "#FF0000", "demo": "#FF0000", "callout": "#FF0000", "dimension": "#FF0000",
    "architectural": "#2563EB", "structural": "#7C3AED", "civil": "#8B5E3C", "concrete": "#64748B",
    "masonry": "#A16207", "roofing": "#7C2D12", "mechanical": "#008B5A", "plumbing": "#00A3A3",
    "fire_protection": "#E00000", "electrical": "#0057FF", "low_voltage": "#7A3EC8", "fire_alarm": "#FF4500",
    "finish": "#B4872A", "millwork": "#C46A00", "general": "#30343B",
}
STYLE_LABELS = {
    "revision": "Revision", "demo": "Demolition", "callout": "Callout", "dimension": "Measurement",
    "architectural": "Architectural", "structural": "Structural", "civil": "Civil", "concrete": "Concrete",
    "masonry": "Masonry", "roofing": "Roofing", "mechanical": "Mechanical", "plumbing": "Plumbing",
    "fire_protection": "Fire Protection", "electrical": "Electrical", "low_voltage": "Low Voltage",
    "fire_alarm": "Fire Alarm", "finish": "Finish", "millwork": "Millwork", "general": "General",
}
DIV_STYLE = {"02": "demo", "03": "concrete", "04": "masonry", "05": "structural", "06": "millwork", "07": "roofing",
             "08": "architectural", "09": "finish", "10": "architectural", "12": "millwork", "21": "fire_protection",
             "22": "plumbing", "23": "mechanical", "26": "electrical", "27": "low_voltage", "28": "fire_alarm",
             "31": "civil", "32": "civil", "33": "civil"}
DEMO_STATUS = {"demo", "demolition", "remove", "removal"}
# markup manifest kinds (schema 3.0) -> how the viewer draws them
KIND_SHAPE = {"cloud": "cloud", "revision_cloud": "cloud", "bounding_box": "rect", "evidence_box": "rect",
              "highlight_rect": "rect", "area": "poly", "area_shade": "poly", "scope_area": "poly",
              "highlight_polygon": "poly", "area_measure": "poly", "route": "line", "polyline": "line",
              "arrow": "arrow", "leader": "arrow", "dimension": "line", "count": "tag", "tag": "tag",
              "quantity_tag": "tag", "text_note": "note", "reference_note": "note", "text_box": "note", "callout": "note"}
MEASURE_KINDS = {"dimension", "area_measure"}
LAYERS = [("markup", "Markups"), ("schedules", "Schedules"), ("notes", "Notes"), ("rooms", "Rooms"), ("doors", "Door Marks")]


def esc(v):
    return html.escape(str(v if v is not None else ""), quote=True)


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def style_for_division(d):
    return DIV_STYLE.get(str(d), "general")


def logo_data_uri():
    p = HERE.parent / "resources" / "brand" / "ntxp_logo_reversed.png"
    try:
        return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    except OSError:
        return ""


# ------------------------------------------------------------------ overlays

def _norm_points(points, mode, w_pt, h_pt):
    out = []
    for x, y in points:
        if mode == "inches":
            x, y = x * 72.0, y * 72.0
        if mode != "normalized":
            x, y = (x / w_pt if w_pt else 0), (y / h_pt if h_pt else 0)
        out.append([round(max(0.0, min(1.0, x)), 4), round(max(0.0, min(1.0, y)), 4)])
    return out


def markup_overlays(model_dir, sheets):
    """Overlay records from markup manifests in model/atlas/markups/*.json (schema 3.0, or the 1.0 geometry body)."""
    by_no, by_page = {}, {}
    for s in sheets:
        by_no.setdefault(str(s.get("sheet_no") or "").upper(), s)
        by_page.setdefault((s.get("source_doc"), int(s.get("page") or 0)), s)
        by_page.setdefault((None, int(s.get("page") or 0)), s)
    out, problems = {}, []
    mdir = Path(model_dir) / "atlas" / "markups"
    for path in sorted(mdir.glob("*.json")) if mdir.is_dir() else []:
        man = load_json(path)
        if not isinstance(man, dict) or not isinstance(man.get("markups"), list):
            problems.append(f"{path.name}: not a markup manifest")
            continue
        root_mode = man.get("coordinate_mode") or "pdf_points"
        for i, m in enumerate(man["markups"]):
            if not isinstance(m, dict):
                continue
            src = m.get("source") or {}
            sheet = by_no.get(str(src.get("sheet") or m.get("sheet") or "").upper()) \
                or by_page.get((None, int(src.get("page") or m.get("page") or 0)))
            kind = m.get("kind") or m.get("type") or ""
            shape = KIND_SHAPE.get(kind)
            if sheet is None or shape is None:
                problems.append(f"{path.name} #{i + 1}: " + ("sheet not in this set" if sheet is None
                                                              else f"kind '{kind}' is not drawn by the viewer"))
                continue
            g = m.get("geometry") if isinstance(m.get("geometry"), dict) else m
            mode = m.get("coordinate_mode") or root_mode
            w_pt, h_pt = (sheet.get("width_in") or 0) * 72.0, (sheet.get("height_in") or 0) * 72.0
            pts = None
            if g.get("rect"):
                x0, y0, x1, y1 = g["rect"]
                pts = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
            elif g.get("points"):
                pts = g["points"]
            elif g.get("start") and g.get("end"):
                pts = [g["start"], g["end"]]
            elif g.get("point") or g.get("target"):
                pts = [g.get("point") or g.get("target")]
            if not pts:
                problems.append(f"{path.name} #{i + 1}: no geometry")
                continue
            style = m.get("style") or m.get("trade") or ("dimension" if kind in MEASURE_KINDS else
                                                         "revision" if shape == "cloud" else "callout" if shape == "note" else "general")
            if kind in MEASURE_KINDS and not m.get("measurement_color_override"):
                style = "dimension"                       # all measurements render red (LOCK-17)
            if style not in STYLE_COLORS:
                style = "general"
            status = str(m.get("work_status") or ("demo" if style == "demo" else "new")).lower()
            out.setdefault(sheet["sheet_id"], []).append({
                "layer": "markup", "shape": shape, "style": style, "demo": status in DEMO_STATUS,
                "pts": _norm_points(pts, mode, w_pt, h_pt),
                "label": str(m.get("label") or m.get("text") or m.get("subject") or "")[:60],
                "id": str(m.get("id") or f"{path.stem}-{i + 1}"), "kind": kind, "source": path.name})
    return out, problems


def index_overlays(scope):
    """Overlay records for what the scope index found on each sheet. Off by default in the viewer."""
    out = {}
    if not scope:
        return out

    def add(sid, layer, style, box, label, rid):
        x0, y0, x1, y1 = box
        out.setdefault(sid, []).append({"layer": layer, "shape": "rect", "style": style, "demo": False,
                                        "pts": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], "label": label, "id": rid,
                                        "kind": "evidence_box", "source": "scope_index"})
    for s in scope.get("schedules") or []:
        add(s["sheet_id"], "schedules", style_for_division(s.get("division")), s["box"], s["title"].title()[:40], s["id"])
    for b in (scope.get("project_index") or {}).get("notes") or []:
        add(b["sheet_id"], "notes", "general", b["box"], b["heading"].title()[:40], f"{b['sheet_id']}-N")
    for r in (scope.get("project_index") or {}).get("rooms") or []:
        add(r["sheet_id"], "rooms", "architectural", r["box"], r["number"], f"room-{r['number']}")
    for m in ((scope.get("scope") or {}).get("08") or {}).get("door_marks") or []:
        for ref in m.get("plan_refs") or []:
            b = ref["box"]
            pad = 0.004
            add(ref["sheet_id"], "doors", "architectural", [b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad], m["mark"],
                f"door-{m['mark']}")
    return out


# ------------------------------------------------------------------ chrome

def header_html(company, project_title, project_sub):
    logo = logo_data_uri()
    mark = (f'<img class="de-logo" src="{logo}" alt="{esc(company)}">' if logo
            else f'<span class="de-logo de-logo-text">{esc(company)}</span>')
    return f'''<header class="de-head" id="de-head">
      <button type="button" class="ham" id="ham-left" aria-label="Navigation: trades, specs, areas" aria-expanded="false"
        aria-controls="de-left"><span></span><span></span><span></span></button>
      {mark}
      <div class="de-lockup"><div class="l1">PLANS ATLAS</div><div class="l2">{esc(project_title)}{project_sub}</div></div>
      <div class="atl-search de-search">
        <input id="atl-search" type="text" placeholder="Search sheets, trades, specs, drawing text" autocomplete="off"
          aria-label="Search">
        <div class="sr-panel" id="atl-search-results"></div>
      </div>
      <div class="de-tools">
        <button type="button" class="de-tool" id="de-index" title="Project index">Index</button>
        <button type="button" class="de-tool" id="de-print" title="Print this view">Print</button>
        <div class="de-menu">
          <button type="button" class="de-tool" id="de-export" aria-haspopup="true" aria-expanded="false">Export</button>
          <div class="de-menu-list" id="de-export-list" hidden>
            <button type="button" data-export="print">Print this view</button>
            <button type="button" data-export="index">Project index</button>
            <button type="button" data-export="png">Sheet image with overlays (PNG)</button>
            <button type="button" data-export="json">Markups on this sheet (JSON, schema 3.0)</button>
            <button type="button" data-export="pdf">Sheet with markups (PDF)</button>
            <a href="./dashboard.html">Command Dashboard</a>
          </div>
        </div>
      </div>
      <button type="button" class="ham" id="ham-right" aria-label="Details for the selected item" aria-expanded="false"
        aria-controls="de-right"><span></span><span></span><span></span></button>
    </header>
    <div class="de-accent"></div>'''


def strip_html(sheets):
    chips = "".join(
        f'<button type="button" class="pg" data-pg-sheet="{esc(s["sheet_id"])}" title="{esc(s.get("title", ""))}">'
        f'<span class="n">{i}</span><b>{esc(s.get("sheet_no") or s["sheet_id"])}</b>'
        f'<span class="t">{esc(s.get("title", ""))}</span></button>'
        for i, s in sorted(((int(x.get("page") or 0), x) for x in sheets), key=lambda t: (str(t[1].get("source_doc")), t[0])))
    return f'''<nav class="de-strip" aria-label="Pages">
      <button type="button" class="pg-nav" data-pg-nav="-1" aria-label="Scroll pages left">&#8249;</button>
      <div class="pg-track" id="pg-track">{chips}</div>
      <button type="button" class="pg-nav" data-pg-nav="1" aria-label="Scroll pages right">&#8250;</button>
    </nav>'''


def _table(columns, rows, max_rows=40):
    if not columns:
        return ""
    head = "".join(f"<th>{esc(c)}</th>" for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in (list(r) + [""] * len(columns))[:len(columns)]) + "</tr>"
                   for r in rows[:max_rows])
    more = (f'<p class="dd-more">{len(rows) - max_rows} more row(s) in the project knowledge base.</p>'
            if len(rows) > max_rows else "")
    return f'<div class="dd-tablewrap"><table class="dd-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>{more}'


def _jump(sheet_id, label, box=None, cls="chip sheetchip"):
    b = f' data-jump-box="{",".join(str(v) for v in box)}"' if box else ""
    return f'<button type="button" class="{cls}" data-jump-sheet="{esc(sheet_id)}"{b}>{esc(label)}</button>'


def _kv(pairs):
    rows = "".join(f'<div class="dd-kv"><span class="k">{esc(k)}</span><span class="v">{esc(v)}</span></div>'
                   for k, v in pairs if v not in (None, "", []))
    return f'<div class="dd-kvs">{rows}</div>' if rows else ""


def _section(title, body, count=None, open_=False):
    if not body:
        return ""
    c = f'<span class="c">{count}</span>' if count is not None else ""
    return (f'<details class="dd-sec"{" open" if open_ else ""}><summary><span>{esc(title)}</span>{c}</summary>'
            f'<div class="dd-body">{body}</div></details>')


def schedule_block(sch, img_src):
    img = (f'<img class="dd-crop" src="{esc(img_src(sch["crop"]))}" alt="{esc(sch["title"])} as drawn" loading="lazy">'
           if sch.get("crop") else "")
    warn = ('<p class="dd-warn">Rebuilt from text columns, not ruled lines. Check it against the image.</p>'
            if sch.get("confidence", 1) < 0.6 else "")
    specs = "".join(f'<button type="button" class="chip" data-detail-kind="spec" data-detail-key="{esc(x)}">{esc(x)}</button>'
                    for x in (sch.get("spec_sections") or [])[:6])
    return _section(f'{sch["title"]}', f'<div class="chiprow">{_jump(sch["sheet_id"], "Open on " + sch["sheet_no"], sch["box"])}'
                    f'{specs}</div>{img}{warn}{_table(sch["columns"], sch["rows"])}', sch.get("row_count"))


def detail_panels_html(atlas, scope, img_src):
    """Right drawer: the bottom level of whatever is selected on the left."""
    concepts = atlas.get("concepts") or {}
    sheets = {s["sheet_id"]: s for s in atlas.get("sheets") or []}
    no = lambda sid: (sheets.get(sid) or {}).get("sheet_no") or sid     # noqa: E731
    sc = (scope or {}).get("scope") or {}
    schedules = {s["id"]: s for s in (scope or {}).get("schedules") or []}
    millwork = {m["id"]: m for m in (scope or {}).get("millwork") or []}
    clar = (scope or {}).get("clarifications") or {}
    clar_labels = (scope or {}).get("clarification_labels") or {}
    pi = (scope or {}).get("project_index") or {}
    out = []

    def panel(kind, key, title, sub, body):
        out.append(f'<section class="dd-panel" data-kind="{esc(kind)}" data-key="{esc(key)}" hidden>'
                   f'<div class="dd-head"><div class="t">{esc(title)}</div><div class="s">{esc(sub)}</div></div>{body}</section>')

    # project index
    addr = pi.get("address") or {}
    party = lambda p: (p or {}).get("name") if isinstance(p, dict) else p      # noqa: E731
    body = _kv([("Project Title", pi.get("title")), ("Project Number", pi.get("number")),
                ("Address", ", ".join(x for x in (addr.get("street"), addr.get("city_state_zip")) if x)),
                ("Owner", party(pi.get("owner"))), ("Architect", party(pi.get("architect"))),
                ("MEP Engineer", party(pi.get("mep_engineer"))),
                *[(e.get("role", "").title(), e.get("name")) for e in pi.get("engineers_other") or []]])
    if not scope:
        body += '<p class="dd-warn">The scope index has not been built for this set yet. Run scope_index.py, then rebuild.</p>'
    for key in ("scheduling", "exclusions", "owner_vendors", "owner_allowance", "pricing_alternates", "phasing"):
        rows = clar.get(key) or []
        items = "".join(f'<li>{_jump(c["sheet_id"], c["sheet_no"], c.get("box"), "dd-ref")} {esc(c["text"][:300])}'
                        + (f' <em>Div {esc(", ".join(c["divisions"]))}</em>' if c.get("divisions") else "") + "</li>"
                        for c in rows[:80])
        body += _section(clar_labels.get(key, key), f'<ul class="dd-list">{items}</ul>' if items else "", len(rows))
    rooms = pi.get("rooms") or []
    if rooms:
        body += _section("Rooms", _table(["Room", "Name", "SF", "Perimeter LF", "Sheet"], [
            [r["number"], r["name"], f'{r["sf"]:,.0f}' if r.get("sf") is not None else "not printed",
             "not printed", r["sheet_no"]] for r in rooms], 200), len(rooms))
    notes = pi.get("notes") or []
    if notes:
        items = "".join(f'<li>{_jump(b["sheet_id"], b["sheet_no"], b.get("box"), "dd-ref")} {esc(b["heading"])} '
                        f'<em>{len(b["items"])} notes</em></li>' for b in notes)
        body += _section("General and Sheet Notes", f'<ul class="dd-list">{items}</ul>', len(notes))
    review = (scope or {}).get("needs_review") or []
    if review:
        body += _section("Check Before Relying on This Index",
                         '<ul class="dd-list">' + "".join(f"<li>{esc(r)}</li>" for r in review) + "</ul>", len(review))
    panel("project", "index", "Project Index", f'{len(sheets)} sheets', body)

    # trades
    for t in concepts.get("trades") or []:
        d = str(t.get("division"))
        v = sc.get(d) or {}
        label = t.get("label") or v.get("label") or f"Division {d}"
        sids = [s for s in t.get("sheet_ids") or [] if s in sheets]
        body = _section("Trade Scope Summary", _kv([
            ("Sheets", len(sids)), ("Spec sections", ", ".join((t.get("spec_sections") or [])[:10])),
            ("Schedules found", len(v.get("schedules") or [])), ("Notes blocks", len(v.get("notes") or [])),
            ("Takeoff", v.get("takeoff_status") or "no takeoff yet"),
            ("Markup colour", STYLE_LABELS[style_for_division(d)])]) +
            f'<div class="chiprow">{"".join(_jump(s, no(s)) for s in sids)}</div>', open_=True)
        tk = v.get("takeoff") or []
        body += _section("Takeoffs", _table(["ID", "Description", "Qty", "Unit"], [
            [q.get("takeoff_id", ""), q.get("description", ""), q.get("quantity", ""), q.get("uom", "")] for q in tk], 80)
            if tk else '<p class="dd-note">No takeoff yet. Quantities are not measured by the atlas.</p>', len(tk))
        for sid_ in v.get("schedules") or []:
            if sid_ in schedules:
                body += schedule_block(schedules[sid_], img_src)
        tags = v.get("size_tags") or []
        if tags:
            body += _section("Sizes Tagged on the Sheets", '<p class="dd-note">A count of printed tags, not a measured length.</p>'
                             + _table(["Type", "Size", "Tags", "Measured", "Sheets"], [
                                 [x["label"], x["size"], x["tag_count"], "not measured",
                                  ", ".join(y["sheet_no"] for y in x["sheets"][:6])] for x in tags], 60), len(tags))
        marks = v.get("door_marks") or []
        if marks:
            rows = "".join(f'<li><b>{esc(m["mark"])}</b> ' + ("".join(_jump(r["sheet_id"], r.get("sheet_no") or r["sheet_id"],
                           r["box"], "dd-ref") for r in m["plan_refs"]) or "<em>not found on a plan</em>") + "</li>"
                           for m in marks[:200])
            body += _section("Door Labels on Plan", f'<ul class="dd-list">{rows}</ul>', len(marks))
        elevs = v.get("door_elevations") or []
        if elevs:
            body += _section("Door Elevations", '<ul class="dd-list">' + "".join(
                f'<li>{_jump(e["sheet_id"], e["sheet_no"], e.get("box"), "dd-ref")} {esc(e.get("label") or "")} {esc(e["title"])}</li>'
                for e in elevs) + "</ul>", len(elevs))
        for mid in v.get("millwork_elevations") or []:
            m = millwork.get(mid)
            if not m:
                continue
            img = f'<img class="dd-crop" src="{esc(img_src(m["crop"]))}" alt="" loading="lazy">' if m.get("crop") else ""
            body += _section(f'{m.get("label") or ""} {m["title"]}'.strip(),
                             f'<div class="chiprow">{_jump(m["sheet_id"], "Open on " + m["sheet_no"], m["box"])}</div>{img}'
                             + _kv([("Room", m.get("room_number") or "not printed"),
                                    ("Cabinet codes", ", ".join(m["cabinet_codes"]) or "none printed"),
                                    ("Finish codes", ", ".join(m["finish_codes"]) or "none printed"),
                                    ("Dimensions", ", ".join(m["dimensions_printed"]) or "none printed"),
                                    ("Countertop", "yes" if m["countertop_noted"] else "not noted"),
                                    ("Sink", "yes" if m["sink_noted"] else "not noted"),
                                    ("Backsplash", "yes" if m["backsplash_noted"] else "not noted"),
                                    ("Cabinet count and lengths", "not measured")]))
        nb = v.get("notes") or []
        if nb:
            body += _section("Notes on This Trade's Sheets", '<ul class="dd-list">' + "".join(
                f'<li>{_jump(n["sheet_id"], n["sheet_no"], None, "dd-ref")} {esc(n["heading"])} <em>{n["items"]} notes</em></li>'
                for n in nb) + "</ul>", len(nb))
        rel = [(clar_labels.get(k, k), c) for k, rows in clar.items() for c in rows if d in (c.get("divisions") or [])]
        if rel:
            body += _section("Clarifications Touching This Trade", '<ul class="dd-list">' + "".join(
                f'<li><em>{esc(lab)}</em> {_jump(c["sheet_id"], c["sheet_no"], c.get("box"), "dd-ref")} {esc(c["text"][:260])}</li>'
                for lab, c in rel[:60]) + "</ul>", len(rel))
        panel("trade", d, f"Division {d}  {label}", f"{len(sids)} sheets", body)

    # specs
    finishes = [(s, f) for s in schedules.values() for f in s.get("finishes") or []]
    for sp in concepts.get("specs") or []:
        sec = sp.get("section") or ""
        sids = [s for s in sp.get("sheet_ids") or [] if s in sheets]
        pdf = sp.get("pdf")
        body = _section("Spec Chapter", _kv([("Section", sec), ("Title", sp.get("title")), ("Division", sp.get("division")),
                                             ("Chapter file", "linked" if pdf else "not linked yet")])
                        + (f'<div class="chiprow"><a class="chip pdfchip" href="{esc(pdf)}" target="_blank" rel="noopener">'
                           f'Open spec chapter</a></div>' if pdf else "")
                        + f'<div class="chiprow">{"".join(_jump(s, no(s)) for s in sids)}</div>', open_=True)
        cited = [(s, f) for s, f in finishes if f.get("spec_section") == sec]
        if cited:
            body += _section("Finishes Citing This Section", _table(["Code", "Fields", "Schedule"], [
                [f["code"], "; ".join(f"{k}: {v}" for k, v in f["fields"].items() if v), s["sheet_no"]] for s, f in cited]),
                len(cited))
        on = [s for s in schedules.values() if sec in (s.get("spec_sections") or [])]
        if on:
            body += _section("Schedules on Sheets Citing This Section", '<ul class="dd-list">' + "".join(
                f'<li>{_jump(s["sheet_id"], s["sheet_no"], s["box"], "dd-ref")} {esc(s["title"])}</li>' for s in on) + "</ul>",
                len(on))
        panel("spec", sec, f"Section {sec}", sp.get("title") or "", body)

    # areas and phases
    for kind, key_name, items in (("area", "area", concepts.get("areas") or []), ("phase", "phase", concepts.get("phases") or [])):
        for it in items:
            nm = it.get(key_name, "")
            sids = [s for s in it.get("sheet_ids") or [] if s in sheets]
            body = _section("Sheets", f'<div class="chiprow">{"".join(_jump(s, no(s)) for s in sids)}</div>', len(sids), True)
            if it.get("summary"):
                body += _section("Summary", f'<p class="dd-note">{esc(it["summary"])}</p>', open_=True)
            if it.get("divisions"):
                body += _section("Trades", '<div class="chiprow">' + "".join(
                    f'<button type="button" class="chip" data-detail-kind="trade" data-detail-key="{esc(d)}">Div {esc(d)}</button>'
                    for d in it["divisions"]) + "</div>", len(it["divisions"]), True)
            panel(kind, nm, f"{kind.title()} {nm}", f"{len(sids)} sheets", body)
    return "".join(out)


def layer_bar_html():
    chips = "".join(f'<button type="button" class="lyr" data-layer="{k}" aria-pressed="{"true" if k == "markup" else "false"}">'
                    f'{esc(v)}</button>' for k, v in LAYERS)
    return f'<div class="de-layers" id="de-layers" aria-label="Overlay layers"><span class="lbl">Overlays</span>{chips}</div>'


def payload(overlays, problems):
    return json.dumps({"overlays": overlays, "colors": STYLE_COLORS, "labels": STYLE_LABELS, "problems": problems})


def merge_overlays(*groups):
    out = {}
    for g in groups:
        for sid, items in g.items():
            out.setdefault(sid, []).extend(items)
    return out


STYLE = r"""
/* ===== NTXP Document Engine shell (document standard 2.1). There is no gold. ===== */
.atl-root{
  --navy:#1B2A4E; --navy-deep:#16224A; --navy-mid:#46567D; --accent:#C8102E; --red:#D0353C; --red-ink:#B92A32;
  --link:#2F529B; --warm:#F6F3EF; --warm-line:#E2DAD0; --warm-edge:#CDC0B2; --paper:#FFFFFF;
  --bg:#FFFFFF; --ink:#1F2A3D; --muted:#46567D; --faint:#5A6880; --blue:#2F529B; --blue-deep:#1B2A4E;
  --gold:#CDC0B2; --gold-soft:#1B2A4E; --line-w:#E2DAD0; --line-g:#CDC0B2; --line2:#CDC0B2;
  --panel:#FFFFFF; --raise:0 1px 2px rgba(27,42,78,.10); --raise-hi:0 8px 22px -10px rgba(27,42,78,.45); --r:4px;
  --sans:"Open Sans","Segoe UI",-apple-system,Roboto,Helvetica,Arial,sans-serif; --serif:var(--sans);
  --head-h:64px; --strip-h:46px; --chrome-h:calc(var(--head-h) + 5px + var(--strip-h));
  background:#fff; color:var(--ink);
}
body.atl-root{margin:0}
/* Drawings and pop-up cards keep the viewer's original look: restore its tokens on them. */
.atl-root .viewer-canvas,.atl-root .toast,.atl-root #tip,.atl-root .sr-panel,.atl-root .sheet-card .thumb{
  --bg:#0b0f16; --ink:#e8edf4; --muted:#9aa7b8; --faint:#66707f; --blue:#4f96d8; --blue-deep:#2f6cae;
  --gold:#c3cddd; --gold-soft:#dde5f0; --line-w:rgba(255,255,255,.08); --line-g:rgba(195,205,221,.28);
  --line2:rgba(255,255,255,.15); --r:14px;
}
.atl-bg,.atl-stars{display:none}
.atl-shell{min-height:100vh}

/* ---- header band: logo zone, title lockup, Accent Red band ---- */
.de-head{position:sticky;top:0;z-index:60;height:var(--head-h);display:flex;align-items:center;gap:12px;
  padding:0 12px;background:var(--navy);color:#fff}
.de-logo{height:46px;width:auto;flex:0 0 auto;display:block}
.de-logo-text{font:700 24px/1 var(--sans);letter-spacing:.04em;height:auto}
.de-lockup{flex:1 1 auto;min-width:0;text-align:center;line-height:1.15;overflow:hidden}
.de-lockup .l1{font:700 21px/1.1 var(--sans);letter-spacing:.07em;text-transform:uppercase;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.de-lockup .l2{font:400 13px/1.25 var(--sans);opacity:.95;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.de-accent{position:sticky;top:var(--head-h);z-index:60;height:5px;
  background:linear-gradient(90deg,rgba(200,16,46,.10) 0%,#C8102E 100%),#182746}
.ham{flex:0 0 auto;width:42px;height:42px;border-radius:4px;cursor:pointer;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:5px;border:1px solid rgba(255,255,255,.28)!important;
  background:rgba(255,255,255,.06)!important;transition:background .2s}
.ham:hover{background:rgba(255,255,255,.16)!important}
.ham span{display:block;width:20px;height:2px;border-radius:2px;background:#fff;
  transition:transform .28s cubic-bezier(.2,.7,.2,1),opacity .2s,width .28s}
.ham[aria-expanded="true"] span:nth-child(1){transform:translateY(7px) rotate(45deg)}
.ham[aria-expanded="true"] span:nth-child(2){opacity:0;width:0}
.ham[aria-expanded="true"] span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}
.de-search{flex:0 1 300px;margin-left:0;min-width:120px;max-width:300px}
.de-search input{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.28);color:#fff;border-radius:4px;
  box-shadow:none;padding:9px 12px}
.de-search input::placeholder{color:rgba(255,255,255,.72)}
.de-search input:focus{border-color:#fff;box-shadow:0 0 0 2px rgba(255,255,255,.25)}
.de-tools{display:flex;gap:6px;flex:0 0 auto;align-items:center}
.de-tool{cursor:pointer;font:600 12px/1 var(--sans);color:#fff!important;padding:9px 11px;border-radius:4px;
  border:1px solid rgba(255,255,255,.28)!important;background:rgba(255,255,255,.06)!important;white-space:nowrap}
.de-tool:hover{background:rgba(255,255,255,.18)!important}
.de-menu{position:relative}
.de-menu-list{position:absolute;right:0;top:calc(100% + 8px);min-width:270px;background:#fff;border:1px solid var(--warm-edge);
  border-radius:4px;box-shadow:0 14px 34px -12px rgba(27,42,78,.5);padding:6px;z-index:70;display:flex;flex-direction:column}
.de-menu-list button,.de-menu-list a{display:block;width:100%;text-align:left;padding:9px 10px;border-radius:3px;
  font:500 12.5px/1.3 var(--sans);color:var(--ink)!important;cursor:pointer}
.de-menu-list button:hover,.de-menu-list a:hover{background:var(--warm)}

/* ---- second line: swipeable page strip ---- */
.de-strip{position:sticky;top:calc(var(--head-h) + 5px);z-index:55;height:var(--strip-h);display:flex;align-items:stretch;
  background:#fff;border-bottom:1px solid var(--warm-edge);box-shadow:0 2px 6px -4px rgba(27,42,78,.35)}
.pg-track{flex:1 1 auto;display:flex;gap:6px;align-items:center;overflow-x:auto;overflow-y:hidden;padding:0 8px;
  scroll-snap-type:x proximity;-webkit-overflow-scrolling:touch;scrollbar-width:none;cursor:grab;touch-action:pan-x;
  mask-image:linear-gradient(90deg,transparent 0,#000 18px,#000 calc(100% - 18px),transparent 100%)}
.pg-track::-webkit-scrollbar{display:none}
.pg-track.dragging{cursor:grabbing;scroll-snap-type:none}
.pg{flex:0 0 auto;scroll-snap-align:center;display:flex;align-items:baseline;gap:7px;max-width:260px;cursor:pointer;
  padding:7px 11px;border-radius:4px;border:1px solid var(--warm-line)!important;background:#fff!important;
  color:var(--ink)!important;transition:transform .22s cubic-bezier(.2,.7,.2,1),background .2s,border-color .2s,box-shadow .2s}
.pg .n{font:600 10px/1 var(--sans);color:var(--faint)}
.pg b{font:700 12.5px/1 var(--sans);color:var(--navy);white-space:nowrap}
.pg .t{font:400 11.5px/1.1 var(--sans);color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pg:hover{background:var(--warm)!important;transform:translateY(-1px)}
.pg.active{background:var(--navy)!important;border-color:var(--navy)!important;box-shadow:0 4px 10px -6px rgba(27,42,78,.8);
  animation:pgpop .32s cubic-bezier(.2,.7,.2,1)}
.pg.active b,.pg.active .t,.pg.active .n{color:#fff}
@keyframes pgpop{0%{transform:scale(.94)}60%{transform:scale(1.04)}100%{transform:scale(1)}}
.pg-nav{flex:0 0 34px;cursor:pointer;font:700 20px/1 var(--sans);color:var(--navy)!important;text-align:center!important;
  background:#fff!important;border-left:1px solid var(--warm-line)!important;border-right:1px solid var(--warm-line)!important}
.pg-nav:hover{background:var(--warm)!important}
@media (hover:none){.pg-nav{display:none}}

/* ---- body and drawers ---- */
.atl-wrap,.atl-wrap.with-right{display:block;max-width:none;padding:16px 16px 60px;transition:padding .28s cubic-bezier(.2,.7,.2,1)}
.rail-left,#de-right{position:fixed;top:var(--chrome-h);bottom:0;z-index:50;max-height:none;overflow-y:auto;
  background:#fff;border-radius:0;box-shadow:none;padding:12px;scrollbar-width:thin;
  transition:transform .28s cubic-bezier(.2,.7,.2,1),visibility .28s;visibility:hidden}
.rail-left{left:0;width:min(320px,86vw);transform:translateX(-103%);border:none;border-right:1px solid var(--warm-edge)}
#de-right{right:0;width:min(380px,92vw);transform:translateX(103%);border-left:1px solid var(--warm-edge);
  display:flex;flex-direction:column;gap:12px}
.left-open .rail-left,.right-open #de-right{transform:none;visibility:visible;box-shadow:0 0 28px -12px rgba(27,42,78,.6)}
@media (min-width:1100px){
  .left-open .atl-wrap{padding-left:336px}
  .right-open .atl-wrap{padding-right:396px}
  .left-open .rail-left,.right-open #de-right{box-shadow:none}
}
.de-scrim{position:fixed;inset:var(--chrome-h) 0 0 0;z-index:45;background:rgba(27,42,78,.38);opacity:0;pointer-events:none;
  transition:opacity .25s}
@media (max-width:1099px){.left-open .de-scrim,.right-open .de-scrim{opacity:1;pointer-events:auto}}
#rail-right{display:flex;position:static;max-height:none;overflow:visible}
.atl-center{min-height:60vh}

/* navy chrome on a light page: the viewer's white hover text becomes navy */
.atl-root .rail-tab{color:var(--navy-mid);background:#fff;border-radius:4px;font-family:var(--sans)}
.atl-root .rail-tab:hover,.atl-root .rail-row:hover,.atl-root .disc-tab:hover,.atl-root .btn:hover,
.atl-root .breadcrumb button:hover,.atl-root .v-zoom button:hover,.atl-root .linkrow:hover,.atl-root .pill:hover{
  color:var(--navy);box-shadow:none;background:var(--warm)}
.atl-root .rail-tab[aria-selected="true"],.atl-root .disc-tab.active,.atl-root .btn.primary{
  color:#fff;background:var(--navy);border-color:var(--navy);box-shadow:none}
.atl-root .rail-row.active{color:var(--navy);background:var(--warm);border-color:var(--warm-edge);font-weight:600}
.atl-root .rail-row.active .cnt{color:var(--navy)}
.atl-root .disc-tab .cnt{color:var(--faint)} .atl-root .disc-tab.active .cnt{color:#fff}
.atl-root .rail-row,.atl-root .disc-tab,.atl-root .btn,.atl-root .v-zoom button{border-radius:4px}
.atl-root .rail-row.is-current{box-shadow:inset 3px 0 0 var(--accent)}
.atl-root .spec-row,.atl-root .concept-row{cursor:pointer;border-radius:4px;padding:8px}
.atl-root .spec-row.is-current,.atl-root .concept-row.is-current{background:var(--warm);box-shadow:inset 3px 0 0 var(--accent)}
.atl-root .chip{background:#fff;color:var(--navy-mid);border-color:var(--warm-edge);border-radius:4px;box-shadow:none}
.atl-root button.chip:hover,.atl-root a.chip:hover{background:var(--warm);color:var(--navy)}
.atl-root .chip.pdfchip{color:var(--link);border-color:var(--link)}
.atl-root .sheet-card{background:#fff;border-color:var(--warm-edge);border-radius:4px}
.atl-root .sheet-card:hover{border-color:var(--navy)}
.atl-root .cardmeta .no{color:var(--navy);font-family:var(--sans)} .atl-root .cardmeta .ttl{color:var(--muted)}
.atl-root .rr-panel,.atl-root .stage-queue{background:#fff;border-color:var(--warm-edge);border-radius:4px;box-shadow:none}
.atl-root .rr-head .no{color:var(--navy);font-family:var(--sans)}
.atl-root .rr-block h4,.atl-root .stage-queue h4,.atl-root .div-detail h5,.atl-root .linkgroup h5{
  font-family:var(--sans);color:var(--navy);text-align:center}
.atl-root .breadcrumb{font-family:var(--sans)} .atl-root .breadcrumb button.cur{color:var(--navy);font-weight:700}

/* ---- right drawer: detail panels ---- */
.dd-empty{font:400 12.5px/1.5 var(--sans);color:var(--faint);text-align:center;padding:18px 8px}
.dd-panel{display:flex;flex-direction:column;gap:8px}
.dd-panel[hidden]{display:none}
.dd-head{background:var(--navy);color:#fff;text-align:center;padding:9px 10px;border-radius:4px}
.dd-head .t{font:700 12.5px/1.25 var(--sans);letter-spacing:.06em;text-transform:uppercase}
.dd-head .s{font:400 11.5px/1.3 var(--sans);opacity:.92}
.dd-sec{border:1px solid var(--warm-edge);border-radius:4px;background:#fff;box-shadow:0 1px 2px rgba(27,42,78,.08)}
.dd-sec>summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;position:relative;
  background:var(--navy-mid);color:#fff;font:700 11px/1.3 var(--sans);letter-spacing:.06em;text-transform:uppercase;
  padding:7px 30px;border-radius:3px;text-align:center}
.dd-sec>summary::-webkit-details-marker{display:none}
.dd-sec>summary::after{content:"+";position:absolute;right:10px;font:700 14px/1 var(--sans);transition:transform .2s}
.dd-sec[open]>summary::after{transform:rotate(45deg)}
.dd-sec[open]>summary{border-radius:3px 3px 0 0}
.dd-sec summary .c{position:absolute;left:10px;font:700 10.5px/1 var(--sans);background:rgba(255,255,255,.2);
  padding:3px 6px;border-radius:9px}
.dd-body{padding:9px;display:flex;flex-direction:column;gap:8px;animation:ddin .26s ease}
@keyframes ddin{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.dd-kvs{display:flex;flex-direction:column}
.dd-kv{display:flex;gap:10px;font:400 12px/1.4 var(--sans);padding:5px 8px}
.dd-kv:nth-child(even){background:var(--warm)}
.dd-kv .k{flex:0 0 42%;font-weight:700;color:var(--navy);text-align:center}
.dd-kv .v{flex:1;text-align:center;color:var(--ink);overflow-wrap:anywhere}
.dd-tablewrap{overflow-x:auto;border:1px solid var(--warm-edge);border-radius:4px}
.dd-table{border-collapse:collapse;width:100%;font:400 11px/1.35 var(--sans)}
.dd-table th{background:var(--navy-mid);color:#fff;font-weight:700;text-transform:uppercase;letter-spacing:.04em;
  font-size:10px;padding:5px 6px;text-align:center;border-right:1px solid #35446B;white-space:nowrap}
.dd-table td{padding:4px 6px;text-align:center;vertical-align:top;border-top:1px solid var(--warm-line);color:var(--ink)}
.dd-table tbody tr:nth-child(even) td{background:var(--warm)}
.dd-crop{display:block;max-width:100%;height:auto;border:1px solid var(--navy);outline:3px solid #fff;
  box-shadow:0 0 0 4px var(--warm-edge);margin:4px auto}
.dd-list{margin:0;padding:0;list-style:none;display:flex;flex-direction:column}
.dd-list li{font:400 12px/1.45 var(--sans);padding:6px 8px;color:var(--ink)}
.dd-list li:nth-child(even){background:var(--warm)}
.dd-list em{font-style:normal;color:var(--faint);font-size:11px}
.dd-ref{cursor:pointer;font:700 11px/1 var(--sans);color:var(--link)!important;padding:2px 5px;border-radius:3px;
  border:1px solid var(--warm-edge)!important;background:#fff!important;margin-right:4px}
.dd-ref:hover{background:var(--warm)!important}
.dd-note,.dd-more{font:400 11.5px/1.45 var(--sans);color:var(--faint);text-align:center;margin:0}
.dd-warn{font:600 11.5px/1.45 var(--sans);color:var(--red-ink);text-align:center;margin:0}

/* ---- live overlays on the sheet (NTXP markup colours) ---- */
.de-layers{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.de-layers .lbl{font:700 10.5px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--navy)}
.lyr{cursor:pointer;font:600 11.5px/1 var(--sans);padding:7px 10px;border-radius:4px;color:var(--navy-mid)!important;
  border:1px solid var(--warm-edge)!important;background:#fff!important;transition:.18s}
.lyr[aria-pressed="true"]{background:var(--navy)!important;border-color:var(--navy)!important;color:#fff!important}
.lyr .q{opacity:.75;margin-left:5px;font-weight:700}
.ov{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible}
.ov .s{fill:none;stroke-width:2.4;vector-effect:non-scaling-stroke;stroke-linejoin:round;stroke-linecap:round}
.ov .s.thin{stroke-width:1.2}
.ov .draw{stroke-dasharray:1;stroke-dashoffset:1;animation:ovdraw .9s cubic-bezier(.3,.7,.2,1) forwards}
.ov .demo{stroke-dasharray:2 5;animation:ovfade .7s ease forwards;opacity:0}
.ov .f{stroke:none;opacity:0;animation:ovfill .6s .35s ease forwards}
.ov .halo{fill:none;stroke-width:7.2;vector-effect:non-scaling-stroke;opacity:0;stroke-linejoin:round;
  animation:ovhalo .6s .2s ease forwards}
@keyframes ovdraw{to{stroke-dashoffset:0}}
@keyframes ovfade{to{opacity:1}}
@keyframes ovfill{to{opacity:var(--fo,.4)}}
@keyframes ovhalo{to{opacity:.3}}
.ov-lbl{position:absolute;transform:translate(-50%,-115%);pointer-events:none;white-space:nowrap;
  font:700 10px/1 Helvetica,Arial,sans-serif;padding:2px 5px;border-radius:3px;background:rgba(255,255,255,.82);
  opacity:0;animation:ovfade .4s .5s ease forwards}
.ov-tag{position:absolute;transform:translate(-50%,-50%);pointer-events:none;min-width:22px;height:22px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;font:700 11px/1 Helvetica,Arial,sans-serif;padding:0 5px;
  opacity:0;animation:ovfade .4s .3s ease forwards}
.ov-legend{position:absolute;right:10px;top:10px;z-index:3;max-width:210px;padding:7px 9px;border-radius:4px;
  background:rgba(255,255,255,.94);border:1px solid #CDC0B2;font:600 10px/1.5 Helvetica,Arial,sans-serif;color:#1F2A3D;
  pointer-events:none}
.ov-legend .h{font-weight:700;letter-spacing:.06em;text-transform:uppercase;text-align:center;color:#1B2A4E}
.ov-legend .r{display:flex;align-items:center;gap:6px}
.ov-legend i{display:inline-block;width:16px;height:0;border-top:2.4px solid currentColor}
.ov-legend i.d{border-top-style:dotted}

@media (max-width:760px){
  .atl-root{--head-h:56px}
  .de-logo{height:36px} .de-lockup .l1{font-size:15px} .de-lockup .l2{font-size:11px}
  .de-search{display:none} .de-tool{padding:8px 8px;font-size:11px} #de-index,#de-print{display:none}
  .de-head{gap:8px;padding:0 8px} .ham{width:38px;height:38px}
  .atl-wrap,.atl-wrap.with-right{padding:10px 10px 50px}
  .atl-root .viewer{height:calc(100vh - var(--chrome-h) - 120px)}
  .atl-root .stage{width:min(94vw,calc(60vh * var(--ar,1.5)))!important}
}
@media (prefers-reduced-motion:reduce){
  .ov .draw{stroke-dashoffset:0} .ov .demo,.ov .f,.ov .halo,.ov-lbl,.ov-tag{opacity:1}
  .ov .f{opacity:var(--fo,.4)} .ov .halo{opacity:.3}
}
@media print{
  @page{margin:.35in}
  .de-head,.de-accent,.de-strip,.rail-left,#de-right,.de-scrim,.viewer-toolbar,.de-layers,.toast,#tip,.disc-tabs{display:none!important}
  .atl-wrap{padding:0!important} .atl-root{background:#fff}
  .printing-sheet .sheet-grid{display:none!important}
  .printing-sheet .viewer{height:auto!important}
  .printing-sheet .viewer-canvas{border:none!important;background:#fff!important;overflow:visible!important;min-height:0;flex:none}
  .printing-sheet #viewer-panels{height:auto} .printing-sheet .viewer-panel.active{position:static;display:block}
  .printing-sheet .stage{transform:none!important;width:100%!important;box-shadow:none!important;
    -webkit-print-color-adjust:exact;print-color-adjust:exact}
  .printing-sheet .hotspots{display:none}
  .ov .draw{stroke-dashoffset:0!important;animation:none!important}
  .ov .demo,.ov .halo,.ov-lbl,.ov-tag{animation:none!important;opacity:1!important}
  .ov .f{animation:none!important;opacity:var(--fo,.4)!important} .ov .halo{opacity:.3!important}
  .sheet-card{break-inside:avoid}
}
"""

SCRIPT = r"""
(function(){
  var root=document.querySelector('.atl-root'); if(!root) return;
  var rm=window.matchMedia&&window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  var wide=function(){ return window.innerWidth>=1100; };
  var D={overlays:{},colors:{},labels:{},problems:[]};
  try{ D=JSON.parse(document.getElementById('atlas-live-data').textContent); }catch(e){}
  function $(s,el){ return (el||document).querySelector(s); }
  function $all(s,el){ return Array.prototype.slice.call((el||document).querySelectorAll(s)); }
  function toast(msg){ var t=document.getElementById('toast'); if(!t) return; t.textContent=msg; t.classList.add('show');
    clearTimeout(toast._t); toast._t=setTimeout(function(){ t.classList.remove('show'); },4200); }

  // ---------------------------------------------------------------- drawers
  var hamL=$('#ham-left'), hamR=$('#ham-right');
  function setDrawer(side,on){
    root.classList.toggle(side+'-open',on);
    var h=side==='left'?hamL:hamR; if(h) h.setAttribute('aria-expanded',on?'true':'false');
    if(on && !wide()){ var other=side==='left'?'right':'left'; root.classList.remove(other+'-open');
      var oh=other==='left'?hamL:hamR; if(oh) oh.setAttribute('aria-expanded','false'); }
  }
  if(hamL) hamL.addEventListener('click',function(){ setDrawer('left',!root.classList.contains('left-open')); });
  if(hamR) hamR.addEventListener('click',function(){ setDrawer('right',!root.classList.contains('right-open')); });
  var scrim=$('.de-scrim'); if(scrim) scrim.addEventListener('click',function(){ setDrawer('left',false); setDrawer('right',false); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape' && !wide()){ setDrawer('left',false); setDrawer('right',false); } });
  if(wide()) setDrawer('left',true);

  // ---------------------------------------------------------------- right drawer: bottom level of the left selection
  var emptyNote=$('#dd-empty');
  function showDetail(kind,key,open){
    var hit=null;
    $all('.dd-panel').forEach(function(p){
      var on=p.getAttribute('data-kind')===kind && p.getAttribute('data-key')===key; p.hidden=!on; if(on) hit=p; });
    if(emptyNote) emptyNote.hidden=!!hit;
    $all('.rail-row.is-current,.spec-row.is-current,.concept-row.is-current').forEach(function(x){ x.classList.remove('is-current'); });
    if(hit && open!==false) setDrawer('right',true);
    return hit;
  }
  $all('.rail-row[data-action="filter-div"]').forEach(function(r){
    r.addEventListener('click',function(){ var d=r.getAttribute('data-div');
      if(d==='all'){ showDetail('project','index'); } else if(showDetail('trade',d)){ r.classList.add('is-current'); } });
  });
  $all('.spec-row[data-spec]').forEach(function(r){
    r.addEventListener('click',function(e){ if(e.target.closest('a,button')) return;
      if(showDetail('spec',r.getAttribute('data-spec'))) r.classList.add('is-current'); });
  });
  $all('.rail-panel[data-tab="areas"] .concept-row').forEach(function(r){
    r.addEventListener('click',function(e){ if(e.target.closest('a,button')) return;
      if(showDetail('area',r.getAttribute('data-key'))) r.classList.add('is-current'); });
  });
  $all('.rail-panel[data-tab="phases"] .concept-row').forEach(function(r){
    r.addEventListener('click',function(e){ if(e.target.closest('a,button')) return;
      if(showDetail('phase',r.getAttribute('data-key'))) r.classList.add('is-current'); });
  });
  var idxBtn=$('#de-index'); if(idxBtn) idxBtn.addEventListener('click',function(){ showDetail('project','index'); });
  document.addEventListener('click',function(e){
    var d=e.target.closest('[data-detail-kind]');
    if(d){ showDetail(d.getAttribute('data-detail-kind'),d.getAttribute('data-detail-key')); return; }
    var j=e.target.closest('[data-jump-sheet]');
    if(j){ jump(j.getAttribute('data-jump-sheet'),j.getAttribute('data-jump-box')); if(!wide()) setDrawer('right',false); }
  });
  // The viewer opens a sheet from the URL hash; a fresh nonce makes the same sheet re-open and re-highlight.
  function jump(id,box){ location.hash='sheet='+encodeURIComponent(id)+(box?'&box='+box:'')+'&t='+Date.now(); }
  showDetail('project','index',false);

  // ---------------------------------------------------------------- page strip (second header line)
  var track=$('#pg-track');
  if(track){
    track.addEventListener('click',function(e){
      if(track._moved){ track._moved=false; return; }
      var b=e.target.closest('.pg'); if(b) jump(b.getAttribute('data-pg-sheet')); });
    var drag=null;
    track.addEventListener('pointerdown',function(e){ if(e.pointerType==='touch') return;   // touch scrolls natively
      drag={x:e.clientX,left:track.scrollLeft}; track._moved=false; });
    window.addEventListener('pointermove',function(e){ if(!drag) return; var dx=e.clientX-drag.x;
      if(Math.abs(dx)>4){ track._moved=true; track.classList.add('dragging'); } track.scrollLeft=drag.left-dx; });
    window.addEventListener('pointerup',function(){ if(drag){ drag=null; track.classList.remove('dragging'); } });
    track.addEventListener('wheel',function(e){ if(Math.abs(e.deltaY)>Math.abs(e.deltaX)){ track.scrollLeft+=e.deltaY; e.preventDefault(); } },{passive:false});
    $all('.pg-nav').forEach(function(b){ b.addEventListener('click',function(){
      track.scrollBy({left:parseInt(b.getAttribute('data-pg-nav'),10)*track.clientWidth*0.8,behavior:rm?'auto':'smooth'}); }); });
    document.addEventListener('keydown',function(e){
      if(e.target.closest('input,textarea')) return;
      if(e.key!=='ArrowLeft' && e.key!=='ArrowRight') return;
      var cur=$('.pg.active'), all=$all('.pg'); if(!all.length) return;
      var i=cur?all.indexOf(cur):-1, n=all[Math.max(0,Math.min(all.length-1,i+(e.key==='ArrowRight'?1:-1)))];
      if(n && n!==cur) jump(n.getAttribute('data-pg-sheet'));
    });
  }

  // ---------------------------------------------------------------- overlays
  var layers={markup:true,schedules:false,notes:false,rooms:false,doors:false};
  var NS='http://www.w3.org/2000/svg';
  function el(n,a){ var x=document.createElementNS(NS,n); for(var k in a) x.setAttribute(k,a[k]); return x; }
  function activeId(){ var v=$('#viewer'); if(!v||v.hidden) return null; var p=$('.viewer-panel.active'); return p?p.getAttribute('data-sheet'):null; }
  function visible(id){ return (D.overlays[id]||[]).filter(function(o){ return layers[o.layer]; }); }
  function pathOf(pts,close){ return pts.map(function(p,i){ return (i?'L':'M')+(p[0]*1000).toFixed(1)+' '+(p[1]*1000).toFixed(1); }).join(' ')+(close?' Z':''); }
  function cloudPath(pts){   // revision cloud: one-sided outward arcs along the rectangle
    var xs=pts.map(function(p){return p[0]*1000;}), ys=pts.map(function(p){return p[1]*1000;});
    var x0=Math.min.apply(0,xs),x1=Math.max.apply(0,xs),y0=Math.min.apply(0,ys),y1=Math.max.apply(0,ys);
    var c=[[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]], d='M'+x0+' '+y0;
    for(var i=0;i<4;i++){ var a=c[i],b=c[i+1],len=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.max(2,Math.round(len/26));
      for(var k=1;k<=n;k++){ var px=a[0]+(b[0]-a[0])*k/n, py=a[1]+(b[1]-a[1])*k/n, r=len/n/2;
        d+=' A'+r.toFixed(1)+' '+r.toFixed(1)+' 0 0 1 '+px.toFixed(1)+' '+py.toFixed(1); } }
    return d;
  }
  function render(){
    $all('.ov,.ov-lbl,.ov-tag,.ov-legend').forEach(function(x){ x.remove(); });
    var id=activeId(); if(!id) return;
    var stage=document.getElementById('stage-'+id); if(!stage) return;
    var items=visible(id); if(!items.length) return;
    var svg=el('svg',{'class':'ov',viewBox:'0 0 1000 1000',preserveAspectRatio:'none'}), used={};
    items.forEach(function(o,i){
      var col=D.colors[o.style]||'#30343B', delay=(rm?0:Math.min(i*0.06,1.2))+'s', closed=(o.shape==='rect'||o.shape==='poly'||o.shape==='cloud');
      used[o.style+(o.demo?'|d':'')]={col:col,label:(D.labels[o.style]||o.style)+(o.demo?' (demo)':''),demo:o.demo};
      if(o.shape==='tag' || (o.shape==='note' && o.pts.length===1)){
        var t=document.createElement('span'); t.className='ov-tag'; t.textContent=o.label||'•';
        t.style.left=(o.pts[0][0]*100)+'%'; t.style.top=(o.pts[0][1]*100)+'%'; t.style.color=col;
        t.style.border='2px solid '+col; t.style.background='rgba(255,255,255,.75)'; t.style.animationDelay=delay; stage.appendChild(t); return;
      }
      var d=o.shape==='cloud'?cloudPath(o.pts):pathOf(o.pts,closed);
      if(o.shape==='poly'){ var f=el('path',{d:d,'class':'f',fill:col}); f.style.setProperty('--fo',o.demo?'.25':'.40'); f.style.animationDelay=delay; svg.appendChild(f); }
      if(o.shape==='line'||o.shape==='arrow'){ var h=el('path',{d:d,'class':'halo',stroke:col}); h.style.animationDelay=delay; svg.appendChild(h); }
      var s=el('path',{d:d,'class':'s '+(o.demo?'demo':'draw')+(o.shape==='cloud'||o.kind==='dimension'?' thin':''),stroke:col,pathLength:'1'});
      if(o.demo) s.removeAttribute('pathLength');
      s.style.animationDelay=delay; svg.appendChild(s);
      if(o.shape==='arrow' && o.pts.length>1){ var a=o.pts[o.pts.length-2], b=o.pts[o.pts.length-1];
        var ang=Math.atan2((b[1]-a[1]),(b[0]-a[0])), L=14, bx=b[0]*1000, by=b[1]*1000;
        var hd=el('path',{d:'M'+bx+' '+by+' L'+(bx-L*Math.cos(ang-0.4)).toFixed(1)+' '+(by-L*Math.sin(ang-0.4)).toFixed(1)+' L'+(bx-L*Math.cos(ang+0.4)).toFixed(1)+' '+(by-L*Math.sin(ang+0.4)).toFixed(1)+' Z',fill:col,'class':'f'});
        hd.style.setProperty('--fo','1'); hd.style.animationDelay=delay; svg.appendChild(hd); }
      if(o.label){ var xs=o.pts.map(function(p){return p[0];}), ys=o.pts.map(function(p){return p[1];});
        var l=document.createElement('span'); l.className='ov-lbl'; l.textContent=o.label;
        l.style.left=((Math.min.apply(0,xs)+Math.max.apply(0,xs))*50)+'%'; l.style.top=(Math.min.apply(0,ys)*100)+'%';
        l.style.color=col; l.style.animationDelay=delay; stage.appendChild(l); }
    });
    stage.appendChild(svg);
    var lg=document.createElement('div'); lg.className='ov-legend';
    lg.innerHTML='<div class="h">Markup Legend</div>'+Object.keys(used).map(function(k){ var u=used[k];
      return '<div class="r" style="color:'+u.col+'"><i class="'+(u.demo?'d':'')+'"></i><span style="color:#1F2A3D">'+u.label+'</span></div>'; }).join('');
    var canvas=$('#viewer-canvas'); if(canvas) canvas.appendChild(lg);
  }
  function countLayers(){
    var id=activeId(), n={};
    (D.overlays[id]||[]).forEach(function(o){ n[o.layer]=(n[o.layer]||0)+1; });
    $all('.lyr').forEach(function(b){ var k=b.getAttribute('data-layer'), q=b.querySelector('.q');
      if(!q){ q=document.createElement('span'); q.className='q'; b.appendChild(q); } q.textContent=n[k]||0; });
  }
  $all('.lyr').forEach(function(b){ b.addEventListener('click',function(){ var k=b.getAttribute('data-layer');
    layers[k]=!layers[k]; b.setAttribute('aria-pressed',layers[k]?'true':'false'); render(); }); });

  // ---------------------------------------------------------------- follow the viewer
  var last=null;
  function sync(){
    var id=activeId();
    $all('.stage').forEach(function(s){ var ar=s.style.aspectRatio; if(ar) s.style.setProperty('--ar',ar); });
    if(id===last) return; last=id;
    $all('.pg').forEach(function(p){ var on=p.getAttribute('data-pg-sheet')===id; p.classList.toggle('active',on);
      if(on && track){ var x=p.offsetLeft-(track.clientWidth-p.offsetWidth)/2; track.scrollTo({left:x,behavior:rm?'auto':'smooth'}); } });
    var lb=$('#de-layers'); if(lb) lb.hidden=!id;
    countLayers(); render();
  }
  var vp=$('#viewer-panels'), vw=$('#viewer');
  if(window.MutationObserver){
    var mo=new MutationObserver(sync);
    if(vp) mo.observe(vp,{subtree:true,attributes:true,attributeFilter:['class']});
    if(vw) mo.observe(vw,{attributes:true,attributeFilter:['hidden']});
  }
  sync();
  if(D.problems && D.problems.length) console.warn('Plans Atlas markups skipped:',D.problems);

  // ---------------------------------------------------------------- export and print
  var exBtn=$('#de-export'), exList=$('#de-export-list');
  if(exBtn) exBtn.addEventListener('click',function(e){ e.stopPropagation(); exList.hidden=!exList.hidden;
    exBtn.setAttribute('aria-expanded',exList.hidden?'false':'true'); });
  document.addEventListener('click',function(e){ if(exList && !e.target.closest('.de-menu')) exList.hidden=true; });
  function save(blob,name){ var a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name;
    document.body.appendChild(a); a.click(); setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },800); }
  function sheetNo(id){ var p=$('.pg[data-pg-sheet="'+(window.CSS&&CSS.escape?CSS.escape(id):id)+'"] b'); return p?p.textContent:id; }
  function manifest(id){
    return {schema_version:'3.0',coordinate_mode:'normalized',project:document.title,
      routing:{route_status:'unresolved',document_type:'plan',purpose:'Viewer Export',visible_title:sheetNo(id),
        note:'Exported from the Plans Atlas viewer. Route it through ntxp-pdf-markups-and-redlines before publishing.'},
      output:{format:'PDF'},
      markups:visible(id).map(function(o){ var g={};
        if(o.shape==='rect'||o.shape==='cloud'){ var xs=o.pts.map(function(p){return p[0];}), ys=o.pts.map(function(p){return p[1];});
          g.rect=[Math.min.apply(0,xs),Math.min.apply(0,ys),Math.max.apply(0,xs),Math.max.apply(0,ys)]; }
        else if(o.pts.length===1){ g.point=o.pts[0]; } else { g.points=o.pts; }
        return {id:o.id,kind:o.kind,subject:o.label,style:o.style,work_status:o.demo?'demo':'new',label:o.label,
          source:{sheet:sheetNo(id),layer:o.layer,from:o.source},geometry:g}; })};
  }
  function exportPng(id){
    var stage=document.getElementById('stage-'+id), m=/url\(["']?(.*?)["']?\)/.exec(stage.style.backgroundImage||'');
    if(!m){ toast('This sheet has no image to export.'); return; }
    var img=new Image();
    img.onload=function(){
      var c=document.createElement('canvas'); c.width=img.naturalWidth; c.height=img.naturalHeight;
      var g=c.getContext('2d'); g.drawImage(img,0,0); var W=c.width,H=c.height, lw=Math.max(2,W/700);
      visible(id).forEach(function(o){ var col=D.colors[o.style]||'#30343B';
        g.strokeStyle=col; g.fillStyle=col; g.lineWidth=(o.shape==='cloud'||o.kind==='dimension')?lw*0.5:lw; g.lineJoin='round';
        g.setLineDash(o.demo?[lw,lw*2.2]:[]);
        if(o.pts.length===1){ var r=lw*5; g.globalAlpha=.75; g.fillStyle='#fff'; g.beginPath(); g.arc(o.pts[0][0]*W,o.pts[0][1]*H,r,0,7); g.fill();
          g.globalAlpha=1; g.stroke(); g.fillStyle=col; g.font='bold '+(lw*4.6)+'px Helvetica,Arial'; g.textAlign='center'; g.textBaseline='middle';
          g.fillText(o.label||'',o.pts[0][0]*W,o.pts[0][1]*H); return; }
        g.beginPath(); o.pts.forEach(function(p,i){ if(i) g.lineTo(p[0]*W,p[1]*H); else g.moveTo(p[0]*W,p[1]*H); });
        if(o.shape!=='line'&&o.shape!=='arrow') g.closePath();
        if(o.shape==='poly'){ g.globalAlpha=o.demo?.25:.40; g.fill(); g.globalAlpha=1; }
        g.stroke(); g.setLineDash([]);
        if(o.label){ var xs=o.pts.map(function(p){return p[0];}), ys=o.pts.map(function(p){return p[1];});
          var tx=(Math.min.apply(0,xs)+Math.max.apply(0,xs))/2*W, ty=Math.min.apply(0,ys)*H-lw*3;
          g.font='bold '+(lw*4.6)+'px Helvetica,Arial'; g.textAlign='center'; g.textBaseline='bottom';
          var tw=g.measureText(o.label).width; g.globalAlpha=.82; g.fillStyle='#fff'; g.fillRect(tx-tw/2-lw*2,ty-lw*6,tw+lw*4,lw*7);
          g.globalAlpha=1; g.fillStyle=col; g.fillText(o.label,tx,ty); }
      });
      try{ c.toBlob(function(b){ save(b,sheetNo(id)+' - Atlas View.png'); },'image/png'); }
      catch(err){ toast('The browser blocked the image export for this sheet.'); }
    };
    img.onerror=function(){ toast('The sheet image could not be read for export.'); };
    img.src=m[1];
  }
  if(exList) exList.addEventListener('click',function(e){
    var b=e.target.closest('[data-export]'); if(!b) return; exList.hidden=true;
    var kind=b.getAttribute('data-export');
    if(kind==='print'){ doPrint(); return; }
    if(kind==='index'){ showDetail('project','index'); return; }
    var id=activeId(); if(!id){ toast('Open a sheet first, then export.'); return; }
    if(kind==='json'){ save(new Blob([JSON.stringify(manifest(id),null,1)],{type:'application/json'}),sheetNo(id)+' - Markups.json'); }
    else if(kind==='png'){ exportPng(id); }
    else if(kind==='pdf'){
      if(location.protocol.indexOf('http')!==0){ toast('PDF export needs the live viewer: run atlas_live.py serve, then open the address it prints.'); return; }
      var on=Object.keys(layers).filter(function(k){ return layers[k]; }).join(',');
      window.open('export/sheet.pdf?sheet='+encodeURIComponent(id)+'&layers='+encodeURIComponent(on),'_blank');
    }
  });
  function doPrint(){ root.classList.toggle('printing-sheet',!!activeId()); window.print(); }
  var prBtn=$('#de-print');
  if(prBtn) prBtn.addEventListener('click',doPrint);
  window.addEventListener('afterprint',function(){ root.classList.remove('printing-sheet'); });
})();
"""
