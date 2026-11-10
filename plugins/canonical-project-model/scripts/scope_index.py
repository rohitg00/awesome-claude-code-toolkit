#!/usr/bin/env python3
"""Build the Plans Atlas scope index from the drawing set.

Deterministic, no network, no model calls. Reads the drawing PDFs listed in
sections/plans_atlas.json and writes sections/scope_index.json plus cropped
schedule images under atlas/crops/:

  project_index    title, address, owner, architect, engineers; the page index
                   with detail labels and titles; general and sheet notes per
                   page; rooms (number, name, SF where printed); millwork
                   elevations; subcontractor trades
  clarifications   notes sorted under scheduling, exclusions, owner-required
                   vendors, owner allowances, pricing and alternates, phasing,
                   each with its page and related trades
  schedules        every schedule found on the sheets: a cropped image and the
                   table recreated as text, typed (door, hardware, finish,
                   lighting, plumbing fixture, equipment, panel ...)
  scope            one index per CSI division: its schedules, notes, details,
                   size tags (duct, pipe, conduit, wire) and takeoff quantities

Rules this file keeps:
  * Never invent. A value that is not printed on the sheets is null, and the
    reason is written beside it. Size tags are counted, not measured: a
    measured length only ever comes from the takeoff section.
  * Everything carries its sheet, page and box, so every row can be opened on
    the drawing (viewer `#sheet=<id>&box=...`, PDF named destination).
  * Heuristic finds carry a confidence and are listed in needs_review.

    python scope_index.py build --model <project>/model [--pdf-dir <dir>]
    python scope_index.py selftest
"""
import argparse
import datetime as dt
import json
import re
import statistics
import sys
import tempfile
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:                      # older PyMuPDF, or none
    try:
        import fitz
    except ImportError:
        fitz = None

HERE = Path(__file__).resolve().parent
SCHEMA = "ntxp.scope-index/1"
CROP_DPI = 110
MAX_ROWS_KEPT = 400

SCALE_RE = re.compile(r"(\d+/\d+\"\s*=\s*1'-?\s*0?\"|\d+\"\s*=\s*1'-?\s*0?\"|1\"\s*=\s*\d+'(?:-0\")?|\bN\.?T\.?S\.?\b|\d+:\d+)")
DETAIL_LABEL_RE = re.compile(r"^(?:[A-Z]{0,2}\d{1,2}|[A-Z]\d?)$")
NOTES_HEAD_RE = re.compile(r"^(?:[A-Z][A-Z&/\-. ]{0,44}\s)?(?:KEY\s?NOTES?|KEYED\s+NOTES?|NOTES?)\s*[:.]?$")
SCHEDULE_HEAD_RE = re.compile(r"\bSCHEDULES?\b")
ITEM_START_RE = re.compile(r"^\(?(\d{1,3}|[A-Z])[.)]\s+")
ROOM_NO_RE = re.compile(r"^[A-Z]{0,2}\d{3,5}[A-Z]?$")
SF_RE = re.compile(r"([\d,]{2,7})\s*(?:SF|S\.F\.|SQ\.?\s*FT\.?)\b")
SPEC_RE = re.compile(r"\b(\d{2})\s(\d{2})\s(\d{2})\b")
NOT_A_NAME = re.compile(r"SCALE|NORTH|SHEET|DETAIL|SECTION|ELEVATION|TYP\b|SEE\b|NOTE|REF\b|EXIST|DEMO|PLAN\b|\d'-")

CLARIFICATION_RULES = {
    "scheduling": r"\bschedul|working hours|after[- ]hours|night work|weekends?\b|sequence of (?:work|construction)|"
                  r"substantial completion|calendar days|working days|lead[- ]times?|milestone|shut[- ]?downs?|\boutages?\b|"
                  r"\d+\s*(?:hours?|days?)\s*(?:prior|notice|in advance)|prior notice|coordinate .{0,40}\bwith (?:the )?owner",
    "exclusions": r"not in contract|\bN\.?I\.?C\.?\b|\bby others\b|\bby owner\b|\bexclud|\bexclusion|not included|"
                  r"owner[- ]furnished|\bO\.?F\.?[CO]\.?I\.?\b|not (?:a )?part of (?:this|the) (?:contract|work|scope)",
    "owner_vendors": r"owner'?s?[- ](?:preferred|required|designated|approved|selected|standard)\b.{0,30}(?:vendor|contractor|"
                     r"subcontractor|supplier|manufacturer)|owner'?s? (?:vendor|contractor|subcontractor|supplier)|"
                     r"sole[- ]source|no substitutions?|proprietary|pre-?approved (?:vendor|contractor)",
    "owner_allowance": r"\ballowances?\b|\bcontingenc",
    "pricing_alternates": r"\balternates?\b|add[- ]alternate|deduct(?:ive)? alternate|unit prices?|base bid|bid items?|"
                          r"\bpricing\b|price separately|separate price|cost proposal",
    "phasing": r"\bphas(?:e|es|ed|ing)\b|temporary (?:partitions?|barriers?|egress|enclosures?)|infection control|\bICRA\b|"
               r"remain (?:in operation|operational|occupied)|occupied (?:building|area|space)|interim life safety|\bILSM\b",
}
CLARIFICATION_LABELS = {
    "scheduling": "Scheduling", "exclusions": "Exclusions", "owner_vendors": "Owner-Required Vendors",
    "owner_allowance": "Owner Allowances", "pricing_alternates": "Pricing and Alternates", "phasing": "Phasing",
}
_CLAR = {k: re.compile(v, re.I) for k, v in CLARIFICATION_RULES.items()}

# schedule title -> (type, CSI division). First match wins, so the order matters.
SCHEDULE_TYPES = [
    (r"HARDWARE", "door_hardware", "08"), (r"DOOR|FRAME|OPENING", "door", "08"),
    (r"WINDOW|GLAZING|STOREFRONT", "window", "08"),
    (r"FINISH|MATERIAL|COLOR", "finish", "09"),
    (r"LIGHT|LUMINAIRE|FIXTURE.*LIGHT", "lighting", "26"),
    (r"PANEL|SWITCHBOARD|FEEDER|TRANSFORMER|ELECTRICAL|RECEPTACLE", "electrical_equipment", "26"),
    (r"PLUMBING|LAVATOR|WATER\s?HEATER|DRAIN|FIXTURE", "plumbing_fixture", "22"),
    (r"DIFFUSER|GRILLE|AIR\s|FAN|VAV|RTU|AHU|UNIT|HVAC|MECHANICAL|DUCT|COIL|PUMP|BOILER|CHILLER", "hvac_equipment", "23"),
    (r"FIRE\s?ALARM", "fire_alarm", "28"), (r"SPRINKLER", "fire_protection", "21"),
    (r"CASEWORK|MILLWORK|CABINET|COUNTER", "millwork", "06"),
    (r"EQUIPMENT|APPLIANCE", "equipment", "11"), (r"SIGN", "signage", "10"),
    (r"PARTITION|WALL\sTYPE", "partition", "09"), (r"ROOM", "room", "09"),
]
DIV_KEYWORDS = [
    ("08", r"\bdoors?\b|\bframes?\b|hardware|glazing|storefront"), ("09", r"paint|gypsum|flooring|ceiling|\btile\b|finish"),
    ("22", r"plumbing|\bpip(?:e|ing)\b|domestic water|sanitary|lavator"), ("23", r"hvac|mechanical|duct|diffuser|\bair\b"),
    ("26", r"electrical|conduit|\bpanel\b|lighting|receptacle|\bpower\b"), ("21", r"sprinkler|fire protection"),
    ("28", r"fire alarm|access control|security"), ("27", r"\bdata\b|telecom|low[- ]voltage|\bcabling\b"),
    ("06", r"millwork|casework|cabinet|countertop"), ("02", r"demoli|\bremove\b|abatement"),
    ("03", r"concrete|slab"), ("07", r"firestop|sealant|waterproof|roof"), ("10", r"signage|toilet accessor|corner guard"),
]
_DIVKW = [(d, re.compile(p, re.I)) for d, p in DIV_KEYWORDS]

