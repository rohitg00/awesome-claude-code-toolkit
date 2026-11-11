#!/usr/bin/env python3
"""
build_atlas_data.py — deterministic Plans Atlas extraction.

This is the fix for the #1 architectural fault we are adapting the Drawing
Atlas concept away from: "no extraction script; the model must build atlas
data by hand-rolled code each run." THIS script IS that extraction. Given the
same PDF drawing set (and the same optional --model cross-links), it always
produces the same sections/plans_atlas.json, atlas-words.json sidecar, and
atlas/img/*.jpg images — replayable in CI, never re-derived by hand.

Pipeline position (mirrors assemble_model.py's philosophy: deterministic code
does the mechanical work, agents/Claude do any real judgement elsewhere):

    PDF drawing set (+ optional assembled canonical model)  ->
    per-page word/box extraction + title-block heuristics    ->
    deterministic callout/spec/sheet-reference link graph    ->
    concepts index (trades / specs / phases / areas)          ->
    sections/plans_atlas.json + atlas-words.json + atlas/img/*.jpg

Conforms to schemas/plans-atlas.schema.json (sheets/links/concepts/search),
using schemas/common.defs.schema.json's provenance + csi_ref shapes. CSI
MasterFormat division is the universal sort key throughout (see
resources/masterformat-divisions.json) — sheets, links, and concepts are all
emitted in division-then-sheet-number order.

PyMuPDF (fitz) is used for real text/image extraction but is OPTIONAL: when
it is not importable, the script degrades gracefully to manifest-only mode
(sheets built from filenames/CLI hints, searchable=false, no links/images)
rather than crashing. Everything else is Python 3.11 stdlib.

Never writes into the source PDF folder. Logs progress to stderr; the atlas
JSON goes to stdout only via --dry-run's plan (the real run writes files).
"""

import argparse
import glob
import json
import re
import sys
from pathlib import Path

try:
    import pymupdf as fitz  # PyMuPDF — optional; current import name
    FITZ_AVAILABLE = True
except ImportError:
    try:
        import fitz  # older PyMuPDF releases
        FITZ_AVAILABLE = True
    except ImportError:
        fitz = None
        FITZ_AVAILABLE = False

HERE = Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent
DIVISIONS_FILE = PLUGIN_DIR / "resources" / "masterformat-divisions.json"

# ----------------------------------------------------------------- constants

# Sheet number: whole-token match, e.g. "A-101", "M2.01A", "FP101".
SHEET_NO_STRICT = re.compile(r"^(?:[A-Z]{1,3}[-.]?\d{1,3}(\.\d{1,2})?[A-Z]?|0\d{2})$")
# Same shape, unanchored, for scanning a token out of free-flowing line text
# (bounded by whitespace so it only ever matches a whole "word").
_SHEET_CORE = r"[A-Z]{1,3}[-.]?\d{1,3}(?:\.\d{1,2})?[A-Z]?"
BARE_SHEET_RE = re.compile(r"(?<!\S)(" + _SHEET_CORE + r")(?!\S)")

# Detail/section callout bubble: "5/A-501", "5 / A-501.10", etc.
CALLOUT_RE = re.compile(r"(\d{1,2})\s*/\s*([A-Z]{1,3}-?\d{2,3}(\.\d{1,2})?)")

# 6-digit MasterFormat section, loosely spaced: "09 91 23", "099123".
SPEC_RE = re.compile(r"\b(\d{2})\s?(\d{2})\s?(\d{2})\b")

# Declared scale in a title block: "1/4\" = 1'-0\"", "1\" = 20'", "1:100".
SCALE_RE = re.compile(r"(\d+/\d+\"\s*=\s*1'-?0?\"|1\"\s*=\s*\d+'|\d+:\d+)")

# Title-block lines that are metadata, never the sheet title.
NOT_A_TITLE = re.compile(r"\bSCALE\b|\bDATE\b|\bDRAWN\b|\bCHECKED\b|\bPROJECT\s+(NO|#)|"
                         + SCALE_RE.pattern, re.I)

