#!/usr/bin/env python3
"""Shrink a drawing-set PDF without touching its navigation.

Downsamples and recompresses the embedded raster images (lossless ones too; that
is where most of a scanned drawing set's weight is) and rewrites the file with object
streams and garbage collection. Pages, text, bookmarks and every link (the
Plans Atlas callout links, the index pages, URLs) are left exactly as they
are; the script counts links and bookmarks before and after and fails if any
are lost.

    python compress_pdf.py --pdf in.pdf --out out.pdf [--dpi 150] [--quality 70]

Needs PyMuPDF. Vector linework is not touched, so the saving depends on how
much of the set is scanned or photographic.
"""
import argparse
import sys
from pathlib import Path


def counts(doc):
    return {"pages": len(doc), "links": sum(len(p.get_links()) for p in doc), "toc": len(doc.get_toc())}


def compress(src, dst, dpi=150, quality=70):
    import pymupdf
    doc = pymupdf.open(src)
    before = counts(doc)
    doc.rewrite_images(dpi_threshold=dpi + 20, dpi_target=dpi, quality=quality, lossy=True, lossless=True,
                       set_to_gray=False)
    doc.save(dst, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, use_objstms=1)
    doc.close()
    out = pymupdf.open(dst)
    after = counts(out)
    out.close()
    if after != before:
        Path(dst).unlink(missing_ok=True)
        sys.exit(f"compression changed structure, output removed: before {before}, after {after}")
    return before, Path(src).stat().st_size, Path(dst).stat().st_size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--quality", type=int, default=70)
    a = ap.parse_args()
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        sys.exit("PyMuPDF is required: pip install pymupdf")
    c, b, s = compress(a.pdf, a.out, a.dpi, a.quality)
    print(f"{c['pages']} pages, {c['links']} links, {c['toc']} bookmarks kept; "
          f"{b / 1e6:.1f} MB -> {s / 1e6:.1f} MB ({100 * (1 - s / b):.0f}% smaller)")


if __name__ == "__main__":
    main()