# size tags on MEP sheets: counted where printed, never measured
TAG_RULES = {
    "23": [("duct_rect", re.compile(r"\b(\d{1,3})\s?[xX]\s?(\d{1,3})\b")),
           ("duct_round", re.compile(r"\b(\d{1,2})\"?\s?(?:ø|Ø|DIA\b|RD\b)"))],
    "22": [("pipe", re.compile(r"(\d+(?:[- ]\d/\d)?|\d/\d)\"\s?(CW|HW|HWR|VTR|V|W|SAN|SS|G|CD|RD|OD|TW|FS|CA|MA|O2|VAC)\b"))],
    "21": [("sprinkler_pipe", re.compile(r"(\d+(?:[- ]\d/\d)?|\d/\d)\"\s?(FS|SP|FP)\b"))],
    "26": [("conduit", re.compile(r"(\d+(?:[- ]\d/\d)?|\d/\d)\"\s?(?:C\b|EMT\b|CONDUIT\b|RGS\b)")),
           ("wire", re.compile(r"(?<![\w/])(?:\d\s?)?#(\d{1,2}|\d/0)\b"))],
}
TAG_LABELS = {"duct_rect": "Rectangular duct", "duct_round": "Round duct", "pipe": "Pipe",
              "sprinkler_pipe": "Sprinkler pipe", "conduit": "Conduit", "wire": "Wire"}
CABINET_CODE_RE = re.compile(r"\b(?:B|W|SB|DB|BC|WC|T|U|VB)\d{2,4}\b")
FINISH_CODE_RE = re.compile(r"\b(?:PL|P-?LAM|SS|SSM|QTZ|WD|ST|PT|CPT|LVT|RB|ACT|CT|WC|SF|FRP)-?\d{1,2}[A-Z]?\b")
DIM_RE = re.compile(r"\d+'\s?-\s?\d+(?:\s\d/\d)?\"")
MILLWORK_RE = re.compile(r"CASEWORK|MILLWORK|CABINET|COUNTER|RECEPTION DESK|NURSE STATION|WORK ?STATION")
PARTY_LABELS = [
    ("owner", r"^OWNER\b"), ("architect", r"^ARCHITECT(?:URE|URAL)?\b"),
    ("mep_engineer", r"M\.?E\.?P\.?\b|MECH(?:ANICAL)?\b.*ENGINEER"),
    ("electrical_engineer", r"ELEC(?:TRICAL)?\b.*ENGINEER"), ("structural_engineer", r"STRUCT(?:URAL)?\b.*ENGINEER"),
    ("civil_engineer", r"CIVIL\b.*ENGINEER"), ("plumbing_engineer", r"PLUMB(?:ING)?\b.*ENGINEER"),
    ("fire_protection_engineer", r"FIRE\b.*ENGINEER"), ("technology_engineer", r"TECH(?:NOLOGY)?\b.*ENGINEER"),
    ("landscape_architect", r"LANDSCAPE"), ("interior_designer", r"INTERIOR"),
]
ADDRESS_RE = re.compile(r"\b\d{2,6}\s+[A-Z0-9 .'-]{3,40}\b(?:BLVD|STREET|ST|AVE|AVENUE|ROAD|RD|DRIVE|DR|LANE|LN|PKWY|PARKWAY|HWY|"
                        r"HIGHWAY|WAY|FWY|EXPY|COURT|CT|PLACE|PL)\b\.?", re.I)
CITY_RE = re.compile(r"\b([A-Z][A-Za-z .'-]{2,30}),\s*(TEXAS|TX|[A-Z]{2})\.?\s*(\d{5})(?:-\d{4})?\b")


def log(msg):
    sys.stderr.write(f"[scope-index] {msg}\n")


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1) + "\n")


# ------------------------------------------------------------------ text layer

class Line:
    __slots__ = ("text", "x0", "y0", "x1", "y1", "size", "words")

    def __init__(self, words):
        self.words = words
        self.text = " ".join(w["text"] for w in words).strip()
        self.x0 = min(w["bbox"][0] for w in words)
        self.y0 = min(w["bbox"][1] for w in words)
        self.x1 = max(w["bbox"][2] for w in words)
        self.y1 = max(w["bbox"][3] for w in words)
        self.size = max((w.get("size") or 0) for w in words) or (self.y1 - self.y0)

    @property
    def h(self):
        return max(self.y1 - self.y0, 1.0)

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def box(self):
        return (self.x0, self.y0, self.x1, self.y1)


def page_lines(page):
    """Lines of words in displayed-page coordinates. The page must be unrotated (see open_unrotated)."""
    raw = page.get_text("dict")
    out = []
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            words = []
            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text.strip():
                    continue
                x0, y0, x1, y1 = span["bbox"]
                toks = text.split()
                total = sum(len(t) for t in toks) or 1
                pos = x0
                for t in toks:
                    step = (x1 - x0) * len(t) / total
                    words.append({"bbox": (pos, y0, pos + step, y1), "text": t, "size": span.get("size", 0.0)})
                    pos += step
            if words:
                out.append(Line(words))
    return out


def norm_box(box, pw, ph):
    c = lambda v: round(max(0.0, min(1.0, v)), 4)      # noqa: E731
    return [c(box[0] / pw), c(box[1] / ph), c(box[2] / pw), c(box[3] / ph)]


def in_title_block(line, pw, ph):
    return line.cx > 0.86 * pw or (line.y0 > 0.92 * ph)


def upper_ratio(text):
    letters = [c for c in text if c.isalpha()]
    return (sum(c.isupper() for c in letters) / len(letters)) if letters else 0.0


def divisions_in_text(text):
    return [d for d, rx in _DIVKW if rx.search(text)]


