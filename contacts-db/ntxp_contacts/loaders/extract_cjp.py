"""Extract embedded page images from the scanned CJP Holders PDF.

The PDF has no text layer — each page is a large raster image. This pulls those
images out to disk so they can be OCR'd (tesseract, a vision model, or a cloud
OCR service). The OCR step writes a JSONL of
`{full_name, company, city, state, cert_id, cert_date, confidence}` rows that
`cjp_pdf.CjpPdfLoader` then routes through the staging quarantine.
"""
from __future__ import annotations

from pathlib import Path


def extract_images(pdf_path: str | Path, out_dir: str | Path) -> list[str]:
    """Write each embedded image XObject to `out_dir`. Returns the file paths."""
    from pypdf import PdfReader

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(pdf_path))
    paths: list[str] = []
    idx = 0
    for pageno, page in enumerate(reader.pages):
        resources = page.get("/Resources")
        if not resources or "/XObject" not in resources:
            continue
        xobjects = resources["/XObject"].get_object()
        for name, ref in xobjects.items():
            obj = ref.get_object()
            if obj.get("/Subtype") != "/Image":
                continue
            data = obj.get_data()
            filt = obj.get("/Filter")
            ext = "jpg" if "DCTDecode" in str(filt) else (
                "jp2" if "JPXDecode" in str(filt) else "bin")
            fp = out / f"page{pageno:02d}_{idx:02d}.{ext}"
            fp.write_bytes(data)
            paths.append(str(fp))
            idx += 1
    return paths