# A first page counts as the cover only when its own text says so.
COVER_RE = re.compile(r"\bCOVER\s+SHEET\b|\bDRAWING\s+INDEX\b|\bSHEET\s+INDEX\b")
PHASE_RE = re.compile(r"\bPHASE\s+(\d{1,2}[A-Z]?|[A-D])\b")
ROOM_RE = re.compile(r"\b(RM|ROOM)\s*[-#]?\s*(\d{3,4}[A-Z]?)\b")
AREA_RE = re.compile(r"\bAREA\s+([A-H])\b")
# Title-block lines that are never a sheet title (stamps, addresses, key plans).
TITLE_NOISE = re.compile(r"AUTODESK|DOCS://|ISSUE\s+FOR|KEY\s*PLAN|\bNORTH\b|\bSTREET\b|\bST\.|"
                         r"\bDRIVE\b|\bTX\b|\b\d{5}\b|\bREVISION|\bARCHITECT|\bENGINEER|\bSEAL\b|COPYRIGHT|INTERIM|NOT\s+TO\s+BE\s+USED|INCOMPLETE|REGULATORY|PERMIT", re.I)

# Discipline -> likely MasterFormat divisions (low-confidence heuristic; see
# divisions_with_confidence()). Order-sensitive lookup handles 2-letter
# disciplines (FP) before falling back to 1-letter ones.
DISC_TO_DIV = {
    "G": ["01"], "C": ["31", "32"], "L": ["32"], "A": ["06", "08", "09"],
    "S": ["03", "05"], "M": ["23"], "E": ["26", "27", "28"], "P": ["22"],
    "FP": ["21"], "T": ["27"], "Q": ["11"],
}

TITLE_BLOCK_X = 0.86   # right-edge strip
TITLE_BLOCK_Y = 0.90   # bottom strip
try:
    import atlas_ocr
except ImportError:   # OCR fallback is optional
    atlas_ocr = None

MIN_SEARCHABLE_WORDS = 25
LONG_EDGE_PX = 2000
THUMB_EDGE_PX = 320


def log(msg):
    sys.stderr.write(msg + "\n")


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:  # noqa: BLE001 — best-effort, missing/broken files are just absent
        return None


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ------------------------------------------------------------- pure helpers

def normalize_tag(text):
    """Punctuation-insensitive normalization for tags/matching: uppercase,
    strip everything that is not a letter or digit. 'FD-2' -> 'FD2'."""
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def natural_key(text):
    """Natural sort key: 'A-9' before 'A-10'."""
    return [int(chunk) if chunk.isdigit() else chunk.lower()
            for chunk in re.split(r"(\d+)", text or "")]


def discipline_of(sheet_no):
    """Leading letters of a sheet number, checked 3/2/1 chars against the
    known discipline table so 'FP' is preferred over a stray 'F'."""
    m = re.match(r"^[A-Za-z]+", sheet_no or "")
    leading = m.group(0).upper() if m else ""
    for length in (3, 2, 1):
        cand = leading[:length]
        if cand and cand in DISC_TO_DIV:
            return cand
    return leading


def divisions_with_confidence(discipline, model_divisions):
    """Discipline -> division table lookup, marked low-confidence (0.5) per
    spec. When an assembled --model is given and it actually shows scope in
    one of the guessed divisions, that overlap is kept and bumped to 0.7
    ('intersect'); with no overlap the full guess is kept as-is ('extend')."""
    base = DISC_TO_DIV.get(discipline, [])
    if not base:
        return [], 0.5
    if model_divisions:
        overlap = [d for d in base if d in model_divisions]
        if overlap:
            return overlap, 0.7
    return base, 0.5


def sanitize_filename(text):
    return re.sub(r"[^A-Za-z0-9._-]", "_", text or "sheet")


def posix_rel(path, base):
    try:
        return Path(path).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def is_title_block(box):
    """box is a normalized [x0,y0,x1,y1]. A word counts as 'in the title
    block' if it sits in the right-edge strip or the bottom strip."""
    x0, y0, _, _ = box
    return x0 > TITLE_BLOCK_X or y0 > TITLE_BLOCK_Y


def humanize_stem(stem):
    words = re.split(r"[\s_\-]+", stem)
    return " ".join(w.capitalize() if not w.isupper() else w for w in words if w).strip()


# ---------------------------------------------------------- manifest-only mode

def sheet_from_filename(pdf_path, used_ids):
    """No PyMuPDF: build one sheet per file from its filename. Never crashes;
    this is the graceful-degradation path."""
    stem = pdf_path.stem
    tokens = re.split(r"[\s_]+", stem)
    sheet_no = None
    for tok in tokens:
        if SHEET_NO_STRICT.match(tok.upper()):
            sheet_no = tok.upper()
            break
    if not sheet_no:
        sheet_no = stem.upper()[:16]
    sheet_id = dedupe_id(sheet_no, used_ids)
    discipline = discipline_of(sheet_no)
    divisions, div_conf = divisions_with_confidence(discipline, set())
    return {
        "sheet_id": sheet_id,
        "sheet_no": sheet_no,
        "title": humanize_stem(stem),
        "discipline": discipline,
        "divisions": divisions,
        "source_doc": pdf_path.name,
        "page": 1,
        "searchable": False,
        "phases": [],
        "areas": [],
        "_div_conf": div_conf,
        "_id_conf": 0.3,
    }


