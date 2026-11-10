#!/usr/bin/env python3
"""Live Plans Atlas: serve the viewer and export or print sheets with their overlays.

    python atlas_live.py serve  --project <dir> [--port 8765]
    python atlas_live.py export --project <dir> --sheet A-101 [--layers markup,schedules] --out sheet.pdf
    python atlas_live.py selftest

`serve` runs a local-only web server (127.0.0.1) on the project's Plans Atlas
folder. The viewer's Export menu then offers "Sheet with markups (PDF)", which
this server answers:

    /export/sheet.pdf?sheet=<sheet id>&layers=markup,schedules,notes,rooms,doors
    /export/set.pdf          the drawing set with the Index Legend in front
    /export/legend.pdf       the Index Legend on its own

The exported sheet is the original page, untouched, with the overlays drawn on
top as vector graphics in the NTXP markup colours (hue is the trade; demolition
is dotted with a 25% fill, new work solid with a 40% fill; measurements are
red), a legend, and the red version footer. It is a working export. A markup
that leaves the building is still published by ntxp-pdf-markups-and-redlines.

Stdlib and PyMuPDF only. Nothing is sent anywhere.
"""
import argparse
import datetime as dt
import json
import sys
import tempfile
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import atlas_shell  # noqa: E402

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

OUT_SUBDIR = "Plans Atlas"
ALL_LAYERS = [k for k, _ in atlas_shell.LAYERS]


def log(msg):
    sys.stderr.write(f"[atlas-live] {msg}\n")


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def find_atlas_dir(project):
    project = Path(project)
    hits = sorted(project.glob(f"**/{OUT_SUBDIR}/plans-atlas.html"), key=lambda p: len(p.parts))
    return hits[0].parent if hits else None


def find_pdf(project, name):
    for p in sorted(Path(project).rglob(name), key=lambda p: len(p.parts)):
        if OUT_SUBDIR not in p.parts and p.is_file():
            return p
    return None


def load_overlays(model_dir):
    atlas = atlas_shell.load_json(model_dir / "sections" / "plans_atlas.json", {}) or {}
    scope = atlas_shell.load_json(model_dir / "sections" / "scope_index.json")
    sheets = atlas.get("sheets") or []
    marks, problems = atlas_shell.markup_overlays(model_dir, sheets)
    return sheets, atlas_shell.merge_overlays(marks, atlas_shell.index_overlays(scope)), problems


def cloud_points(x0, y0, x1, y1, step=26.0):
    """Revision cloud as a scalloped outline: outward arcs approximated with short curves."""
    import math
    pts = []
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for (ax, ay), (bx, by) in zip(corners, corners[1:]):
        length = math.hypot(bx - ax, by - ay)
        n = max(2, round(length / step))
        nx, ny = (by - ay) / length, -(bx - ax) / length          # outward normal for a clockwise rectangle
        for k in range(n):
            sx, sy = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
            ex, ey = ax + (bx - ax) * (k + 1) / n, ay + (by - ay) * (k + 1) / n
            r = length / n / 2
            pts.append(((sx, sy), (sx + nx * r * 1.3, sy + ny * r * 1.3), (ex + nx * r * 1.3, ey + ny * r * 1.3), (ex, ey)))
    return pts


