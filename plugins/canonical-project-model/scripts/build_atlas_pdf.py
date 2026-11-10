#!/usr/bin/env python3
"""Embed the Plans Atlas navigation into the drawing-set PDF itself.

Reads sections/plans_atlas.json (and sections/scope_index.json when present)
and writes a new PDF in which:

  * an INDEX LEGEND (Letter portrait, NTXP Document Engine style) sits IN FRONT
    of the first drawing: project index, page index with detail labels,
    trades, spec sections, notes, clarifications and exclusions, rooms, and a
    scope index per trade with each schedule's image and recreated table;
  * every legend entry and every verified sheet callout is a live link;
  * every link targets a NAMED DESTINATION (`sheet:A-101`, `schedule:A-601-S1`,
    `index:doors` ...), written with explicit numeric coordinates. A named
    destination survives page insertion, reordering and re-issue, and can be
    opened from outside the file as `set.pdf#nameddest=sheet:A-101`;
  * the outline lists the legend sections and every sheet;
  * page labels show the sheet number, so the viewer's page box reads "A-101".

The drawing pages themselves are untouched: same content, same size, same
original links and annotations. The source PDF is never modified. Requires PyMuPDF.

    python build_atlas_pdf.py --pdf set.pdf --model <project>/model --out set-atlas.pdf
        [--legend-out index-legend.pdf] [--legend-md INDEX-LEGEND.md]
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:  # older PyMuPDF
    import fitz

# NTXP Document Engine palette (document standard 2.1). There is no gold.
def _rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


NAVY, NAVY_MID, ACCENT = _rgb("#1B2A4E"), _rgb("#46567D"), _rgb("#C8102E")
INK, INK_SOFT, LINK = _rgb("#1F2A3D"), _rgb("#5A6880"), _rgb("#2F529B")
WARM, WARM_LINE, WARM_EDGE, WHITE = _rgb("#F6F3EF"), _rgb("#E2DAD0"), _rgb("#CDC0B2"), (1, 1, 1)
SIGNAL = _rgb("#B92A32")
PW, PH, MARGIN = 612, 792, 40
BAND = 58                                   # header band height on a legend page
BODY_TOP, BODY_BOTTOM = BAND + 30, PH - 40

# NTXP construction markup trade colours (ntxp-pdf-markups-and-redlines, trade-color-standards.md)
TRADE_COLORS = [("Architectural", "#2563EB"), ("Structural", "#7C3AED"), ("Civil", "#8B5E3C"), ("Concrete", "#64748B"),
                ("Masonry", "#A16207"), ("Roofing", "#7C2D12"), ("Mechanical", "#008B5A"), ("Plumbing", "#00A3A3"),
                ("Fire Protection", "#E00000"), ("Electrical", "#0057FF"), ("Low Voltage", "#7A3EC8"),
                ("Fire Alarm", "#FF4500"), ("Finish", "#B4872A"), ("Millwork", "#C46A00"), ("General", "#30343B"),
                ("Revision / Demo", "#FF0000")]
SCOPE_TITLES = {"08": "Door Scope Index", "23": "HVAC Scope Index", "26": "Electrical Scope Index",
                "22": "Plumbing Scope Index", "06": "Millwork Scope Index"}
SCOPE_ORDER = ["08", "23", "26", "22", "06"]


def log(msg):
    sys.stderr.write(f"[atlas-pdf] {msg}\n")


def latin(text):
    """Base-14 fonts are Latin-1: keep what prints, replace the rest plainly."""
    text = str(text if text is not None else "")
    for a, b in (("–", "-"), ("—", "-"), ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                 ("•", "-"), ("Ø", "dia"), ("ø", "dia"), ("…", "...")):
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


def wrap(text, font, size, width):
    words, lines, cur = latin(text).split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if fitz.get_text_length(trial, fontname=font, fontsize=size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    out = []
    for ln in lines:                                    # a single token wider than the cell is cut, never overflowed
        while fitz.get_text_length(ln, fontname=font, fontsize=size) > width and len(ln) > 4:
            cut = max(4, int(len(ln) * width / fitz.get_text_length(ln, fontname=font, fontsize=size)) - 1)
            out.append(ln[:cut])
            ln = ln[cut:]
        out.append(ln)
    return out or [""]


def tbox(page, rect, text, fontname="helv", fontsize=8, color=INK, align=0):
    """One line of text set at the top of rect, aligned 0 left / 1 centre / 2 right.

    insert_textbox draws nothing at all when the box is a hair too short; this never drops text."""
    rect = fitz.Rect(rect)
    text = latin(text)
    w = fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
    while w > rect.width and len(text) > 4:              # too long for the measure: shorten, keep it on the sheet
        text = text[:-2]
        w = fitz.get_text_length(text + "...", fontname=fontname, fontsize=fontsize)
        if w <= rect.width:
            text += "..."
            break
    x = rect.x0 if align == 0 else rect.x0 + (rect.width - w) / 2 if align == 1 else rect.x1 - w
    page.insert_text((x, rect.y0 + fontsize * 0.92), text, fontname=fontname, fontsize=fontsize, color=color)


class Legend:
    """Letter-portrait flowing layout in NTXP Document Engine style. Links are named, resolved after merge."""

    def __init__(self, title, project, tag):
        self.doc = fitz.open()
        self.title, self.project, self.tag = latin(title), latin(project), latin(tag)
        self.links = []            # (legend page index, rect, destination name)
        self.anchors = {}          # destination name -> (legend page index, y)
        self.outline = []          # (level, title, legend page index)
        self.md = []
        self.page, self.y = None, 0
        self.new_page()

    # ---- page furniture
    def new_page(self):
        p = self.page = self.doc.new_page(width=PW, height=PH)
        p.draw_rect(fitz.Rect(0, 0, PW, BAND), color=None, fill=NAVY)
        tbox(p, fitz.Rect(0, 11, 86, 47), "NTXP", fontname="hebo", fontsize=22, color=WHITE, align=1)
        tbox(p, fitz.Rect(86, 10, PW - MARGIN, 34), self.title.upper(), fontname="hebo", fontsize=17,
                         color=WHITE, align=1)
        tbox(p, fitz.Rect(86, 33, PW - MARGIN, 51), self.project, fontname="helv", fontsize=9.5,
                         color=WHITE, align=1)
        steps = 40                                        # accent band: red fading in from the left over brand blue
        for i in range(steps):
            a = 0.10 + 0.90 * i / (steps - 1)
            base = _rgb("#182746")
            col = tuple(base[k] + (ACCENT[k] - base[k]) * a for k in range(3))
            p.draw_rect(fitz.Rect(PW * i / steps, BAND, PW * (i + 1) / steps + 0.5, BAND + 6), color=None, fill=col)
        tbox(p, fitz.Rect(MARGIN, BAND + 9, PW - MARGIN, BAND + 21), self.tag, fontname="helv", fontsize=7,
                         color=INK_SOFT, align=1)
        p.draw_line((MARGIN, BAND + 22), (PW - MARGIN, BAND + 22), color=WARM_LINE, width=0.5)
        p.insert_text((MARGIN, PH - 20), "Organizes only. The stamped drawings govern.", fontname="helv",
                      fontsize=6.5, color=INK_SOFT)
        self.y = BODY_TOP

    def finish(self):
        n = self.doc.page_count
        for i, p in enumerate(self.doc):
            txt = f"Page {i + 1} of {n}"
            w = fitz.get_text_length(txt, fontname="hebi", fontsize=8)
            p.insert_text((PW - MARGIN - w, PH - 20), txt, fontname="hebi", fontsize=8, color=NAVY)

    def ensure(self, h):
        if self.y + h > BODY_BOTTOM:
            self.new_page()

    @property
    def pno(self):
        return self.doc.page_count - 1

    # ---- blocks
    def section(self, text, anchor=None, count=None, level=1):
        self.ensure(46)
        self.y += 6
        if anchor:
            self.anchors[anchor] = (self.pno, self.y - 4)
        self.outline.append((level + 1, latin(text), self.pno))
        p = self.page
        p.draw_rect(fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + 17), color=None, fill=NAVY)
        tbox(p, fitz.Rect(MARGIN, self.y + 3.2, PW - MARGIN, self.y + 16), latin(text).upper(), fontname="hebo",
                         fontsize=9, color=WHITE, align=1)
        if count is not None:
            c = str(count)
            p.insert_text((PW - MARGIN - 8 - fitz.get_text_length(c, fontname="hebo", fontsize=8), self.y + 12),
                          c, fontname="hebo", fontsize=8, color=WHITE)
        self.y += 23
        self.md.append(f"\n{'#' * (level + 1)} {text}\n")

    def heading(self, text, sub=None, dest=None):
        self.ensure(22)
        p = self.page
        t = latin(text).upper()
        tbox(p, fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + 12), t, fontname="hebo", fontsize=8,
                         color=LINK if dest else NAVY, align=1)
        if dest:
            w = fitz.get_text_length(t, fontname="hebo", fontsize=8)
            self.links.append((self.pno, fitz.Rect(PW / 2 - w / 2 - 3, self.y, PW / 2 + w / 2 + 3, self.y + 11), dest))
        self.y += 11
        if sub:
            tbox(p, fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + 10), latin(sub), fontname="helv", fontsize=6.8,
                             color=INK_SOFT, align=1)
            self.y += 10
        p.draw_line((MARGIN + 150, self.y + 1), (PW - MARGIN - 150, self.y + 1), color=WARM_LINE, width=0.5)
        self.y += 6
        self.md.append(f"\n**{text}**" + (f" ({sub})" if sub else "") + "\n")

    def para(self, text, size=7.5, color=INK, bold=False):
        font = "hebo" if bold else "helv"
        for ln in wrap(text, font, size, PW - 2 * MARGIN - 8):
            self.ensure(size + 3)
            self.page.insert_text((MARGIN + 4, self.y + size), ln, fontname=font, fontsize=size, color=color)
            self.y += size + 2.6
        self.y += 2
        self.md.append(latin(text) + "\n")

    def kv(self, pairs):
        """Two-tone label / value block. Labels bold and centred, values centred."""
        rows = [(k, v) for k, v in pairs if v]
        self.md.append("")
        for i, (k, v) in enumerate(rows):
            lines = wrap(v, "helv", 8, PW - 2 * MARGIN - 170)
            h = max(14, len(lines) * 10 + 4)
            self.ensure(h)
            p = self.page
            if i % 2:
                p.draw_rect(fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + h), color=None, fill=WARM)
            tbox(p, fitz.Rect(MARGIN, self.y + 2.5, MARGIN + 150, self.y + h), latin(k).upper(), fontname="hebo",
                             fontsize=7.5, color=NAVY, align=1)
            for j, ln in enumerate(lines):
                tbox(p, fitz.Rect(MARGIN + 160, self.y + 2 + j * 10, PW - MARGIN, self.y + 14 + j * 10), ln,
                                 fontname="helv", fontsize=8, color=INK, align=1)
            self.y += h
            self.md.append(f"- **{k}:** {latin(v)}")
        self.page.draw_line((MARGIN, self.y), (PW - MARGIN, self.y), color=WARM_EDGE, width=0.7)
        self.y += 8

    def chips(self, items, dest_of, label_of=None):
        x, line_h = MARGIN + 6, 13
        names = []
        for it in items:
            dest = dest_of(it)
            text = latin(label_of(it) if label_of else it)
            w = fitz.get_text_length(text, fontname="hebo", fontsize=7) + 9
            if x + w > PW - MARGIN:
                x = MARGIN + 6
                self.y += line_h
            self.ensure(line_h + 2)
            r = fitz.Rect(x, self.y, x + w, self.y + 10.5)
            self.page.draw_rect(r, color=WARM_EDGE, fill=WHITE if dest else WARM, width=0.5, radius=0.25)
            self.page.insert_text((x + 4.5, self.y + 7.8), text, fontname="hebo", fontsize=7,
                                  color=LINK if dest else INK_SOFT)
            if dest:
                self.links.append((self.pno, r, dest))
            names.append(text)
            x += w + 4
        self.y += line_h + 4
        self.md.append(", ".join(names) + "\n")

    def bars(self, rows, unit="sheets"):
        top = max([c for _, c in rows] or [1]) or 1
        for lab, c in rows:
            self.ensure(13)
            p = self.page
            tbox(p, fitz.Rect(MARGIN, self.y, MARGIN + 196, self.y + 11), latin(lab)[:44], fontname="helv",
                             fontsize=7.2, color=INK, align=2)
            bw = max(2, 270 * c / top)
            p.draw_rect(fitz.Rect(MARGIN + 204, self.y + 1, MARGIN + 204 + 270, self.y + 9), color=None, fill=WARM)
            p.draw_rect(fitz.Rect(MARGIN + 204, self.y + 1, MARGIN + 204 + bw, self.y + 9), color=None, fill=NAVY)
            p.insert_text((MARGIN + 480, self.y + 8.2), f"{c} {unit}", fontname="hebo", fontsize=7, color=NAVY)
            self.y += 12.5
        self.y += 6

    def swatches(self, pairs):
        x = MARGIN + 6
        for name, hexv in pairs:
            w = fitz.get_text_length(name, fontname="helv", fontsize=6.8) + 20
            if x + w > PW - MARGIN:
                x = MARGIN + 6
                self.y += 12
            self.ensure(12)
            self.page.draw_rect(fitz.Rect(x, self.y + 1.5, x + 9, self.y + 8.5), color=None, fill=_rgb(hexv))
            self.page.insert_text((x + 12, self.y + 8), name, fontname="helv", fontsize=6.8, color=INK)
            x += w + 6
        self.y += 16

    def table(self, columns, rows, weights=None, link_col=None, dests=None, max_rows=None, size=6.8, money=()):
        """Two-tone table. Header centred; cells centred, a column holding a paragraph is left-aligned whole."""
        ncol = len(columns)
        if not ncol:
            return
        shown = rows if max_rows is None else rows[:max_rows]
        width = PW - 2 * MARGIN
        if not weights:
            weights = []
            for c in range(ncol):
                longest = max([len(latin(columns[c]))] + [len(latin(r[c] if c < len(r) else "")) for r in shown[:60]])
                weights.append(min(max(longest, 4), 46))
        total = float(sum(weights))
        widths = [width * w / total for w in weights]
        para_col = [any(fitz.get_text_length(latin(r[c] if c < len(r) else ""), fontname="helv", fontsize=size) > widths[c] - 6
                        for r in shown) for c in range(ncol)]

        def header():
            hl = [wrap(c, "hebo", size, widths[i] - 6) for i, c in enumerate(columns)]
            h = max(len(x) for x in hl) * (size + 2) + 5
            self.ensure(h + 14)
            p, x = self.page, MARGIN
            p.draw_rect(fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + h), color=None, fill=NAVY_MID)
            for i, lines in enumerate(hl):
                for j, ln in enumerate(lines):
                    tbox(p, fitz.Rect(x, self.y + 2 + j * (size + 2), x + widths[i], self.y + 14 + j * (size + 2)),
                                     ln.upper(), fontname="hebo", fontsize=size, color=WHITE, align=1)
                x += widths[i]
            self.y += h

        header()
        self.md.append("\n| " + " | ".join(latin(c) for c in columns) + " |\n|" + "---|" * ncol)
        for ri, r in enumerate(shown):
            cells = [wrap(r[c] if c < len(r) else "", "helv", size, widths[c] - 6) for c in range(ncol)]
            h = max(len(x) for x in cells) * (size + 2) + 4
            if self.y + h > BODY_BOTTOM:
                self.new_page()
                header()
            p, x = self.page, MARGIN
            if ri % 2:
                p.draw_rect(fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + h), color=None, fill=WARM)
            for c, lines in enumerate(cells):
                is_link = link_col == c and dests and ri < len(dests) and dests[ri]
                align = 2 if c in money else 0 if para_col[c] else 1
                for j, ln in enumerate(lines):
                    tbox(p, fitz.Rect(x + 3, self.y + 1.5 + j * (size + 2), x + widths[c] - 3,
                                               self.y + 13 + j * (size + 2)), ln,
                                     fontname="hebo" if is_link else "helv", fontsize=size,
                                     color=LINK if is_link else INK, align=align)
                if is_link:
                    self.links.append((self.pno, fitz.Rect(x, self.y, x + widths[c], self.y + h), dests[ri]))
                x += widths[c]
            self.y += h
            self.md.append("| " + " | ".join(latin(str(v)).replace("|", "/") for v in (list(r) + [""] * ncol)[:ncol]) + " |")
        self.page.draw_line((MARGIN, self.y), (PW - MARGIN, self.y), color=WARM_EDGE, width=0.7)
        self.y += 4
        if max_rows is not None and len(rows) > max_rows:
            self.note(f"{len(rows) - max_rows} more row(s) are in the project knowledge base (sections/scope_index.json).")
        self.y += 5

    def note(self, text, alert=False):
        for ln in wrap(text, "heit", 6.8, PW - 2 * MARGIN - 8):
            self.ensure(10)
            tbox(self.page, fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + 10), ln, fontname="heit",
                                     fontsize=6.8, color=SIGNAL if alert else INK_SOFT, align=1)
            self.y += 9
        self.y += 3
        self.md.append(f"_{latin(text)}_\n")

    def image(self, path, max_h=190, caption=None):
        try:
            pix = fitz.Pixmap(str(path))
        except Exception:                                # noqa: BLE001  (a missing crop never stops the legend)
            return
        w_avail = PW - 2 * MARGIN - 12
        scale = min(w_avail / pix.width, max_h / pix.height, 1.2)
        w, h = pix.width * scale, pix.height * scale
        self.ensure(h + 18)
        x = (PW - w) / 2
        r = fitz.Rect(x, self.y + 3, x + w, self.y + 3 + h)
        self.page.draw_rect(fitz.Rect(r.x0 - 3, r.y0 - 3, r.x1 + 3, r.y1 + 3), color=WARM_EDGE, fill=WHITE, width=0.6)
        self.page.insert_image(r, pixmap=pix)
        self.page.draw_rect(r, color=NAVY, width=0.5)
        self.y += h + 9
        if caption:
            tbox(self.page, fitz.Rect(MARGIN, self.y, PW - MARGIN, self.y + 10), latin(caption), fontname="helv",
                                     fontsize=6.5, color=INK_SOFT, align=1)
            self.y += 11


def pdf_string(s):
    return "(" + s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ")"


def dest_name(kind, key):
    """Stable, ASCII destination name. The same sheet always gets the same name."""
    return f"{kind}:" + re.sub(r"[^A-Za-z0-9._-]+", "-", str(key)).strip("-")


def write_named_destinations(doc, dests):
    """dests: name -> (page index, x, y in displayed page points). Written as a /Names /Dests name tree.

    Explicit numbers only: a null in the /XYZ view breaks pdf.js and older PyMuPDF outline parsing."""
    entries = {}
    # Keep the named destinations the source set already carries: its own links may point at them.
    # resolve_names() reports the raw PDF point, so it is written back unchanged.
    try:
        carried = doc.resolve_names() or {}
    except Exception:                                    # noqa: BLE001  (older PyMuPDF: nothing to carry)
        carried = {}
    for name, d in carried.items():
        pno = d.get("page", -1)
        if name in dests or not isinstance(pno, int) or not 0 <= pno < doc.page_count:
            continue
        x, y = (list(d.get("to") or (0, 0)) + [0, 0])[:2]
        entries[name] = f"[{doc[pno].xref} 0 R/XYZ {round(x, 2)} {round(y, 2)} {round(d.get('zoom') or 0, 2)}]"
    for name in dests:
        pno, x, y = dests[name]
        page = doc[pno]
        pt = fitz.Point(x, y) * page.derotation_matrix * ~page.transformation_matrix
        entries[name] = f"[{page.xref} 0 R/XYZ {round(pt.x, 2)} {round(pt.y, 2)} 0]"
    # A name tree's keys must be in byte order.
    items = [pdf_string(n) + entries[n] for n in sorted(entries, key=lambda n: n.encode("latin-1", "replace"))]
    tree = doc.get_new_xref()
    doc.update_object(tree, "<</Names[" + "".join(items) + "]>>")
    # Path form: sets /Dests whether /Names is absent, inline or indirect, and leaves the other name trees alone.
    doc.xref_set_key(doc.pdf_catalog(), "Names/Dests", f"{tree} 0 R")
    return len(dests)


def add_named_link(doc, page, rect, name, target_page):
    """A link annotation whose action is GoTo <named destination>."""
    before = {x[0] for x in page.annot_xrefs()}
    page.insert_link({"kind": fitz.LINK_GOTO, "from": rect, "page": target_page, "to": fitz.Point(0, 0), "zoom": 0})
    new = [x[0] for x in page.annot_xrefs() if x[0] not in before]
    if not new:
        return False
    doc.xref_set_key(new[0], "A", f"<</S/GoTo/D{pdf_string(name)}>>")
    # Drop /Dest outright: a leftover "/Dest null" beside /A is read differently by different viewers.
    obj = doc.xref_object(new[0], compressed=True)
    cleaned = re.sub(r"/Dest\s*(null|\[[^\]]*\])", "", obj)
    if cleaned != obj:
        doc.update_object(new[0], cleaned)
    return True


def fmt_party(p):
    if not p:
        return None
    return p.get("name") if isinstance(p, dict) else str(p)


def build_legend(atlas, scope, sheets, sheet_dest, model_dir, project_name):
    """Lay out the Index Legend. Returns the Legend (pages, named links, anchors, markdown)."""
    pi = (scope or {}).get("project_index") or {}
    L = Legend("Index Legend", project_name, f"NTXP PLANS ATLAS  |  {len(sheets)} SHEETS  |  EVERY BLUE ENTRY IS A LIVE LINK")
    L.md.append(f"# Index Legend: {project_name}\n")
    sdest = lambda sid: sheet_dest.get(sid)                # noqa: E731
    by_id = {s["sheet_id"]: s for s in sheets}
    concepts = atlas.get("concepts") or {}

    # ---- project index
    L.section("Project Index", "index:project")
    addr = pi.get("address") or {}
    L.kv([("Project Title", pi.get("title") or project_name), ("Project Number", pi.get("number")),
          ("Project Address", ", ".join(x for x in (addr.get("street"), addr.get("city_state_zip")) if x)),
          ("Project Owner", fmt_party(pi.get("owner"))), ("Project Architect", fmt_party(pi.get("architect"))),
          ("Project MEP Engineer", fmt_party(pi.get("mep_engineer"))),
          *[(f"Engineer: {e.get('role', '').title()}", e.get("name")) for e in pi.get("engineers_other") or []]])
    if not scope:
        L.note("The scope index has not been built for this set, so this legend lists sheets, trades and specs only.", True)

    contents = [("Page Index", "index:pages"), ("Trades", "index:trades"), ("Spec Sections", "index:specs"),
                ("General and Sheet Notes", "index:notes"), ("Clarifications and Exclusions", "index:clarifications"),
                ("Rooms", "index:rooms")]
    L.heading("Contents")
    scope_divs = [d for d in SCOPE_ORDER if d in ((scope or {}).get("scope") or {})]
    scope_divs += sorted(d for d in ((scope or {}).get("scope") or {}) if d not in SCOPE_ORDER)
    for d in scope_divs:
        v = scope["scope"][d]
        contents.append((SCOPE_TITLES.get(d) or f"Division {d} {v['label']} Scope Index", f"index:scope-{d}"))
    L.chips(contents, lambda it: it[1], lambda it: it[0])

    trades = [t for t in concepts.get("trades", []) if t.get("sheet_ids")]
    if trades:
        L.heading("Sheets by Trade", "CSI MasterFormat division")
        L.bars([(f"Div {t['division']}  {t.get('label', '')}", len(t["sheet_ids"])) for t in trades])
    L.heading("Markup Colour Key", "NTXP construction markup standard: hue carries trade; dotted is demolition, solid is new work")
    L.swatches(TRADE_COLORS)

    # ---- page index
    pages = pi.get("pages") or [{"page": s.get("page"), "sheet_id": s["sheet_id"], "sheet_no": s.get("sheet_no"),
                                 "sheet_title": s.get("title"), "details": []} for s in sheets]
    pages = [p for p in pages if p["sheet_id"] in by_id]
    L.section("Page Index", "index:pages", len(pages))
    rows = [[str(p["page"]), p["sheet_no"], p.get("sheet_title") or "",
             "; ".join(f"{d['label'] or '-'} {d['title']}" for d in p.get("details") or [])] for p in pages]
    L.table(["Page", "Sheet", "Page Title", "Detail Labels and Titles"], rows, weights=[5, 9, 26, 46], link_col=1,
            dests=[sdest(p["sheet_id"]) for p in pages])

    # ---- trades / specs / areas / phases
    L.section("Trades (CSI Division)", "index:trades", len(trades))
    for t in trades:
        L.heading(f"Division {t['division']}  {t.get('label', '')}",
                  f"{len(t['sheet_ids'])} sheets" + (f"  |  specs {', '.join(t['spec_sections'][:6])}" if t.get("spec_sections") else ""),
                  dest=f"index:scope-{t['division']}" if str(t["division"]) in ((scope or {}).get("scope") or {}) else None)
        L.chips(sorted(x for x in t["sheet_ids"] if x in by_id), sdest, lambda sid: by_id[sid].get("sheet_no") or sid)
    specs = [sp for sp in concepts.get("specs", []) if sp.get("sheet_ids")]
    L.section("Spec Sections", "index:specs", len(specs))
    for sp in sorted(specs, key=lambda x: x["section"]):
        L.heading(f"Section {sp['section']}", f"Div {sp['division']}" + (f"  {sp['title']}" if sp.get("title") else ""))
        L.chips(sorted(x for x in sp["sheet_ids"] if x in by_id), sdest, lambda sid: by_id[sid].get("sheet_no") or sid)
    for key, title, name_of in (("areas", "Areas", lambda a: a.get("area") or a.get("label") or ""),
                                ("phases", "Phases", lambda a: f"Phase {a.get('phase', '')}")):
        items = concepts.get(key) or []
        if items:
            L.section(title, f"index:{key}", len(items))
            for it in items:
                L.heading(name_of(it))
                L.chips(sorted(x for x in it.get("sheet_ids", []) if x in by_id), sdest,
                        lambda sid: by_id[sid].get("sheet_no") or sid)
    if not scope:
        L.finish()
        return L

    # ---- notes
    notes = [b for b in pi.get("notes") or [] if b["sheet_id"] in by_id]
    L.section("General and Sheet Notes", "index:notes", sum(len(b["items"]) for b in notes))
    if not notes:
        L.note("No notes blocks were found on the sheets.")
    for b in notes:
        L.heading(f"{b['sheet_no']}  {b['heading']}", f"Page {b['page']}  |  {b.get('sheet_title') or ''}", dest=sdest(b["sheet_id"]))
        rows = [[i["no"] or "-", i["text"][:420]] for i in b["items"]]
        L.table(["No.", "Note"], rows, weights=[4, 60], max_rows=30)

    # ---- clarifications and exclusions
    clar = scope.get("clarifications") or {}
    labels = scope.get("clarification_labels") or {}
    L.section("Clarifications and Exclusions", "index:clarifications", sum(len(v) for v in clar.values()))
    L.note("Notes sorted by what they affect. A note can appear under more than one header. Sorted by keyword: read each one "
           "on its sheet before relying on it.")
    for key in ("scheduling", "exclusions", "owner_vendors", "owner_allowance", "pricing_alternates", "phasing"):
        rows_src = [c for c in clar.get(key) or [] if c["sheet_id"] in by_id]
        L.heading(labels.get(key, key), f"{len(rows_src)} note(s)")
        if not rows_src:
            L.note("None found on the sheets.")
            continue
        L.table(["Sheet", "Page", "Note", "Related Trades"],
                [[c["sheet_no"], str(c["page"]), c["text"][:380], ", ".join("Div " + d for d in c.get("divisions") or [])]
                 for c in rows_src], weights=[9, 5, 52, 14], link_col=0, dests=[sdest(c["sheet_id"]) for c in rows_src],
                max_rows=60)

    # ---- rooms
    rooms = [r for r in pi.get("rooms") or [] if r["sheet_id"] in by_id]
    L.section("Rooms", "index:rooms", len(rooms))
    if rooms:
        L.table(["Room No.", "Room Name", "SF", "Perimeter LF", "Sheet"],
                [[r["number"], r["name"], f"{r['sf']:,.0f}" if r.get("sf") is not None else "not printed",
                  f"{r['perimeter_lf']:,.0f}" if r.get("perimeter_lf") is not None else "not printed", r["sheet_no"]]
                 for r in rooms], weights=[10, 28, 10, 12, 10], link_col=4, dests=[sdest(r["sheet_id"]) for r in rooms],
                max_rows=220)
        L.note("SF is listed only where it is printed on the plan. Perimeter is not printed on drawings; both come from the takeoff.")
    else:
        L.note("No room tags were found on the plan sheets.")

    # ---- scope index per trade
    schedules = {s["id"]: s for s in scope.get("schedules") or [] if s["sheet_id"] in by_id}
    millwork = {m["id"]: m for m in scope.get("millwork") or [] if m["sheet_id"] in by_id}
    for d in scope_divs:
        v = scope["scope"][d]
        title = SCOPE_TITLES.get(d) or f"Division {d} {v['label']} Scope Index"
        L.section(title, f"index:scope-{d}")
        if v.get("sheets"):
            L.heading("Sheets")
            L.chips([s["sheet_id"] for s in sheets if (s.get("sheet_no") or s["sheet_id"]) in set(v["sheets"])], sdest,
                    lambda sid: by_id[sid].get("sheet_no") or sid)
        for sid_ in v.get("schedules") or []:
            sch = schedules.get(sid_)
            if not sch:
                continue
            L.heading(sch["title"], f"{sch['sheet_no']}  |  Page {sch['page']}  |  {sch['row_count']} rows"
                      + (f"  |  specs {', '.join(sch['spec_sections'][:5])}" if sch.get("spec_sections") else ""),
                      dest=f"schedule:{sch['id']}")
            if sch.get("crop"):
                L.image(model_dir / sch["crop"], caption=f"As drawn on {sch['sheet_no']}")
            cols = sch["columns"][:9]
            L.table(cols, [r[:9] for r in sch["rows"]], max_rows=30)
            if sch["confidence"] < 0.6:
                L.note("Rebuilt from text columns, not ruled lines. Check it against the image above.", True)
        if d == "08":
            marks = v.get("door_marks") or []
            if marks:
                L.heading("Door Labels on Plan", f"{len(marks)} opening(s)")
                L.table(["Mark", "Plan Sheet", "Schedule"],
                        [[m["mark"], ", ".join(r["sheet_no"] or r["sheet_id"] for r in m["plan_refs"]) or "not found on a plan",
                          m["schedule_id"]] for m in marks], weights=[12, 30, 14], link_col=1,
                        dests=[sdest(m["plan_refs"][0]["sheet_id"]) if m["plan_refs"] else None for m in marks], max_rows=120)
            elevs = v.get("door_elevations") or []
            if elevs:
                L.heading("Door Elevations")
                L.table(["Label", "Title", "Sheet"], [[e.get("label") or "-", e["title"], e["sheet_no"]] for e in elevs],
                        weights=[8, 40, 10], link_col=2, dests=[sdest(e["sheet_id"]) for e in elevs])
        if d == "06":
            for mid in v.get("millwork_elevations") or []:
                m = millwork.get(mid)
                if not m:
                    continue
                L.heading(f"{m.get('label') or ''} {m['title']}".strip(), f"{m['sheet_no']}  |  Page {m['page']}",
                          dest=sdest(m["sheet_id"]))
                if m.get("crop"):
                    L.image(model_dir / m["crop"], max_h=150)
                L.table(["Item", "As Printed on the Elevation"], [
                    ["Room", m.get("room_number") or "not printed"],
                    ["Cabinet codes", ", ".join(m["cabinet_codes"]) or "none printed"],
                    ["Finish codes", ", ".join(m["finish_codes"]) or "none printed"],
                    ["Dimensions", ", ".join(m["dimensions_printed"]) or "none printed"],
                    ["Countertop / Sink / Backsplash", " / ".join("yes" if m[k] else "not noted" for k in
                                                               ("countertop_noted", "sink_noted", "backsplash_noted"))],
                    ["Cabinet count, linear feet, depths", "not measured: read from the elevation by the estimator"],
                    ["Spec sections", ", ".join(m.get("spec_sections") or []) or "none linked"]], weights=[22, 50])
        tags = v.get("size_tags") or []
        if tags:
            L.heading("Sizes Tagged on the Sheets", "a count of printed tags, not a measured length")
            L.table(["Type", "Size", "Tags", "Measured Qty", "Sheets"],
                    [[t["label"], t["size"], str(t["tag_count"]), "not measured",
                      ", ".join(x["sheet_no"] for x in t["sheets"][:8])] for t in tags], weights=[16, 10, 6, 10, 30],
                    max_rows=60)
        if v.get("takeoff"):
            L.heading("Measured Quantities", "from the quantity takeoff")
            L.table(["ID", "Description", "Quantity", "Unit"],
                    [[str(q.get("takeoff_id", "")), str(q.get("description", "")), str(q.get("quantity", "")),
                      str(q.get("uom", ""))] for q in v["takeoff"]], weights=[8, 44, 10, 6], max_rows=80)
        else:
            L.note(v.get("takeoff_status") or "No takeoff yet.")
        if v.get("notes"):
            L.heading("Notes on This Trade's Sheets")
            L.chips(v["notes"], lambda n: sdest(n["sheet_id"]), lambda n: f"{n['sheet_no']} {n['heading']} ({n['items']})")

    review = scope.get("needs_review") or []
    if review:
        L.section("Check Before Relying on This Index", "index:review", len(review))
        for r in review:
            L.para("- " + r)
    L.finish()
    return L


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--model", required=True, type=Path, help="project model/ dir holding sections/plans_atlas.json")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--project", default="", help="Project name for the legend header.")
    ap.add_argument("--legend-out", type=Path, help="Also save the Index Legend alone (for the knowledge base).")
    ap.add_argument("--legend-md", type=Path, help="Also save the Index Legend as Markdown (for the knowledge base).")
    a = ap.parse_args()

    atlas = json.loads((a.model / "sections" / "plans_atlas.json").read_text())
    scope_path = a.model / "sections" / "scope_index.json"
    scope = json.loads(scope_path.read_text()) if scope_path.is_file() else None
    doc = fitz.open(str(a.pdf))
    n_orig = doc.page_count
    # Page numbers restart at 1 in every source PDF; only this PDF's sheets map here.
    sheets = sorted((x for x in atlas["sheets"] if x.get("source_doc") == a.pdf.name
                     and 1 <= int(x.get("page") or 0) <= n_orig), key=lambda s: int(s["page"]))
    if not sheets:
        sys.exit(f"no sheets in plans_atlas.json come from {a.pdf.name}; run deploy_atlas.py on this set first")
    mine = {x["sheet_id"] for x in sheets}
    orig_page = {s["sheet_id"]: int(s["page"]) - 1 for s in sheets}
    sheet_dest = {s["sheet_id"]: dest_name("sheet", s.get("sheet_no") or s["sheet_id"]) for s in sheets}
    by_no = {}
    for s in sheets:
        by_no.setdefault(s.get("sheet_no"), s["sheet_id"])

    # ---- 1. the legend, laid out on its own so its page count is known ------
    name = a.project or ((scope or {}).get("project_index") or {}).get("title") or a.pdf.stem
    L = build_legend(atlas, scope, sheets, sheet_dest, a.model, name)
    n_leg = L.doc.page_count
    if a.legend_out:
        a.legend_out.parent.mkdir(parents=True, exist_ok=True)
        L.doc.save(str(a.legend_out), garbage=3, deflate=True)
    if a.legend_md:
        a.legend_md.parent.mkdir(parents=True, exist_ok=True)
        a.legend_md.write_text("\n".join(L.md).strip() + "\n")

    toc_before = doc.get_toc()
    doc.insert_pdf(L.doc, start_at=0)                    # legend goes in front of the first drawing
    page_of = {sid: p + n_leg for sid, p in orig_page.items()}

    # ---- 2. named destinations ---------------------------------------------
    dests = {sheet_dest[sid]: (page_of[sid], 0, 0) for sid in mine}
    for anchor, (pno, y) in L.anchors.items():
        dests[anchor] = (pno, 0, max(y - 6, 0))
    for sch in (scope or {}).get("schedules") or []:
        box_ok = isinstance(sch.get("box"), (list, tuple)) and len(sch["box"]) >= 2
        if sch.get("sheet_id") in mine and sch.get("id") and box_ok:
            pg = doc[page_of[sch["sheet_id"]]]
            dests[dest_name("schedule", sch["id"])] = (page_of[sch["sheet_id"]], sch["box"][0] * pg.rect.width,
                                                       sch["box"][1] * pg.rect.height)
    n_dests = write_named_destinations(doc, dests)
    dest_page = {n: v[0] for n, v in dests.items()}

    # ---- 3. live callout links on the drawing pages ------------------------
    existing = {p: [fitz.Rect(l["from"]) for l in doc[p].get_links()] for p in set(page_of.values())}
    added, why = 0, {"unresolved": 0, "same_sheet": 0, "overlaps_original": 0}
    for l in atlas.get("links", []):
        if l.get("from_sheet") not in mine:
            continue
        to = l.get("to_sheet") if l.get("to_sheet") in mine else by_no.get(l.get("to_sheet"))
        box = l.get("from_box")
        if to is None or not box:
            why["unresolved"] += 1
            continue
        src, dst = page_of[l["from_sheet"]], page_of[to]
        if src == dst:
            why["same_sheet"] += 1
            continue
        page = doc[src]
        W, H = page.rect.width, page.rect.height
        shown = fitz.Rect(box[0] * W - 2, box[1] * H - 2, box[2] * W + 2, box[3] * H + 2)
        # get_links() reports rectangles as displayed, so the overlap test is made in displayed space;
        # the link itself is inserted in the page's unrotated space.
        if any(shown.intersects(e) for e in existing[src]):
            why["overlaps_original"] += 1                 # never shadow an original link
            continue
        r = shown * page.derotation_matrix
        r.normalize()
        if add_named_link(doc, page, r, sheet_dest[to], dst):
            existing[src].append(shown)
            added += 1
    log(f"callout links added {added}, skipped {sum(why.values())} {why}")

    # ---- 4. legend links ----------------------------------------------------
    legend_links = 0
    for pno, rect, name_ in L.links:
        if name_ in dest_page and add_named_link(doc, doc[pno], rect, name_, dest_page[name_]):
            legend_links += 1

    # ---- 5. outline and page labels -----------------------------------------
    toc = [[1, "Index Legend", 1]] + [[lvl, t, p + 1] for lvl, t, p in L.outline]
    if toc_before:
        toc += [[lvl, t, pg + n_leg, *rest] for lvl, t, pg, *rest in toc_before]
    else:
        toc.append([1, "Drawings", n_leg + 1])
        toc += [[2, latin(f"{s.get('sheet_no') or s['sheet_id']}  {s.get('title') or ''}".strip()), page_of[s["sheet_id"]] + 1]
                for s in sheets]
    doc.set_toc(toc)
    label_of = {page_of[s["sheet_id"]]: s.get("sheet_no") or s["sheet_id"] for s in sheets}
    rules = [{"startpage": 0, "prefix": "Index ", "style": "D", "firstpagenum": 1}]
    for p in range(n_leg, doc.page_count):
        rules.append({"startpage": p, "prefix": latin(label_of[p]), "style": "", "firstpagenum": 1} if p in label_of
                     else {"startpage": p, "prefix": "", "style": "D", "firstpagenum": p - n_leg + 1})
    try:
        doc.set_page_labels(rules)
    except Exception as e:                               # noqa: BLE001  (labels are a convenience, never a blocker)
        log(f"page labels not written: {e}")

    meta = dict(doc.metadata or {})
    meta["subject"] = ((meta.get("subject") or "") + " | NTXP Plans Atlas: Index Legend in front, named-destination links").strip(" |")
    doc.set_metadata(meta)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(a.out), garbage=3, deflate=True)
    log(f"wrote {a.out}: {n_leg} legend pages in front of {n_orig} drawing pages")
    print(json.dumps({"status": "built", "out": str(a.out), "drawing_pages": n_orig, "index_pages": n_leg,
                      "callout_links_added": added, "legend_links": legend_links, "named_destinations": n_dests,
                      "legend_out": str(a.legend_out) if a.legend_out else None,
                      "legend_md": str(a.legend_md) if a.legend_md else None}))


if __name__ == "__main__":
    main()
