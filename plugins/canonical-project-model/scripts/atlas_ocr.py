#!/usr/bin/env python3
"""OCR fallback for drawing sheets that have no text layer (scans, flattened PDFs).

build_atlas_data.py calls ocr_page_lines(page) only when a page yields fewer
than MIN_SEARCHABLE_WORDS words from its text layer. Output matches the shape
extract_page_structure() returns, in the page's rotated (displayed) coordinate
space, so title-block detection, callout links, and the word index work on
scanned sets exactly as they do on vector ones.

Providers (NTXP_OCR = auto | rapidocr | mistral | none; default auto):
  rapidocr  offline, free, word-level boxes. pip install rapidocr-onnxruntime.
            Large sheets are OCR'd in overlapping tiles at NTXP_OCR_DPI (150)
            because a single 42 x 30 in image is downscaled past legibility.
  mistral   Mistral OCR API (needs MISTRAL_API_KEY). It returns text without
            word boxes, so it is used only on the title-block strips to recover
            the sheet number and title; such sheets stay marked not searchable.
Nothing here ever blocks a build: any failure returns None and the sheet is
indexed as 'not searchable', as before.
"""
import base64
import json
import os
import sys
import urllib.request

try:
    import pymupdf as fitz
except ImportError:  # older PyMuPDF
    import fitz

TILE_PX = 1800
OVERLAP_PX = 120
_ENGINE = {}


def log(msg):
    sys.stderr.write(f"[atlas-ocr] {msg}\n")


def _rapid_engine():
    if "rapid" not in _ENGINE:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ENGINE["rapid"] = RapidOCR()
        except Exception as e:  # noqa: BLE001
            log(f"rapidocr unavailable ({e.__class__.__name__}); pip install rapidocr-onnxruntime")
            _ENGINE["rapid"] = None
    return _ENGINE["rapid"]


def _png_bytes(page, clip, zoom):
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
    return pix.tobytes("png"), pix.width, pix.height


def _tiles(rect, zoom):
    step_pt = (TILE_PX - OVERLAP_PX) / zoom
    size_pt = TILE_PX / zoom
    y = rect.y0
    while y < rect.y1:
        x = rect.x0
        while x < rect.x1:
            yield fitz.Rect(x, y, min(x + size_pt, rect.x1), min(y + size_pt, rect.y1))
            x += step_pt
        y += step_pt


def _split_words(text, x0, y0, x1, y1, size):
    toks = text.split()
    if not toks:
        return []
    total = sum(len(t) for t in toks) or 1
    cur, out = x0, []
    for t in toks:
        w = (x1 - x0) * len(t) / total
        out.append({"bbox": (cur, y0, cur + w, y1), "text": t, "size": size})
        cur += w
    return out


def _rapid_lines(page, dpi):
    engine = _rapid_engine()
    if engine is None:
        return None
    import numpy as np
    from PIL import Image
    import io

    zoom = max(0.5, dpi / 72.0)
    lines, seen = [], set()
    for clip in _tiles(page.rect, zoom):
        data, _, _ = _png_bytes(page, clip, zoom)
        arr = np.array(Image.open(io.BytesIO(data)).convert("RGB"))
        result, _ = engine(arr)
        for box, text, conf in (result or []):
            if float(conf) < 0.5 or not str(text).strip():
                continue
            xs, ys = [p[0] for p in box], [p[1] for p in box]
            x0, x1 = clip.x0 + min(xs) / zoom, clip.x0 + max(xs) / zoom
            y0, y1 = clip.y0 + min(ys) / zoom, clip.y0 + max(ys) / zoom
            key = (str(text).strip().upper(), round(x0 / 6), round(y0 / 6))   # overlap de-dup
            if key in seen:
                continue
            seen.add(key)
            size = max(4.0, (y1 - y0) / 0.72)            # em height from line-box height
            lines.append(_split_words(str(text).strip(), x0, y0, x1, y1, size))
    lines = [l for l in lines if l]
    lines.sort(key=lambda l: (round(l[0]["bbox"][1] / 8), l[0]["bbox"][0]))
    return lines or None


def _mistral_titleblock_lines(page):
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        return None
    W, H = page.rect.width, page.rect.height
    strips = [fitz.Rect(W * 0.80, 0, W, H), fitz.Rect(0, H * 0.86, W, H)]
    lines = []
    for clip in strips:
        zoom = min(150 / 72.0, 3800 / max(clip.width, clip.height))
        data, _, _ = _png_bytes(page, clip, zoom)
        body = json.dumps({"model": os.environ.get("MISTRAL_OCR_MODEL", "mistral-ocr-latest"),
                           "document": {"type": "image_url",
                                        "image_url": "data:image/png;base64," + base64.b64encode(data).decode()}}).encode()
        req = urllib.request.Request("https://api.mistral.ai/v1/ocr", data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                pages = json.load(r).get("pages", [])
        except Exception as e:  # noqa: BLE001
            log(f"mistral ocr failed ({e.__class__.__name__})")
            return None
        # No boxes: stack recognised lines top-to-bottom inside the strip at a
        # large nominal size so the sheet number outranks body text.
        txt = [t.strip() for p in pages for t in (p.get("markdown") or "").splitlines() if t.strip()]
        for i, t in enumerate(txt):
            t = t.lstrip("#*- ").strip()
            if not t:
                continue
            y0 = clip.y0 + (clip.height * 0.98) * i / max(len(txt), 1)
            size = 53.0 if i == 0 and clip.x0 > 0 else 25.0
            lines.append(_split_words(t, clip.x0 + clip.width * 0.05, y0, clip.x1 - 2, y0 + 20, size))
    return [l for l in lines if l] or None


def ocr_page_lines(page):
    """Returns (lines, provider) or (None, 'none'). lines = list of word-dict lists."""
    provider = os.environ.get("NTXP_OCR", "auto").lower()
    if provider == "none":
        return None, "none"
    dpi = float(os.environ.get("NTXP_OCR_DPI", "150"))
    if provider in ("auto", "rapidocr"):
        try:
            lines = _rapid_lines(page, dpi)
        except Exception as e:  # noqa: BLE001
            log(f"rapidocr failed on a page ({e.__class__.__name__}: {e})")
            lines = None
        if lines:
            return lines, "rapidocr"
    if provider in ("auto", "mistral"):
        lines = _mistral_titleblock_lines(page)
        if lines:
            return lines, "mistral-titleblock"
    return None, "none"