def draw_overlays(page, items):
    """Draw overlay records on a page whose rotation has been removed."""
    W, H = page.rect.width, page.rect.height
    lw = max(1.6, W / 700.0)
    used = {}
    for o in items:
        col = rgb(atlas_shell.STYLE_COLORS.get(o["style"], "#30343B"))
        pts = [fitz.Point(x * W, y * H) for x, y in o["pts"]]
        used[(o["style"], o["demo"])] = col
        thin = o["shape"] == "cloud" or o.get("kind") == "dimension"
        width = lw * (0.5 if thin else 1.0)
        dashes = f"[{lw:.1f} {lw * 2.2:.1f}] 0" if o["demo"] else None
        shape = page.new_shape()
        if o["shape"] == "tag" or len(pts) == 1:
            r = lw * 5
            shape.draw_circle(pts[0], r)
            shape.finish(color=col, fill=(1, 1, 1), fill_opacity=0.75, width=lw)
            shape.commit()
            text = o.get("label") or ""
            tw = fitz.get_text_length(text, fontname="hebo", fontsize=lw * 4.6)
            page.insert_text((pts[0].x - tw / 2, pts[0].y + lw * 1.6), text, fontname="hebo", fontsize=lw * 4.6, color=col)
            continue
        if o["shape"] == "cloud":
            xs, ys = [p.x for p in pts], [p.y for p in pts]
            for a, c1, c2, b in cloud_points(min(xs), min(ys), max(xs), max(ys), step=max(26.0, W / 60)):
                shape.draw_bezier(fitz.Point(a), fitz.Point(c1), fitz.Point(c2), fitz.Point(b))
            shape.finish(color=col, width=width, closePath=False)
        elif o["shape"] in ("line", "arrow"):
            shape.draw_polyline(pts)
            shape.finish(color=col, width=width * 3, stroke_opacity=0.3, closePath=False, lineJoin=1)   # focus halo
            shape.draw_polyline(pts)
            shape.finish(color=col, width=width, dashes=dashes, closePath=False, lineJoin=1)
            if o["shape"] == "arrow" and len(pts) > 1:
                import math
                a, b = pts[-2], pts[-1]
                ang, L = math.atan2(b.y - a.y, b.x - a.x), lw * 6
                shape.draw_polyline([b, fitz.Point(b.x - L * math.cos(ang - 0.4), b.y - L * math.sin(ang - 0.4)),
                                     fitz.Point(b.x - L * math.cos(ang + 0.4), b.y - L * math.sin(ang + 0.4))])
                shape.finish(color=col, fill=col, width=0.1, closePath=True)
        else:
            shape.draw_polyline(pts + [pts[0]])
            fill = col if o["shape"] == "poly" else None
            shape.finish(color=col, fill=fill, fill_opacity=(0.25 if o["demo"] else 0.40) if fill else 1, width=width,
                         dashes=dashes, closePath=True, lineJoin=1)
        shape.commit()
        if o.get("label"):
            size = lw * 4.2
            tw = fitz.get_text_length(o["label"], fontname="hebo", fontsize=size)
            cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
            ty = min(p.y for p in pts) - lw * 2.5
            halo = page.new_shape()
            halo.draw_rect(fitz.Rect(cx - tw / 2 - lw * 2, ty - size, cx + tw / 2 + lw * 2, ty + lw * 1.5))
            halo.finish(color=None, fill=(1, 1, 1), fill_opacity=0.82, width=0)
            halo.commit()
            page.insert_text((cx - tw / 2, ty), o["label"], fontname="hebo", fontsize=size, color=col)

    if used:                                             # legend, top right, kept off the drawing's title block
        size = max(7.0, W / 220)
        rows = [(atlas_shell.STYLE_LABELS.get(st, st) + (" (Demo)" if demo else ""), col, demo)
                for (st, demo), col in sorted(used.items())]
        bw = max(fitz.get_text_length(t, fontname="helv", fontsize=size) for t, _, _ in rows) + size * 5
        bh = size * 1.6 * (len(rows) + 1) + size
        x0, y0 = W * 0.80 - bw, size * 2
        box = page.new_shape()
        box.draw_rect(fitz.Rect(x0, y0, x0 + bw, y0 + bh))
        box.finish(color=rgb("#CDC0B2"), fill=(1, 1, 1), fill_opacity=0.94, width=0.6)
        box.commit()
        title = "Markup Legend"
        page.insert_text((x0 + (bw - fitz.get_text_length(title, fontname="hebo", fontsize=size)) / 2, y0 + size * 1.5), title,
                         fontname="hebo", fontsize=size, color=rgb("#1B2A4E"))
        for i, (text, col, demo) in enumerate(rows):
            y = y0 + size * 1.6 * (i + 2)
            ln = page.new_shape()
            ln.draw_line((x0 + size, y - size * 0.3), (x0 + size * 3.2, y - size * 0.3))
            ln.finish(color=col, width=lw, dashes=f"[{lw:.1f} {lw * 2.2:.1f}] 0" if demo else None)
            ln.commit()
            page.insert_text((x0 + size * 3.8, y), text, fontname="helv", fontsize=size, color=rgb("#1F2A3D"))
    return len(items)