def dedupe_id(candidate, used_ids):
    if candidate not in used_ids:
        used_ids.add(candidate)
        return candidate
    n = 2
    while f"{candidate}({n})" in used_ids:
        n += 1
    new_id = f"{candidate}({n})"
    used_ids.add(new_id)
    return new_id


# --------------------------------------------------------- fitz page parsing

def extract_page_structure(page):
    """Returns (lines, words_flat). Both are built from the span layer of
    page.get_text('dict'): each span's text is split on whitespace into
    words, and the span's bbox is divided proportionally by character count
    to give each word an approximate (but deterministic) box. 'lines' groups
    words by their original line so callout/spec regexes can scan real
    reading-order text; 'words_flat' is the full per-page word list used for
    the search sidecar and the searchable-word-count check."""
    raw = page.get_text("dict")
    rot_m = page.rotation_matrix if page.rotation else None
    lines = []
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            line_words = []
            for span in line.get("spans", []):
                text = span.get("text", "")
                size = span.get("size", 0.0)
                bx0, by0, bx1, by1 = span.get("bbox", (0, 0, 0, 0))
                tokens = text.split()
                if not tokens:
                    continue
                # Split along the text direction in the span's own (unrotated)
                # space, then rotate each token box into the displayed page.
                dx, dy = line.get("dir", (1.0, 0.0))
                vertical = abs(dy) > abs(dx)
                lo, hi = (by0, by1) if vertical else (bx0, bx1)
                reverse = (dy < 0) if vertical else (dx < 0)
                extent = hi - lo
                total_chars = sum(len(t) for t in tokens) or 1
                pos = hi if reverse else lo
                for tok in tokens:
                    step = extent * len(tok) / total_chars
                    a0, a1 = (pos - step, pos) if reverse else (pos, pos + step)
                    pos = a0 if reverse else a1
                    box = (bx0, a0, bx1, a1) if vertical else (a0, by0, a1, by1)
                    if rot_m is not None:
                        box = tuple(fitz.Rect(*box) * rot_m)
                    line_words.append({"bbox": box, "text": tok, "size": size})
            if line_words:
                lines.append(line_words)
    words_flat = [w for line in lines for w in line]
    return lines, words_flat


def norm_box(bbox, pw, ph):
    x0, y0, x1, y1 = bbox
    clamp = lambda v: round(max(0.0, min(1.0, v)), 4)  # noqa: E731
    return [clamp(x0 / pw), clamp(y0 / ph), clamp(x1 / pw), clamp(y1 / ph)]