# ------------------------------------------------------------------ extractors

def find_details(lines, pw, ph):
    """Detail bubbles: a scale line with a short label and an uppercase title beside it."""
    found, seen = [], set()
    for s in lines:
        if in_title_block(s, pw, ph) or not SCALE_RE.search(s.text) or len(s.text) > 40:
            continue
        near = [l for l in lines if l is not s and abs(l.y0 - s.y0) < 4.5 * s.h
                and l.x1 > s.x0 - 9 * s.h and l.x0 < s.x1 + 26 * s.h and not in_title_block(l, pw, ph)]
        titles = [l for l in near if not SCALE_RE.search(l.text) and upper_ratio(l.text) > 0.8
                  and re.search(r"[A-Z]{3,}", l.text) and len(l.text) <= 70 and not DETAIL_LABEL_RE.match(l.text)]
        if not titles:
            continue
        title = min(titles, key=lambda l: abs(l.y0 - s.y0) + abs(l.x0 - s.x0) * 0.15)
        labels = [l for l in near if DETAIL_LABEL_RE.match(l.text)]
        label = min(labels, key=lambda l: abs(l.y0 - title.y0) + abs(l.x1 - title.x0)) if labels else None
        key = (title.text, round(title.x0), round(title.y0))
        if key in seen:
            continue
        seen.add(key)
        box = (min(title.x0, s.x0, label.x0 if label else title.x0), min(title.y0, s.y0),
               max(title.x1, s.x1, label.x1 if label else title.x1), max(title.y1, s.y1))
        found.append({"label": label.text if label else None, "title": title.text,
                      "scale": SCALE_RE.search(s.text).group(1), "box": norm_box(box, pw, ph),
                      "_title_box": title.box, "confidence": 0.7 if label else 0.55})
    found.sort(key=lambda d: (d["box"][1], d["box"][0]))
    return found


def column_below(head, lines, pw, ph, max_lines=120):
    """Lines stacked under a heading, in its column, until a wide gap or the next heading."""
    left, right = head.x0 - 2.5 * head.h, max(head.x1 + 0.22 * pw, head.x0 + 0.28 * pw)
    pool = sorted((l for l in lines if l.y0 >= head.y1 - 1 and left <= l.x0 <= right and l is not head
                   and not in_title_block(l, pw, ph)), key=lambda l: (l.y0, l.x0))
    out, last_y1 = [], head.y1
    for l in pool:
        if out and (l.y0 - last_y1) > 3.2 * max(l.h, out[-1].h):
            break
        if not out and (l.y0 - last_y1) > 6 * head.h:
            break
        if NOTES_HEAD_RE.match(l.text.upper()) or (SCHEDULE_HEAD_RE.search(l.text.upper()) and len(l.text) < 60
                                                    and upper_ratio(l.text) > 0.8 and l.size >= head.size * 0.95):
            break
        out.append(l)
        last_y1 = max(last_y1, l.y1)
        if len(out) >= max_lines:
            break
    return out


def find_notes(lines, pw, ph):
    blocks = []
    for head in lines:
        t = head.text.upper().strip()
        if len(t) > 48 or not NOTES_HEAD_RE.match(t) or in_title_block(head, pw, ph):
            continue
        body = column_below(head, lines, pw, ph)
        if not body:
            continue
        items, cur = [], None
        for l in body:
            m = ITEM_START_RE.match(l.text)
            if m or cur is None:
                cur = {"no": m.group(1) if m else None, "text": l.text[m.end():] if m else l.text,
                       "box": list(l.box)}
                items.append(cur)
            else:
                cur["text"] += " " + l.text
                cur["box"] = [min(cur["box"][0], l.x0), min(cur["box"][1], l.y0),
                              max(cur["box"][2], l.x1), max(cur["box"][3], l.y1)]
        items = [i for i in items if len(i["text"].strip()) > 3]
        if not items:
            continue
        box = (min(head.x0, *(i["box"][0] for i in items)), head.y0,
               max(head.x1, *(i["box"][2] for i in items)), max(i["box"][3] for i in items))
        for i in items:
            i["text"] = re.sub(r"\s+", " ", i["text"]).strip()
            i["box"] = norm_box(i["box"], pw, ph)
        kind = "general" if "GENERAL" in t else "keyed" if "KEY" in t else "sheet"
        blocks.append({"heading": head.text.strip(" :."), "kind": kind, "items": items,
                       "box": norm_box(box, pw, ph), "confidence": 0.75})
    return blocks


def classify_schedule(title, sheet_division):
    up = title.upper()
    for pat, typ, div in SCHEDULE_TYPES:
        if re.search(pat, up):
            return typ, div
    return "other", sheet_division