def export_sheet_pdf(project, sheet_key, layers=None, out=None, today=None):
    """One sheet with its overlays burned in. Returns (path, overlay count)."""
    if fitz is None:
        raise SystemExit("PyMuPDF is required: pip install pymupdf")
    project = Path(project)
    model_dir = project / "model"
    sheets, overlays, _ = load_overlays(model_dir)
    key = str(sheet_key).upper()
    sheet = next((s for s in sheets if str(s["sheet_id"]).upper() == key or str(s.get("sheet_no") or "").upper() == key), None)
    if sheet is None:
        raise SystemExit(f"sheet not in the atlas: {sheet_key}")
    src = find_pdf(project, sheet.get("source_doc") or "")
    if src is None:
        raise SystemExit(f"drawing file not found under the project: {sheet.get('source_doc')}")
    layers = [x for x in (layers or ["markup"]) if x in ALL_LAYERS]
    items = [o for o in overlays.get(sheet["sheet_id"], []) if o["layer"] in layers]
    doc = fitz.open()
    with fitz.open(str(src)) as source:
        pno = int(sheet.get("page") or 1) - 1
        doc.insert_pdf(source, from_page=pno, to_page=pno, links=False)
    page = doc[0]
    if page.rotation:
        page.remove_rotation()
    draw_overlays(page, items)
    W, H = page.rect.width, page.rect.height
    size = max(7.0, W / 200)
    stamp = f"{(today or dt.date.today()).isoformat()}  v01  Atlas view export, not a published markup"
    page.insert_text((size * 2, H - size * 2), stamp, fontname="hebo", fontsize=size, color=(1, 0, 0), fill_opacity=0.5)
    name = f"{sheet.get('sheet_no') or sheet['sheet_id']} - Atlas View.pdf"
    out = Path(out) if out else Path(tempfile.mkdtemp(prefix="atlas-export-")) / name
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata({"title": name, "subject": "NTXP Plans Atlas view export: " + ", ".join(layers)})
    doc.save(str(out), garbage=3, deflate=True)
    doc.close()
    return out, len(items)