def detect_sheet_and_title(lines, pw, ph):
    """Heuristic title-block scan: candidate sheet numbers are title-block
    tokens matching SHEET_NO_STRICT; the largest-font one wins (ties broken
    topmost-then-leftmost for determinism). Title = the longest title-block
    line that is not the sheet number's own line."""
    candidates = []
    for li, line in enumerate(lines):
        for w in line:
            nb = norm_box(w["bbox"], pw, ph)
            if is_title_block(nb) and SHEET_NO_STRICT.match(w["text"].upper()):
                candidates.append((w["size"], nb[1], nb[0], w["text"].upper(), li))
    if not candidates:
        return None, ""
    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))
    # A real title-block sheet number is set far larger than body text; a
    # same-size token (e.g. in a drawing index or notes) is not the number.
    sizes = sorted(w["size"] for line in lines for w in line)
    median = sizes[len(sizes) // 2] if sizes else 0
    if median and candidates[0][0] < 1.6 * median:
        return None, ""
    sheet_no = candidates[0][3]
    sheet_line_idx = candidates[0][4]

    # Real title blocks put the sheet title in the lowest-right corner in the
    # second-largest type (the number is the largest). Collect those lines first,
    # join wrapped lines top-to-bottom, and fall back to the longest-line rule.
    cands = []
    for li, line in enumerate(lines):
        if li == sheet_line_idx:
            continue
        text = " ".join(w["text"] for w in line).strip()
        if not text or text.upper() == sheet_no or NOT_A_TITLE.search(text) or TITLE_NOISE.search(text):
            continue
        boxes = [norm_box(w["bbox"], pw, ph) for w in line]
        if min(b[0] for b in boxes) < 0.80 or min(b[1] for b in boxes) < 0.86:
            continue
        if sum(c.isalpha() for c in text) < 3:
            continue
        cands.append((max(w["size"] for w in line), boxes[0][1], boxes[0][0], text))
    best_title = ""
    if cands:
        top = max(c[0] for c in cands)
        keep = sorted((c for c in cands if c[0] >= 0.85 * top), key=lambda c: (round(c[1], 3), c[2]))
        best_title = " ".join(c[3] for c in keep)[:90].strip()
    if not best_title:
        for li, line in enumerate(lines):
            if li == sheet_line_idx:
                continue
            if not any(is_title_block(norm_box(w["bbox"], pw, ph)) for w in line):
                continue
            text = " ".join(w["text"] for w in line).strip()
            if NOT_A_TITLE.search(text) or TITLE_NOISE.search(text):
                continue
            if text and text.upper() != sheet_no and len(text) > len(best_title):
                best_title = text
    return sheet_no, best_title


def detect_scale(lines, pw, ph):
    texts = [" ".join(w["text"] for w in line) for line in lines
             if any(is_title_block(norm_box(w["bbox"], pw, ph)) for w in line)]
    m = SCALE_RE.search(" | ".join(texts))
    return m.group(0) if m else None


def scan_phases_areas(words_flat):
    full_text = " ".join(w["text"] for w in words_flat).upper()
    phases = sorted({m.group(1) for m in PHASE_RE.finditer(full_text)})
    areas = sorted({m.group(2) for m in ROOM_RE.finditer(full_text)}
                   | {"Area " + m.group(1) for m in AREA_RE.finditer(full_text)})
    return phases, areas


def render_page_images(page, sheet_id, img_dir, dpi):
    """Full page fit within LONG_EDGE_PX on its long edge, plus a THUMB_EDGE_PX
    thumbnail. Never upscales past the requested --dpi."""
    long_edge_pt = max(page.rect.width, page.rect.height) or 1.0
    dpi_cap = LONG_EDGE_PX * 72.0 / long_edge_pt
    eff_dpi = min(float(dpi), dpi_cap)
    zoom = eff_dpi / 72.0
    safe = sanitize_filename(sheet_id)

    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img_path = img_dir / f"{safe}.jpg"
    pix.save(str(img_path), jpg_quality=72)

    thumb_dpi = min(eff_dpi, THUMB_EDGE_PX * 72.0 / long_edge_pt)
    tpix = page.get_pixmap(matrix=fitz.Matrix(thumb_dpi / 72.0, thumb_dpi / 72.0))
    thumb_path = img_dir / f"{safe}.thumb.jpg"
    tpix.save(str(thumb_path))
    return img_path, thumb_path


def build_sheets_from_pdfs(pdf_paths, out_dir, render_images, dpi, model_divisions):
    """Pass 1: open every PDF, extract every page's sheet record, words, and
    (optionally) images. Returns (sheets, lines_by_sheet, words_store, review).
    lines_by_sheet holds the raw fitz-space line structures needed by the
    link pass (pass 2), keyed by sheet_id; it is never written to disk."""
    sheets = []
    lines_by_sheet = {}
    words_store = {}
    review = []
    used_ids = set()
    img_dir = out_dir / "atlas" / "img"
    if render_images:
        img_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdf_paths:
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:  # noqa: BLE001
            review.append(f"could not open {pdf_path.name}: {e}")
            continue
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            pw, ph = page.rect.width, page.rect.height
            lines, words_flat = extract_page_structure(page)
            ocr_used = ""
            if len(words_flat) < MIN_SEARCHABLE_WORDS and atlas_ocr is not None:
                ocr_lines, ocr_used = atlas_ocr.ocr_page_lines(page)
                if ocr_lines:
                    lines = ocr_lines
                    words_flat = [w for ln in ocr_lines for w in ln]
                    review.append(f"page {page_index + 1} of {pdf_path.name} had no text layer; "
                                  f"read with OCR ({ocr_used}) - verify sheet number and title")
                else:
                    ocr_used = ""
            sheet_no, title = detect_sheet_and_title(lines, pw, ph)
            page_no = page_index + 1
            if sheet_no:
                sheet_id = dedupe_id(sheet_no, used_ids)
                if sheet_id != sheet_no:
                    review.append(
                        f"duplicate sheet number '{sheet_no}' in {pdf_path.name} "
                        f"p{page_no} — disambiguated as '{sheet_id}'")
                id_conf = 0.95
            elif (page_no == 1 and not ocr_used
                  and COVER_RE.search(" ".join(w["text"] for w in words_flat).upper())):
                sheet_no, title = "COVER", "Cover Sheet"
                sheet_id = dedupe_id("COVER", used_ids)
                id_conf = 0.6
                review.append(f"page 1 of {pdf_path.name} has no sheet number; labelled 'COVER' from the word "
                              f"on the page - verify")
            else:
                sheet_id = dedupe_id(f"{pdf_path.stem}-p{page_no}", used_ids)
                id_conf = 0.4
                review.append(
                    f"sheet number not detected on page {page_no} of "
                    f"{pdf_path.name}; used fallback id '{sheet_id}'")

            discipline = discipline_of(sheet_no or sheet_id)
            divisions, div_conf = divisions_with_confidence(discipline, model_divisions)
            phases, areas = scan_phases_areas(words_flat)
            searchable = len(words_flat) >= MIN_SEARCHABLE_WORDS

            sheet = {
                "sheet_id": sheet_id,
                "sheet_no": sheet_no or sheet_id,
                "title": title,
                "discipline": discipline,
                "divisions": divisions,
                "source_doc": pdf_path.name,
                "page": page_no,
                "width_in": round(pw / 72.0, 2),
                "height_in": round(ph / 72.0, 2),
                "declared_scale": detect_scale(lines, pw, ph) or "",
                "searchable": searchable,
                "ocr": ocr_used or False,
                "phases": phases,
                "areas": areas,
                "_div_conf": div_conf,
                "_id_conf": id_conf,
            }

            if render_images:
                try:
                    img_path, thumb_path = render_page_images(page, sheet_id, img_dir, dpi)
                    sheet["image"] = posix_rel(img_path, out_dir)
                    sheet["thumbnail"] = posix_rel(thumb_path, out_dir)
                except Exception as e:  # noqa: BLE001
                    review.append(f"image render failed for {sheet_id}: {e}")

            sheets.append(sheet)
            lines_by_sheet[sheet_id] = (lines, pw, ph)
            words_store[sheet_id] = [
                [*norm_box(w["bbox"], pw, ph), w["text"]] for w in words_flat
            ]
        log(f"extracted {doc.page_count} page(s) from {pdf_path.name}")
        doc.close()
    return sheets, lines_by_sheet, words_store, review


# --------------------------------------------------------------- link pass

def line_text_and_offsets(line):
    parts, offsets, cur = [], [], 0
    for i, w in enumerate(line):
        t = w["text"]
        offsets.append((cur, cur + len(t), i))
        parts.append(t)
        cur += len(t) + 1
    return " ".join(parts), offsets


def words_for_span(offsets, start, end):
    return [i for (s, e, i) in offsets if e > start and s < end]


def union_box(line, indices, pw, ph):
    xs0 = min(line[i]["bbox"][0] for i in indices)
    ys0 = min(line[i]["bbox"][1] for i in indices)
    xs1 = max(line[i]["bbox"][2] for i in indices)
    ys1 = max(line[i]["bbox"][3] for i in indices)
    return norm_box((xs0, ys0, xs1, ys1), pw, ph)


def make_link(kind, sheet, tag, box, confidence, to_sheet=None, to_spec_section=None):
    link = {
        "kind": kind,
        "from_sheet": sheet["sheet_id"],
        "from_box": box,
        "tag": tag,
        "confidence": confidence,
        "provenance": {
            "source_doc": sheet["source_doc"],
            "page": sheet["page"],
            "confidence": confidence,
            "extracted_verbatim": tag,
        },
    }
    if to_sheet:
        link["to_sheet"] = to_sheet
    if to_spec_section:
        link["to_spec_section"] = to_spec_section
    return link


def extract_links_for_sheet(sheet, lines, pw, ph, sheet_norm_map, valid_divisions):
    """Deterministic, regex-only. A link is emitted ONLY when its target
    resolves (a real sheet in the set, or a plausible MasterFormat section);
    everything else is skipped and counted as unresolved — never guessed."""
    links = []
    unresolved = 0
    own_norm = normalize_tag(sheet["sheet_no"])

    for line in lines:
        text, offsets = line_text_and_offsets(line)
        consumed = []

        for m in CALLOUT_RE.finditer(text):
            consumed.append(m.span())
            raw_tag, sheet_ref = m.group(0), m.group(2)
            norm_ref = normalize_tag(sheet_ref)
            target = sheet_norm_map.get(norm_ref)
            if target and target != sheet["sheet_id"]:
                idxs = words_for_span(offsets, *m.span())
                box = union_box(line, idxs, pw, ph)
                links.append(make_link("detail", sheet, raw_tag, box, 0.9, to_sheet=target))
            else:
                unresolved += 1

        for m in SPEC_RE.finditer(text):
            if any(s < m.end() and m.start() < e for s, e in consumed):
                continue
            division = m.group(1)
            if division not in valid_divisions:
                continue  # not a plausible spec tag — ordinary number, not counted
            consumed.append(m.span())
            idxs = words_for_span(offsets, *m.span())
            box = union_box(line, idxs, pw, ph)
            section = f"{m.group(1)} {m.group(2)} {m.group(3)}"
            links.append(make_link("spec", sheet, section, box, 0.7, to_spec_section=section))

        for m in BARE_SHEET_RE.finditer(text):
            if any(s < m.end() and m.start() < e for s, e in consumed):
                continue
            tag = m.group(0)
            norm_tag = normalize_tag(tag)
            if norm_tag == own_norm:
                continue  # the sheet restating its own number — not a link
            target = sheet_norm_map.get(norm_tag)
            if target and target != sheet["sheet_id"]:
                idxs = words_for_span(offsets, *m.span())
                box = union_box(line, idxs, pw, ph)
                links.append(make_link("sheet", sheet, tag, box, 0.9, to_sheet=target))
            else:
                unresolved += 1
    return links, unresolved


# -------------------------------------------------------- --model cross-link

def load_model_crosslinks(model_dir):
    """Reads canonical-model.json + sections/*.json (embedded or standalone —
    assemble_model.py supports both) to gather: divisions actually in scope,
    a trade_href per division from quick_links, takeoff_ids per division from
    quantity_takeoff, and known spec sections from requirements/scope."""
    result = {
        "model_divisions": set(),
        "trade_href_by_division": {},
        "takeoff_ids_by_division": {},
        "spec_from_model": {},
    }
    if not model_dir:
        return result
    model_dir = Path(model_dir)
    model_json = load_json(model_dir / "canonical-model.json") or {}
    embedded = model_json.get("sections", {}) if isinstance(model_json, dict) else {}

    def section(key):
        data = load_json(model_dir / "sections" / f"{key}.json")
        if isinstance(data, dict):
            return data
        val = embedded.get(key) if isinstance(embedded, dict) else None
        return val if isinstance(val, dict) else {}

    def note_division(div):
        if isinstance(div, str) and re.match(r"^\d{2}$", div):
            result["model_divisions"].add(div)

    def note_spec(csi):
        if not isinstance(csi, dict):
            return
        sec = csi.get("masterformat_section")
        div = csi.get("masterformat_division")
        if sec:
            result["spec_from_model"].setdefault(
                sec, {"title": csi.get("section_title", ""), "division": div or sec[:2]})

    scope = section("scope")
    for item in scope.get("items", []) if isinstance(scope, dict) else []:
        csi = item.get("csi") if isinstance(item, dict) else None
        if isinstance(csi, dict):
            note_division(csi.get("masterformat_division"))
            note_spec(csi)

    trades = section("trades")
    for t in trades.get("trades", []) if isinstance(trades, dict) else []:
        if isinstance(t, dict):
            for d in t.get("csi_divisions", []) or []:
                note_division(d)

    requirements = section("requirements")
    for r in requirements.get("requirements", []) if isinstance(requirements, dict) else []:
        csi = r.get("csi") if isinstance(r, dict) else None
        if isinstance(csi, dict):
            note_division(csi.get("masterformat_division"))
            note_spec(csi)

    qto = section("quantity_takeoff")
    for item in qto.get("items", []) if isinstance(qto, dict) else []:
        csi = item.get("csi") if isinstance(item, dict) else None
        div = csi.get("masterformat_division") if isinstance(csi, dict) else None
        if div and item.get("takeoff_id"):
            result["takeoff_ids_by_division"].setdefault(div, []).append(item["takeoff_id"])

    quick_links = section("quick_links")
    for link in quick_links.get("links", []) if isinstance(quick_links, dict) else []:
        if isinstance(link, dict) and link.get("category") == "trade":
            div = link.get("masterformat_division")
            href = link.get("pdf_url") or link.get("screenshot_url")
            if div and href:
                result["trade_href_by_division"].setdefault(div, href)

    return result


def guess_spec_pdf(section_no, division, bases):
    for base in bases:
        if not base:
            continue
        # The section number must end where the match ends: "03 30 00" must not pick up "03 30 00.13 ...".
        matches = sorted(p for p in Path(base).glob(f"Specs By CSI/{division}/{glob.escape(section_no)}*.pdf")
                         if not re.match(r"[\d.]", p.name[len(section_no):len(section_no) + 1] or " "))
        if matches:
            return posix_rel(matches[0], base)
    return None


# --------------------------------------------------------------- concepts

def build_concepts(sheets, links, model, divisions_resource, out_dir, model_dir):
    labels = {d["division"]: d["title"] for d in divisions_resource.get("divisions", [])}
    order = [d["division"] for d in divisions_resource.get("divisions", [])]

    spec_links_by_division = {}
    spec_sheet_ids_by_section = {}
    for link in links:
        if link["kind"] == "spec":
            section = link["to_spec_section"]
            division = section[:2]
            spec_links_by_division.setdefault(division, set()).add(section)
            spec_sheet_ids_by_section.setdefault(section, set()).add(link["from_sheet"])

    trades = []
    for division in order:
        sheet_ids = sorted(
            {s["sheet_id"] for s in sheets if division in s.get("divisions", [])},
            key=natural_key)
        spec_sections = sorted(spec_links_by_division.get(division, set())
                                | {sec for sec, meta in model["spec_from_model"].items()
                                   if meta.get("division") == division})
        takeoff_ids = model["takeoff_ids_by_division"].get(division, [])
        if not (sheet_ids or spec_sections or takeoff_ids):
            continue
        entry = {
            "division": division,
            "label": labels.get(division, ""),
            "sheet_ids": sheet_ids,
            "spec_sections": spec_sections,
            "takeoff_ids": takeoff_ids,
        }
        href = model["trade_href_by_division"].get(division)
        if href:
            entry["trade_href"] = href
        trades.append(entry)

    all_sections = set(spec_sheet_ids_by_section) | set(model["spec_from_model"])
    bases = [model_dir, out_dir]
    specs = []
    for section in sorted(all_sections):
        division = section[:2]
        meta = model["spec_from_model"].get(section, {})
        entry = {
            "section": section,
            "title": meta.get("title", ""),
            "division": division,
            "sheet_ids": sorted(spec_sheet_ids_by_section.get(section, set())),
        }
        pdf = guess_spec_pdf(section, division, bases)
        if pdf:
            entry["pdf"] = pdf
        specs.append(entry)

    phase_sheets, area_sheets = {}, {}
    phase_divs, area_divs = {}, {}
    for s in sheets:
        for ph in s.get("phases", []):
            phase_sheets.setdefault(ph, set()).add(s["sheet_id"])
            phase_divs.setdefault(ph, set()).update(s.get("divisions", []))
        for ar in s.get("areas", []):
            area_sheets.setdefault(ar, set()).add(s["sheet_id"])
            area_divs.setdefault(ar, set()).update(s.get("divisions", []))

    phases = [{"phase": ph, "sheet_ids": sorted(ids, key=natural_key),
               "divisions": sorted(phase_divs.get(ph, set()))}
              for ph, ids in sorted(phase_sheets.items())]
    areas = [{"area": ar, "sheet_ids": sorted(ids, key=natural_key),
              "divisions": sorted(area_divs.get(ar, set()))}
             for ar, ids in sorted(area_sheets.items())]

    return {"trades": trades, "specs": specs, "phases": phases, "areas": areas}


# ------------------------------------------------------------------- build

def build(args):
    out_dir = Path(args.out)
    model_dir = Path(args.model) if args.model else None
    divisions_resource = load_json(DIVISIONS_FILE) or {"divisions": []}

    seen, pdf_paths = set(), []
    for raw in args.pdf:
        p = Path(raw)
        key = p.resolve() if p.exists() else p
        if key not in seen:
            seen.add(key)
            pdf_paths.append(p)
    if args.dir:
        for p in sorted(Path(args.dir).glob("*.pdf")):
            key = p.resolve()
            if key not in seen:
                seen.add(key)
                pdf_paths.append(p)

    render_images = args.render_images and FITZ_AVAILABLE

    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "pdfs": [str(p) for p in pdf_paths],
            "out_dir": str(out_dir),
            "model_dir": str(model_dir) if model_dir else None,
            "fitz_available": FITZ_AVAILABLE,
            "render_images": render_images,
            "dpi": args.dpi,
            "outputs": ["sections/plans_atlas.json", "atlas-words.json", "atlas/img/*.jpg"],
        }, indent=2))
        return

    model = load_model_crosslinks(model_dir)
    needs_review = []

    if not FITZ_AVAILABLE:
        needs_review.append(
            "PyMuPDF (fitz) not installed — degraded to manifest-only mode: sheets were "
            "built from filenames/CLI hints only; searchable=false and no text, links, "
            "or images were extracted. Install pymupdf to enable full extraction.")
        used_ids = set()
        sheets = [sheet_from_filename(p, used_ids) for p in pdf_paths]
        lines_by_sheet, words_store = {}, {}
    else:
        sheets, lines_by_sheet, words_store, review = build_sheets_from_pdfs(
            pdf_paths, out_dir, render_images, args.dpi, model["model_divisions"])
        needs_review.extend(review)

    valid_divisions = {d["division"] for d in divisions_resource.get("divisions", [])}
    sheet_norm_map = {normalize_tag(s["sheet_no"]): s["sheet_id"] for s in sheets}
    sheet_norm_map.update({normalize_tag(s["sheet_id"]): s["sheet_id"] for s in sheets})

    all_links = []
    unresolved_total = 0
    for sheet in sheets:
        entry = lines_by_sheet.get(sheet["sheet_id"])
        if not entry:
            continue
        lines, pw, ph = entry
        links, unresolved = extract_links_for_sheet(
            sheet, lines, pw, ph, sheet_norm_map, valid_divisions)
        all_links.extend(links)
        unresolved_total += unresolved
    for i, link in enumerate(all_links, start=1):
        link["link_id"] = f"LNK-{i:04d}"
    if unresolved_total:
        needs_review.append(f"{unresolved_total} callout tags did not resolve")

    # finalize each sheet: csi block, provenance, drop scratch fields
    for s in sheets:
        divisions = s.get("divisions", [])
        primary = divisions[0] if divisions else "01"
        s["csi"] = {"masterformat_division": primary,
                    "division_title": labels_lookup(divisions_resource, primary)}
        s["provenance"] = {
            "source_doc": s["source_doc"],
            "page": s["page"],
            "confidence": round(min(s.pop("_id_conf"), s.pop("_div_conf")), 2),
            "extracted_verbatim": s["sheet_no"],
        }

    sheets.sort(key=lambda s: (s["csi"]["masterformat_division"], natural_key(s["sheet_no"])))

    concepts = build_concepts(sheets, all_links, model, divisions_resource, out_dir, model_dir)

    not_searchable = sorted((s["sheet_id"] for s in sheets if not s["searchable"]),
                             key=natural_key)
    atlas = {
        "section": "plans_atlas",  # discriminator assemble_model.py's validator expects
        "generated_at": args.generated_at or "",
        "source_set": {
            "documents": sorted(p.name for p in pdf_paths),
            "pack_qa": "not_run",
        },
        "sheets": sheets,
        "links": all_links,
        "concepts": concepts,
        "search": {
            "words_file": "atlas-words.json",
            "sheets_indexed": len(sheets) - len(not_searchable),
            "sheets_not_searchable": not_searchable,
        },
        "needs_review": needs_review,
    }

    write_json(out_dir / "sections" / "plans_atlas.json", atlas)
    write_json(out_dir / "atlas-words.json", words_store)
    log(f"wrote plans atlas: {out_dir / 'sections' / 'plans_atlas.json'} "
        f"({len(sheets)} sheet(s), {len(all_links)} link(s))")
    print(json.dumps({
        "sheets": len(sheets), "links": len(all_links),
        "searchable": len(sheets) - len(not_searchable),
        "needs_review": len(needs_review),
        "out": str(out_dir / "sections" / "plans_atlas.json"),
    }, indent=2))