def clean_rows(rows):
    out = []
    for r in rows or []:
        cells = [re.sub(r"\s+", " ", (c or "")).strip() for c in r]
        if any(cells):
            out.append(cells)
    if not out:
        return [], []
    width = max(len(r) for r in out)
    out = [r + [""] * (width - len(r)) for r in out]
    keep = [i for i in range(width) if any(r[i] for r in out)]
    out = [[r[i] for i in keep] for r in out]
    header_i = next((i for i, r in enumerate(out) if sum(1 for c in r if c) >= max(2, len(r) // 2)), None)
    if header_i is None:                                 # no row reads as a header: do not promote a data row
        return [], out
    return out[header_i], out[header_i + 1:]


def text_table(head, lines, pw, ph):
    """Fallback when the schedule has no ruling lines: rows by baseline, columns by left edges."""
    body = [l for l in lines if l.y0 > head.y1 and l.y0 < head.y1 + 0.35 * ph
            and l.x1 > head.x0 - 0.02 * pw and l.x0 < head.x0 + 0.45 * pw and not in_title_block(l, pw, ph)]
    if len(body) < 4:
        return None
    rows = {}
    for l in body:
        rows.setdefault(round(l.y0 / max(l.h, 4)), []).append(l)
    ordered = [sorted(v, key=lambda l: l.x0) for _, v in sorted(rows.items())]
    multi = [r for r in ordered if len(r) >= 2]
    if len(multi) < 3:
        return None
    edges = sorted({round(l.x0 / 6) * 6 for r in multi for l in r})
    cols = []
    for e in edges:
        if not cols or e - cols[-1] > 14:
            cols.append(e)
    table = []
    for r in multi:
        cells = [""] * len(cols)
        for l in r:
            i = max(range(len(cols)), key=lambda k: (cols[k] <= l.x0 + 7, cols[k]))
            cells[i] = (cells[i] + " " + l.text).strip()
        table.append(cells)
    box = (min(l.x0 for r in multi for l in r), head.y0, max(l.x1 for r in multi for l in r),
           max(l.y1 for r in multi for l in r))
    return table, box


def find_schedules(page, lines, pw, ph, sheet_division):
    heads = [l for l in lines if SCHEDULE_HEAD_RE.search(l.text.upper()) and len(l.text) <= 60
             and upper_ratio(l.text) > 0.8 and not in_title_block(l, pw, ph)
             and not re.search(r"\bSEE\b|\bREFER\b|\bPER\b|\bPROJECT SCHEDULE\b|CONSTRUCTION SCHEDULE", l.text.upper())]
    if not heads:
        return []
    words = [w for l in lines for w in l.words]

    def cell_text(rect):
        x0, y0, x1, y1 = rect
        inside = [w for w in words if x0 - 1 <= (w["bbox"][0] + w["bbox"][2]) / 2 <= x1 + 1
                  and y0 - 1 <= (w["bbox"][1] + w["bbox"][3]) / 2 <= y1 + 1]
        inside.sort(key=lambda w: (round(w["bbox"][1] / 4), w["bbox"][0]))
        return " ".join(w["text"] for w in inside)

    out = []
    for head in sorted(heads, key=lambda l: (l.y0, l.x0)):
        # look only in this heading's own region, so schedules set side by side stay separate
        right = min([h.x0 - 4 for h in heads if h is not head and h.x0 > head.x1 and abs(h.y0 - head.y0) < 0.05 * ph] + [0.86 * pw])
        bottom = min([h.y0 - 2 for h in heads if h is not head and h.y0 > head.y1 + 4 and h.x0 < right and h.x1 > head.x0] + [0.93 * ph])
        clip = fitz.Rect(max(head.x0 - 0.012 * pw, 0), head.y0 - 3, right, bottom)
        method, conf, rows, box = None, 0.0, None, None
        try:
            tables = sorted(page.find_tables(clip=clip).tables, key=lambda t: t.bbox[1])
        except Exception:                                # noqa: BLE001  (find_tables is best effort)
            tables = []
        for t in tables:
            if t.bbox[1] - head.y1 > 0.06 * ph:
                break
            # find_tables can return one table for two schedules sharing a row: keep this region's cells
            # Cells outside the region become blanks in place, so the cells that stay keep their columns;
            # clean_rows then drops the columns and rows that are blank throughout.
            mine = [[c if c and clip.x0 <= (c[0] + c[2]) / 2 <= clip.x1 else None for c in r.cells] for r in t.rows]
            flat = [c for r in mine for c in r if c]
            if not flat:
                continue
            tb = (min(c[0] for c in flat), min(c[1] for c in flat), max(c[2] for c in flat), max(c[3] for c in flat))
            grid = [[cell_text(c) if c else "" for c in r] for r in mine]
            header, body = clean_rows(grid)
            if header and SCHEDULE_HEAD_RE.search(" ".join(header).upper()) and body:
                header, body = body[0], body[1:]            # the title was the table's first row
            if header and body:
                rows = (header, body)
                box = (min(tb[0], head.x0), min(tb[1], head.y0), max(tb[2], head.x1), tb[3])
                method, conf = "ruled_table", 0.85
                break
        if rows is None:
            tt = text_table(head, lines, pw, ph)
            if tt:
                header, body = clean_rows(tt[0])
                if header and len(body) >= 2:
                    rows, box, method, conf = (header, body), tt[1], "text_columns", 0.5
        if rows is None:
            continue
        typ, div = classify_schedule(head.text, sheet_division)
        out.append({"title": head.text.strip(" :."), "type": typ, "division": div, "columns": rows[0],
                    "rows": rows[1][:MAX_ROWS_KEPT], "row_count": len(rows[1]), "method": method,
                    "confidence": conf, "_box": box, "box": norm_box(box, pw, ph)})
    return out


def find_rooms(lines, pw, ph):
    """Room tags on plans: a room number with its name printed directly above."""
    rooms = []
    for n in lines:
        if not ROOM_NO_RE.match(n.text) or in_title_block(n, pw, ph):
            continue
        above = [l for l in lines if 0 < n.y0 - l.y1 < 1.8 * n.h and abs(l.cx - n.cx) < max(l.x1 - l.x0, n.x1 - n.x0) * 0.6
                 and upper_ratio(l.text) > 0.85 and re.search(r"[A-Z]{3,}", l.text) and len(l.text) <= 34
                 and not NOT_A_NAME.search(l.text.upper())]
        if not above:
            continue
        name = max(above, key=lambda l: l.y1)
        sf, best = None, None
        for l in lines:
            if (abs(l.cx - n.cx) < 6 * n.h and -1 < l.y0 - n.y1 < 2.6 * n.h) or (l is n):
                m = SF_RE.search(l.text.upper())
                if m:
                    dist = 0 if l is n else (l.y0 - n.y1) + abs(l.cx - n.cx)
                    if best is None or dist < best:      # the nearest printed area belongs to this tag
                        best, sf = dist, float(m.group(1).replace(",", ""))
        box = (min(name.x0, n.x0), name.y0, max(name.x1, n.x1), n.y1)
        rooms.append({"number": n.text, "name": name.text, "sf": sf, "box": norm_box(box, pw, ph)})
    return rooms


def tag_counts(lines, division):
    counts = {}
    for kind, rx in TAG_RULES.get(division, []):
        for l in lines:
            for m in rx.finditer(l.text.upper()):
                if kind == "duct_rect":
                    a, b = int(m.group(1)), int(m.group(2))
                    if not (4 <= a <= 120 and 4 <= b <= 120):
                        continue
                    size = f"{a}x{b}"
                elif kind == "wire":
                    size = "#" + m.group(1)
                elif kind in ("pipe", "sprinkler_pipe"):
                    size = f'{m.group(1)}" {m.group(2)}'
                else:
                    size = m.group(1) + '"'
                counts[(kind, size)] = counts.get((kind, size), 0) + 1
    return counts


def millwork_region(detail, details, lines, pw, ph):
    """Text printed in the drawing area above a millwork elevation title."""
    tx0, ty0, tx1, _ = detail["_title_box"]
    right = min([d["_title_box"][0] for d in details if d is not detail and abs(d["_title_box"][1] - ty0) < 0.03 * ph
                 and d["_title_box"][0] > tx1] + [tx0 + 0.30 * pw])
    region = (tx0 - 0.03 * pw, ty0 - 0.24 * ph, right, ty0)
    text = " ".join(l.text.upper() for l in lines if l.x0 >= region[0] and l.x1 <= region[2] + 0.02 * pw
                    and region[1] <= l.y0 <= region[3])
    return region, text


def find_parties(lines):
    """Project team blocks on the cover: a role label with the firm name on the next line."""
    ordered = sorted(lines, key=lambda l: (round(l.y0 / 3), l.x0))
    parties = {}
    for i, l in enumerate(ordered):
        up = l.text.upper().strip(" :")
        if len(up) > 46:
            continue
        for role, pat in PARTY_LABELS:
            if role in parties or not re.search(pat, up):
                continue
            below = [m for m in lines if 0 <= m.y0 - l.y1 < 3.2 * l.h and abs(m.x0 - l.x0) < 6 * l.h and m is not l]
            below.sort(key=lambda m: m.y0)
            def is_label(t):
                u = t.upper().strip(" :")
                return len(u) <= 46 and any(re.search(p, u) for _, p in PARTY_LABELS)
            name = None
            for m in below:
                if is_label(m.text):                     # the next role starts here: this role has no firm printed
                    break
                if (re.search(r"[A-Za-z]{3,}", m.text) and not re.match(r"^\d", m.text)
                        and not re.search(r"ENGINEERS?$|^P:", m.text.upper())):
                    name = m.text.strip()
                    break
            if name:
                parties[role] = {"name": name, "label": l.text.strip(" :"), "confidence": 0.7}
            break
    return parties


# ------------------------------------------------------------------ build

def open_unrotated(path):
    """Open a PDF with page rotation folded into the content, so every box is in displayed coordinates."""
    doc = fitz.open(str(path))
    for page in doc:
        if page.rotation:
            page.remove_rotation()
    return doc


def crop_image(page, box, dest, pad=6):
    r = fitz.Rect(box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad) & page.rect
    if r.is_empty or r.width < 8 or r.height < 8:
        return False
    zoom = CROP_DPI / 72.0
    if max(r.width, r.height) * zoom > 2600:
        zoom = 2600 / max(r.width, r.height)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=r, alpha=False)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(dest), jpg_quality=78)
    return True


def classify_note(text):
    return [k for k, rx in _CLAR.items() if rx.search(text)]


def build(model_dir, pdf_dir=None, now=None, crops=True):
    model_dir = Path(model_dir)
    atlas = load_json(model_dir / "sections" / "plans_atlas.json")
    if not atlas or not atlas.get("sheets"):
        raise SystemExit(f"{model_dir}/sections/plans_atlas.json has no sheets: run deploy_atlas.py first")
    if fitz is None:
        raise SystemExit("PyMuPDF is required: pip install pymupdf")
    ident = load_json(model_dir / "sections" / "project_identity.json", {}) or {}
    takeoff = load_json(model_dir / "sections" / "quantity_takeoff.json", {}) or {}
    labels = {str(d.get("division")): d.get("title") or d.get("label") or ""
              for d in (load_json(HERE.parent / "resources" / "masterformat-divisions.json", {}) or {}).get("divisions", [])}
    trade_labels = {str(t.get("division")): t.get("label") or labels.get(str(t.get("division")), "")
                    for t in (atlas.get("concepts") or {}).get("trades") or []}
    spec_by_sheet = {}
    for sp in (atlas.get("concepts") or {}).get("specs") or []:
        for sid in sp.get("sheet_ids") or []:
            spec_by_sheet.setdefault(sid, []).append(sp.get("section"))

    search_dirs = [Path(pdf_dir)] if pdf_dir else []
    search_dirs += [model_dir.parent, *sorted((p for p in model_dir.parent.rglob("*") if p.is_dir()
                                               and "model" not in p.parts[-1:]), key=lambda p: (len(p.parts), str(p)))[:400]]
    def locate(name):
        for d in search_dirs:
            p = d / name
            if p.is_file():
                return p
        return None

    review, pages, notes, schedules, rooms, millwork = [], [], [], [], {}, []
    tags, clar = {}, {k: [] for k in CLARIFICATION_RULES}
    parties, addr, docs = {}, None, {}
    crop_dir = model_dir / "atlas" / "crops"
    def page_int(s):
        try:
            return int(s.get("page") or 0)
        except (TypeError, ValueError):                   # a bad page value skips the sheet, not the build
            return 0
    sheets = sorted(atlas["sheets"], key=lambda s: (str(s.get("source_doc")), page_int(s)))
    for s in sheets:
        name = s.get("source_doc")
        if name not in docs:
            path = locate(name) if name else None
            docs[name] = open_unrotated(path) if path else None
            if not path:
                review.append(f"drawing file not found, so its sheets were not indexed: {name}")
        doc = docs[name]
        pno = page_int(s)
        if doc is None or not (1 <= pno <= doc.page_count):
            if doc is not None:
                review.append(f"sheet skipped, page {s.get('page')!r} is not in {name}: {s.get('sheet_no') or s.get('sheet_id')}")
            continue
        page = doc[pno - 1]
        pw, ph = page.rect.width, page.rect.height
        lines = page_lines(page)
        sid, sno, stitle = s["sheet_id"], s.get("sheet_no") or s["sheet_id"], s.get("title") or ""
        sdiv = str((s.get("divisions") or ["01"])[0])
        ref = {"sheet_id": sid, "sheet_no": sno, "sheet_title": stitle, "page": pno, "doc": name}
        if not lines:
            pages.append({**ref, "details": [], "text_indexed": False})
            continue

        details = find_details(lines, pw, ph)
        pages.append({**ref, "text_indexed": True,
                      "details": [{k: v for k, v in d.items() if not k.startswith("_")} for d in details]})

        for b in find_notes(lines, pw, ph):
            b.update(ref, divisions=s.get("divisions") or [])
            notes.append(b)
            for it in b["items"]:
                for cat in classify_note(it["text"]):
                    clar[cat].append({**ref, "text": it["text"], "no": it["no"], "heading": b["heading"], "box": it["box"],
                                      "divisions": sorted(set((s.get("divisions") or []) + divisions_in_text(it["text"]))),
                                      "source": "note", "confidence": 0.75})

        for n, sch in enumerate(find_schedules(page, lines, pw, ph, sdiv), 1):
            sch_id = f"{sid}-S{n}"
            box = sch.pop("_box")
            sch.update(ref, id=sch_id, spec_sections=sorted(set(spec_by_sheet.get(sid, [])))[:12], crop=None)
            if crops and crop_image(page, box, crop_dir / f"{sch_id}.jpg"):
                sch["crop"] = f"atlas/crops/{sch_id}.jpg"
            schedules.append(sch)

        if re.search(r"\bPLAN\b", stitle.upper()) and not re.search(r"CEILING|ROOF|SITE|KEY PLAN", stitle.upper()):
            for r in find_rooms(lines, pw, ph):
                cur = rooms.get(r["number"])
                if cur is None or (cur["sf"] is None and r["sf"] is not None):
                    rooms[r["number"]] = {**r, **ref}

        for (kind, size), c in tag_counts(lines, sdiv).items():
            t = tags.setdefault((sdiv, kind, size), {"division": sdiv, "type": kind, "label": TAG_LABELS[kind], "size": size,
                                                     "tag_count": 0, "sheets": []})
            t["tag_count"] += c
            t["sheets"].append({"sheet_id": sid, "sheet_no": sno, "sheet_title": stitle, "page": pno, "count": c})

        for d in details:
            if not (MILLWORK_RE.search(d["title"].upper()) or (MILLWORK_RE.search(stitle.upper()) and "ELEV" in d["title"].upper())):
                continue
            region, text = millwork_region(d, details, lines, pw, ph)
            mid = f"{sid}-M{len([m for m in millwork if m['sheet_id'] == sid]) + 1}"
            rec = {**ref, "id": mid, "label": d["label"], "title": d["title"], "scale": d["scale"],
                   "box": norm_box(region, pw, ph),
                   "cabinet_codes": sorted(set(CABINET_CODE_RE.findall(text))),
                   "finish_codes": sorted(set(FINISH_CODE_RE.findall(text))),
                   "dimensions_printed": sorted(set(DIM_RE.findall(text)))[:24],
                   "countertop_noted": "COUNTER" in text, "sink_noted": "SINK" in text,
                   "backsplash_noted": "SPLASH" in text,
                   "cabinet_count": None, "linear_feet": None, "countertop_depth": None, "countertop_length": None,
                   "room_number": (re.search(r"\b[A-Z]{0,2}\d{3,5}[A-Z]?\b", d["title"]) or [None])[0],
                   "not_measured": "cabinet count, lengths and depths are read off the elevation by an estimator; "
                                   "only what is printed as text is listed here",
                   "spec_sections": [x for x in spec_by_sheet.get(sid, []) if x.startswith(("06", "12"))],
                   "crop": None, "confidence": 0.5}
            if crops and crop_image(page, region, crop_dir / f"{mid}.jpg"):
                rec["crop"] = f"atlas/crops/{mid}.jpg"
            millwork.append(rec)

        up_title = stitle.upper()
        if pno <= 3 or "COVER" in up_title or "GENERAL INFORMATION" in up_title:
            for role, p in find_parties(lines).items():
                parties.setdefault(role, {**p, **ref})
            if addr is None:
                for l in sorted(lines, key=lambda l: (l.y0, l.x0)):
                    a = ADDRESS_RE.search(l.text)
                    if not a:
                        continue
                    # City, state and ZIP count only when printed with the street: same line or the lines just under it.
                    c = CITY_RE.search(l.text[a.end():])
                    if not c:
                        under = sorted((m for m in lines if 0 <= m.y0 - l.y1 < 2.6 * l.h and abs(m.x0 - l.x0) < 8 * l.h),
                                       key=lambda m: m.y0)
                        c = next((x for x in (CITY_RE.search(m.text) for m in under) if x), None)
                    addr = {"street": a.group(0).strip(), "city_state_zip": c.group(0).strip() if c else None, **ref}
                    break

        # strong-keyword lines outside a notes block still belong in the clarifications
        noted = {it["text"] for b in notes if b["sheet_id"] == sid for it in b["items"]}
        for l in lines:
            if len(l.text.split()) < 5 or in_title_block(l, pw, ph) or any(l.text in t for t in noted):
                continue
            for cat in classify_note(l.text):
                if cat in ("owner_allowance", "pricing_alternates", "exclusions", "owner_vendors"):
                    clar[cat].append({**ref, "text": l.text, "no": None, "heading": None, "box": norm_box(l.box, pw, ph),
                                      "divisions": sorted(set((s.get("divisions") or []) + divisions_in_text(l.text))),
                                      "source": "text_line", "confidence": 0.5})

    for d in docs.values():
        if d is not None:
            d.close()

    # door labels: every mark in a door schedule, located on the plans
    door_marks = []
    door_schedules = [x for x in schedules if x["type"] == "door"]
    plan_words = load_json(model_dir / "atlas-words.json", {}) or {}
    sheet_meta = {s["sheet_id"]: s for s in sheets}
    for sch in door_schedules:
        for row in sch["rows"]:
            mark = (row[0] if row else "").strip()
            if not re.match(r"^[A-Z]{0,2}\d{2,5}[A-Z]?(?:[.\-][A-Z0-9]{1,2})?$", mark):
                continue
            refs = []
            for sid, words in plan_words.items():
                meta = sheet_meta.get(sid) or {}
                if sid == sch["sheet_id"] or not re.search(r"\bPLAN\b", (meta.get("title") or "").upper()):
                    continue
                for w in words:
                    if len(w) > 4 and w[4] == mark:
                        refs.append({"sheet_id": sid, "sheet_no": meta.get("sheet_no"), "box": [w[0], w[1], w[2], w[3]]})
                        break
            door_marks.append({"mark": mark, "schedule_id": sch["id"], "row": dict(zip(sch["columns"], row)),
                               "plan_refs": refs[:4]})
    door_elevs = [dict(d, sheet_id=p["sheet_id"], sheet_no=p["sheet_no"], page=p["page"])
                  for p in pages for d in p["details"] if re.search(r"DOOR|FRAME", d["title"].upper())
                  and re.search(r"TYPE|ELEV", d["title"].upper())]

    # finish schedule rows carry a link to their spec chapter when the atlas knows one
    spec_titles = {sp.get("section"): sp for sp in (atlas.get("concepts") or {}).get("specs") or []}
    for sch in schedules:
        if sch["type"] != "finish":
            continue
        sch["finishes"] = []
        for row in sch["rows"]:
            rec = dict(zip(sch["columns"], row))
            blob = " ".join(row)
            m = SPEC_RE.search(blob)
            sec = " ".join(m.groups()) if m else None
            sch["finishes"].append({"code": row[0] if row else "", "fields": rec, "spec_section": sec,
                                    "spec_pdf": (spec_titles.get(sec) or {}).get("pdf") if sec else None})

    # scope: one index per division that has anything
    takeoff_by_div = {}
    for it in takeoff.get("items") or []:
        d = str((it.get("csi") or {}).get("masterformat_division") or it.get("division") or "")
        if d:
            takeoff_by_div.setdefault(d, []).append({k: it.get(k) for k in ("takeoff_id", "description", "quantity", "uom")
                                                    if it.get(k) is not None})
    divisions = sorted({x["division"] for x in schedules} | {t["division"] for t in tags.values()} | set(takeoff_by_div)
                       | {d for b in notes for d in b.get("divisions") or []} | set(trade_labels))
    scope = {}
    for d in divisions:
        d_tags = sorted((t for t in tags.values() if t["division"] == d), key=lambda t: (t["type"], -t["tag_count"]))
        for t in d_tags:
            t["measured_quantity"], t["uom"] = None, None    # no quantity, so no unit either
            t["status"] = "tag count only: a measured length comes from the takeoff"
        scope[d] = {
            "division": d, "label": trade_labels.get(d) or labels.get(d) or f"Division {d}",
            "schedules": [x["id"] for x in schedules if x["division"] == d],
            "notes": [{"sheet_id": b["sheet_id"], "sheet_no": b["sheet_no"], "page": b["page"], "heading": b["heading"],
                       "items": len(b["items"])} for b in notes if d in (b.get("divisions") or [])],
            "size_tags": d_tags,
            "takeoff": takeoff_by_div.get(d, []),
            "takeoff_status": "from the quantity takeoff" if takeoff_by_div.get(d) else
                              "no takeoff yet: quantities are not measured by the atlas",
            "sheets": sorted({x["sheet_no"] for x in pages if d in (sheet_meta.get(x["sheet_id"], {}).get("divisions") or [])}),
        }
    scope.setdefault("08", {"division": "08", "label": labels.get("08", "Openings"), "schedules": [], "notes": [],
                            "size_tags": [], "takeoff": [], "takeoff_status": "no takeoff yet", "sheets": []})
    scope["08"]["door_marks"] = door_marks
    scope["08"]["door_elevations"] = door_elevs
    if millwork:
        scope.setdefault("06", {"division": "06", "label": labels.get("06", "Wood, Plastics and Composites"),
                                "schedules": [], "notes": [], "size_tags": [], "takeoff": [],
                                "takeoff_status": "no takeoff yet", "sheets": []})
        scope["06"]["millwork_elevations"] = [m["id"] for m in millwork]

    room_list = sorted(rooms.values(), key=lambda r: r["number"])
    for r in room_list:
        r["perimeter_lf"] = None
        r["sf_source"] = "printed on the plan" if r["sf"] is not None else None
    if room_list and not any(r["sf"] is not None for r in room_list):
        review.append("room square footage is not printed on the plans; SF and perimeter need the takeoff")
    elif room_list:
        review.append("room perimeter is not printed on the plans; it needs the takeoff")
    for cat in clar:                                     # one row per (sheet, text)
        seen, uniq = set(), []
        for c in clar[cat]:
            k = (c["sheet_id"], c["text"][:120])
            if k not in seen:
                seen.add(k)
                uniq.append(c)
        clar[cat] = uniq
    low = [x["id"] for x in schedules if x["confidence"] < 0.6]
    if low:
        review.append(f"{len(low)} schedule(s) were rebuilt from text columns, not ruled tables; check them against "
                      f"the image: {', '.join(low[:8])}")
    if millwork:
        review.append(f"{len(millwork)} millwork elevation(s) listed; cabinet counts and lengths are not measured")
    if any(t for t in tags.values()):
        review.append("duct, pipe, conduit and wire sizes are tag counts, not measured lengths")

    loc = ident.get("location") if isinstance(ident.get("location"), dict) else {}
    project_index = {
        "title": ident.get("title") or (atlas.get("project") or {}).get("title"),
        "number": ident.get("number"),
        "address": ({"street": loc.get("address"), "city_state_zip": ", ".join(x for x in (loc.get("city"), loc.get("state")) if x)
                     + (f" {loc['zip']}" if loc.get("zip") else ""), "source": "project record"} if loc.get("address") else addr),
        "owner": ({"name": ident["owner"], "source": "project record"} if ident.get("owner") else parties.get("owner")),
        "architect": parties.get("architect"),
        "mep_engineer": parties.get("mep_engineer"),
        "engineers_other": [{"role": k.replace("_", " "), **v} for k, v in parties.items()
                            if k not in ("owner", "architect", "mep_engineer")],
        "pages": pages, "notes": notes, "rooms": room_list,
        "millwork_elevations": [{"id": m["id"], "label": m["label"], "title": m["title"], "sheet_no": m["sheet_no"],
                                 "sheet_id": m["sheet_id"], "page": m["page"]} for m in millwork],
        "trades": [{"division": d, "label": v["label"], "sheets": len(v["sheets"]), "schedules": len(v["schedules"])}
                   for d, v in sorted(scope.items())],
    }
    for k in ("title", "address", "owner", "architect", "mep_engineer"):
        if not project_index.get(k):
            review.append(f"project {k.replace('_', ' ')} was not found on the cover sheets")
    stats = {"sheets": len(pages), "details": sum(len(p["details"]) for p in pages), "note_blocks": len(notes),
             "note_items": sum(len(b["items"]) for b in notes), "schedules": len(schedules), "rooms": len(room_list),
             "millwork_elevations": len(millwork), "door_marks": len(door_marks),
             "clarifications": {k: len(v) for k, v in clar.items()}}
    return {"section": "scope_index", "schema": SCHEMA,
            "generated_at": (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds"),
            "source_set": (atlas.get("source_set") or {}).get("documents") or [],
            "project_index": project_index, "clarifications": clar, "clarification_labels": CLARIFICATION_LABELS,
            "schedules": schedules, "millwork": millwork, "scope": scope, "stats": stats, "needs_review": review}


def cmd_build(args):
    idx = build(args.model, args.pdf_dir)
    out = Path(args.model) / "sections" / "scope_index.json"
    write_json(out, idx)
    print(json.dumps({"status": "built", "out": str(out), "stats": idx["stats"],
                      "needs_review": len(idx["needs_review"])}, indent=2))


# ------------------------------------------------------------------ selftest

def _selftest_pdf(path):
    doc = fitz.open()
    cover = doc.new_page(width=2592, height=1728)                     # 36x24 sheet
    t = lambda p, xy, s, size=11: p.insert_text(xy, s, fontsize=size, fontname="helv")   # noqa: E731
    t(cover, (200, 200), "OWNER", 12); t(cover, (200, 218), "Test Health System", 12)
    t(cover, (200, 300), "ARCHITECT", 12); t(cover, (200, 318), "Studio North Architects", 12)
    t(cover, (200, 400), "MECH & PLUMB ENGINEERS", 12); t(cover, (200, 418), "Campus Engineering", 12)
    t(cover, (200, 500), "5200 HARRY HINES BLVD.", 12); t(cover, (200, 518), "DALLAS, TEXAS 75235", 12)
    plan = doc.new_page(width=2592, height=1728)
    t(plan, (300, 300), "GENERAL NOTES", 14)
    t(plan, (300, 322), "1. Contractor shall provide 72 hours notice prior to any shutdown.")
    t(plan, (300, 338), "2. Signage is by owner and not in contract.")
    t(plan, (300, 354), "3. Include an allowance of $5,000 for patching.")
    t(plan, (300, 370), "4. Work shall be phased to keep the unit occupied; see ICRA plan.")
    t(plan, (300, 386), "5. Alternate No. 1: add corner guards at all corridors.")
    t(plan, (300, 402), "6. Use owner's preferred vendor for access control.")
    t(plan, (1200, 700), "PHARMACY", 11); t(plan, (1205, 716), "B1144", 11); t(plan, (1198, 732), "240 SF", 9)
    t(plan, (1500, 700), "TRIAGE", 11); t(plan, (1502, 716), "B1145", 11)
    t(plan, (1250, 760), "B1144A", 9)
    t(plan, (900, 1500), "A6", 12); t(plan, (940, 1500), "ENLARGED PLAN", 12); t(plan, (940, 1516), '1/4" = 1\'-0"', 9)
    sched = doc.new_page(width=2592, height=1728)
    t(sched, (300, 280), "DOOR SCHEDULE", 14)
    cols, rows = ["MARK", "WIDTH", "HEIGHT", "TYPE", "HDWR"], [["B1144A", "3'-0\"", "7'-0\"", "A", "HW-1"],
                                                               ["B1145A", "3'-6\"", "7'-0\"", "B", "HW-2"]]
    x0, y0, cw, rh = 300, 300, 150, 24
    for r, row in enumerate([cols] + rows):
        for c, cell in enumerate(row):
            sched.draw_rect(fitz.Rect(x0 + c * cw, y0 + r * rh, x0 + (c + 1) * cw, y0 + (r + 1) * rh), width=0.7)
            t(sched, (x0 + c * cw + 6, y0 + r * rh + 16), cell, 10)
    t(sched, (1300, 280), "FINISH SCHEDULE", 14)
    fcols, frows = ["CODE", "MANUFACTURER", "PRODUCT", "SPEC"], [["PT-1", "Sherwin", "ProMar 200", "09 91 23"]]
    for r, row in enumerate([fcols] + frows):
        for c, cell in enumerate(row):
            sched.draw_rect(fitz.Rect(1300 + c * 180, y0 + r * rh, 1300 + (c + 1) * 180, y0 + (r + 1) * rh), width=0.7)
            t(sched, (1306 + c * 180, y0 + r * rh + 16), cell, 10)
    t(sched, (700, 1500), "C3", 12); t(sched, (740, 1500), "CASEWORK ELEVATION - PHARMACY B1144", 12)
    t(sched, (740, 1516), '1/2" = 1\'-0"', 9); t(sched, (760, 1300), "B24", 9); t(sched, (820, 1300), "SB36", 9)
    t(sched, (760, 1260), "PL-1 COUNTERTOP", 9)
    mech = doc.new_page(width=2592, height=1728)
    t(mech, (400, 400), "12x8", 9); t(mech, (600, 400), "12x8", 9); t(mech, (800, 400), '10"ø', 9)
    doc.save(str(path))
    doc.close()


def selftest():
    if fitz is None:
        raise SystemExit("PyMuPDF is required for the selftest")
    tmp = Path(tempfile.mkdtemp(prefix="scope-index-"))
    model = tmp / "model"
    _selftest_pdf(tmp / "set.pdf")
    words = {"A-101": [[0.48, 0.43, 0.5, 0.44, "B1144A"]]}
    write_json(model / "atlas-words.json", words)
    mk = lambda sid, title, page, divs: {"sheet_id": sid, "sheet_no": sid, "title": title, "page": page,   # noqa: E731
                                         "source_doc": "set.pdf", "divisions": divs}
    write_json(model / "sections" / "plans_atlas.json", {"section": "plans_atlas", "sheets": [
        mk("G-001", "COVER SHEET", 1, ["01"]), mk("A-101", "FIRST FLOOR PLAN", 2, ["09"]),
        mk("A-601", "SCHEDULES AND CASEWORK", 3, ["08"]), mk("M-101", "MECHANICAL PLAN", 4, ["23"])],
        "concepts": {"trades": [{"division": "08", "label": "Openings", "sheet_ids": ["A-601"]}],
                     "specs": [{"section": "09 91 23", "division": "09", "title": "Painting", "sheet_ids": ["A-601"]}]}})
    write_json(model / "sections" / "quantity_takeoff.json", {"items": [
        {"takeoff_id": "Q1", "csi": {"masterformat_division": "23"}, "description": "Supply duct", "quantity": 120, "uom": "LF"}]})
    idx = build(model, tmp, now=dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc))
    pi = idx["project_index"]
    assert pi["owner"]["name"] == "Test Health System" and pi["architect"]["name"] == "Studio North Architects", pi
    assert pi["mep_engineer"]["name"] == "Campus Engineering", pi["mep_engineer"]
    assert pi["address"]["street"].startswith("5200 HARRY HINES") and "75235" in pi["address"]["city_state_zip"], pi["address"]
    notes = [b for b in pi["notes"] if b["sheet_id"] == "A-101"]
    assert notes and notes[0]["kind"] == "general" and len(notes[0]["items"]) == 6, notes
    c = idx["clarifications"]
    assert any("72 hours" in x["text"] for x in c["scheduling"]), c["scheduling"]
    assert any("not in contract" in x["text"] for x in c["exclusions"])
    assert any("allowance" in x["text"] for x in c["owner_allowance"])
    assert any("phased" in x["text"] for x in c["phasing"])
    assert any("Alternate" in x["text"] for x in c["pricing_alternates"])
    assert any("preferred vendor" in x["text"] for x in c["owner_vendors"])
    rooms = {r["number"]: r for r in pi["rooms"]}
    assert rooms["B1144"]["name"] == "PHARMACY" and rooms["B1144"]["sf"] == 240.0 and rooms["B1144"]["perimeter_lf"] is None
    assert rooms["B1145"]["sf"] is None, "SF is never invented"
    door = next(s for s in idx["schedules"] if s["type"] == "door")
    assert door["columns"][0] == "MARK" and door["rows"][0][0] == "B1144A" and door["method"] == "ruled_table", door
    assert door["crop"] and (model / door["crop"]).is_file(), "schedule screenshot saved"
    fin = next(s for s in idx["schedules"] if s["type"] == "finish")
    assert fin["finishes"][0]["code"] == "PT-1" and fin["finishes"][0]["spec_section"] == "09 91 23", fin
    marks = idx["scope"]["08"]["door_marks"]
    assert marks[0]["mark"] == "B1144A" and marks[0]["plan_refs"][0]["sheet_id"] == "A-101", marks
    assert any(d["title"] == "ENLARGED PLAN" and d["label"] == "A6" for p in pi["pages"] for d in p["details"]), pi["pages"]
    mw = idx["millwork"][0]
    assert "B24" in mw["cabinet_codes"] and "PL-1" in mw["finish_codes"] and mw["cabinet_count"] is None, mw
    assert mw["room_number"] == "B1144" and mw["countertop_noted"], mw
    hv = idx["scope"]["23"]
    duct = next(t for t in hv["size_tags"] if t["size"] == "12x8")
    assert duct["tag_count"] == 2 and duct["measured_quantity"] is None, duct
    assert hv["takeoff"][0]["quantity"] == 120, "measured quantities come only from the takeoff"
    again = build(model, tmp, now=dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc))
    assert json.dumps(again, sort_keys=True) == json.dumps(idx, sort_keys=True), "identical runs give identical output"
    print("scope_index selftest passed:", tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Write sections/scope_index.json and atlas/crops/.")
    b.add_argument("--model", required=True, help="Project model/ directory.")
    b.add_argument("--pdf-dir", help="Folder holding the drawing PDFs (default: searched under the project).")
    sub.add_parser("selftest")
    a = ap.parse_args()
    selftest() if a.cmd == "selftest" else cmd_build(a)


if __name__ == "__main__":
    main()