def make_handler(project, atlas_dir):
    project = Path(project)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(atlas_dir), **kw)

        def log_message(self, fmt, *args):
            log(fmt % args)

        def send_file(self, path, name):
            data = Path(path).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Content-Disposition", f'inline; filename="{name}"')
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(url.query)
            try:
                if url.path == "/export/sheet.pdf":
                    layers = [x for x in (q.get("layers") or ["markup"])[0].split(",") if x]
                    path, _ = export_sheet_pdf(project, (q.get("sheet") or [""])[0], layers)
                    return self.send_file(path, path.name)
                if url.path in ("/export/set.pdf", "/export/legend.pdf"):
                    pick = (sorted(atlas_dir.glob("* - Plans Atlas.pdf")) if url.path.endswith("set.pdf")
                            else [atlas_dir / "Index Legend.pdf"])
                    if not pick or not pick[0].is_file():
                        return self.send_error(404, "Not built yet: run deploy_atlas.py")
                    return self.send_file(pick[0], pick[0].name)
                if url.path == "/api/ping":
                    body = json.dumps({"ok": True, "project": project.name}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    return self.wfile.write(body)
            except SystemExit as e:
                return self.send_error(404, str(e))
            if url.path in ("", "/"):
                self.path = "/plans-atlas.html"
            return super().do_GET()

    return Handler


def cmd_serve(args):
    atlas_dir = find_atlas_dir(args.project)
    if atlas_dir is None:
        sys.exit(f"no Plans Atlas under {args.project}: run deploy_atlas.py first")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.project, atlas_dir))
    print(json.dumps({"status": "serving", "url": f"http://127.0.0.1:{server.server_address[1]}/", "folder": str(atlas_dir)}),
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def cmd_export(args):
    layers = [x for x in (args.layers or "markup").split(",") if x]
    path, n = export_sheet_pdf(args.project, args.sheet, layers, args.out)
    print(json.dumps({"status": "exported", "out": str(path), "overlays": n, "layers": layers}))


def selftest():
    if fitz is None:
        raise SystemExit("PyMuPDF is required for the selftest")
    tmp = Path(tempfile.mkdtemp(prefix="atlas-live-"))
    docs = tmp / "Construction Documents"
    docs.mkdir()
    d = fitz.open()
    d.new_page(width=2592, height=1728).insert_text((300, 300), "FLOOR PLAN", fontsize=20)
    d.save(str(docs / "set.pdf"))
    model = tmp / "model"
    (model / "sections").mkdir(parents=True)
    (model / "atlas" / "markups").mkdir(parents=True)
    (model / "sections" / "plans_atlas.json").write_text(json.dumps({"sheets": [
        {"sheet_id": "A-101", "sheet_no": "A-101", "title": "FLOOR PLAN", "page": 1, "source_doc": "set.pdf",
         "width_in": 36, "height_in": 24}]}))
    (model / "atlas" / "markups" / "m.json").write_text(json.dumps({"schema_version": "3.0", "coordinate_mode": "pdf_points", "markups": [
        {"id": "R1", "kind": "cloud", "source": {"sheet": "A-101"}, "rect": [259.2, 172.8, 518.4, 345.6], "label": "Confirm"},
        {"id": "E1", "kind": "area", "style": "electrical", "source": {"sheet": "A-101"},
         "points": [[1000, 800], [1400, 800], [1400, 1100]], "label": "New Power"},
        {"id": "D1", "kind": "polyline", "style": "demo", "work_status": "demo", "source": {"sheet": "A-101"},
         "points": [[1600, 400], [2000, 400]]},
        {"id": "M1", "kind": "dimension", "style": "plumbing", "source": {"sheet": "A-101"}, "start": [200, 1500], "end": [600, 1500]},
        {"id": "X1", "kind": "signature", "source": {"sheet": "A-101"}, "rect": [0, 0, 10, 10]}]}))
    sheets, ov, problems = load_overlays(model)
    items = {o["id"]: o for o in ov["A-101"]}
    assert items["R1"]["style"] == "revision" and items["R1"]["pts"][0] == [0.1, 0.1], items["R1"]
    assert items["E1"]["style"] == "electrical" and not items["E1"]["demo"]
    assert items["D1"]["demo"] and items["D1"]["style"] == "demo"
    assert items["M1"]["style"] == "dimension", "measurements are red whatever the trade"
    assert "X1" not in items and any("signature" in p for p in problems), "kinds the viewer cannot draw are reported, not dropped silently"
    out, n = export_sheet_pdf(tmp, "a-101", ["markup"], tmp / "out.pdf", today=dt.date(2026, 11, 10))
    assert n == 4 and out.is_file()
    with fitz.open(str(out)) as doc:
        assert doc.page_count == 1 and abs(doc[0].rect.width - 2592) < 1, "the sheet keeps its size"
        text = doc[0].get_text()
        assert "FLOOR PLAN" in text and "Markup Legend" in text and "Electrical" in text and "Demolition (Demo)" in text, text
        assert len(doc[0].get_drawings()) >= 6
    print("atlas_live selftest passed:", tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="Serve the viewer locally with PDF export.")
    s.add_argument("--project", required=True)
    s.add_argument("--port", type=int, default=8765, help="0 picks a free port.")
    e = sub.add_parser("export", help="Write one sheet with its overlays as a PDF.")
    e.add_argument("--project", required=True)
    e.add_argument("--sheet", required=True, help="Sheet id or sheet number.")
    e.add_argument("--layers", help="Comma list: " + ",".join(ALL_LAYERS) + " (default markup).")
    e.add_argument("--out")
    sub.add_parser("selftest")
    a = ap.parse_args()
    {"serve": cmd_serve, "export": cmd_export}.get(a.cmd, lambda _a: selftest())(a)


if __name__ == "__main__":
    main()