def labels_lookup(divisions_resource, division):
    for d in divisions_resource.get("divisions", []):
        if d["division"] == division:
            return d["title"]
    return ""


def main():
    ap = argparse.ArgumentParser(
        description="Deterministic Plans Atlas extraction — builds sections/plans_atlas.json "
                     "(+ atlas-words.json sidecar, atlas/img/ page images) from a PDF drawing "
                     "set. Replayable; never hand-rolled per run.")
    ap.add_argument("--pdf", action="append", default=[],
                     help="A drawing-set PDF (repeatable).")
    ap.add_argument("--dir", help="Directory to glob *.pdf from (sorted).")
    ap.add_argument("--out", required=True, help="Project model directory to write into.")
    ap.add_argument("--model", help="Assembled canonical model dir to cross-link against "
                                     "(canonical-model.json + sections/*.json).")
    ap.add_argument("--render-images", action=argparse.BooleanOptionalAction,
                     default=FITZ_AVAILABLE,
                     help="Render page + thumbnail PNGs (requires PyMuPDF; default on when "
                          "PyMuPDF is available).")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--generated-at", default="", help="ISO timestamp to stamp (caller supplies).")
    ap.add_argument("--dry-run", action="store_true",
                     help="Print the plan (PDFs found, outputs, fitz availability) and exit.")
    build(ap.parse_args())


if __name__ == "__main__":
    main()
