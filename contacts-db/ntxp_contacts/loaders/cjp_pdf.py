"""Certified JOC Professional (CJP) holders, sourced from a scanned PDF.

The PDF has no text layer, so extraction is a separate OCR/vision step
(`extract_cjp.py`) that writes a JSONL of `{full_name, company, ...,
confidence}` rows. This loader reads that JSONL and routes rows through the
staging quarantine — OCR output never auto-merges into canonical tables.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from .. import normalize as N
from ..model import CanonicalRecord, Tag
from .base import register

CONFIDENCE_FLOOR = 0.80  # below this -> always staged for review


class CjpPdfLoader:
    source = "cjp_pdf"

    def rows(self, path: str | Path) -> Iterator[dict]:
        """Read the OCR JSONL produced by extract_cjp.py."""
        p = Path(path)
        if p.suffix.lower() == ".pdf":
            raise ValueError(
                "Pass the OCR JSONL produced by `ntxp extract-cjp <pdf>`, not the raw PDF."
            )
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def to_canonical(self, row: dict) -> CanonicalRecord | None:
        full = str(row.get("full_name") or "").strip()
        company = str(row.get("company") or "").strip()
        if not full and not company:
            return None
        first, last = N.parse_name(full)
        rec = CanonicalRecord(source=self.source, raw=dict(row))
        rec.source_pk = "|".join([N.name_norm(first, last, full), N.org_name_norm(company)])
        if company:
            rec.org_name = company
            rec.org_name_norm = N.org_name_norm(company)
            rec.org_tags.append(Tag("source", "cjp_pdf"))
        if full:
            rec.first_name, rec.last_name = first, last
            rec.full_name = full
            rec.name_norm = N.name_norm(first, last, full)
            rec.tags.append(Tag("cjp", "holder"))
            rec.tags.append(Tag("source", "cjp_pdf"))
            for k in ("cert_id", "cert_date", "city", "state"):
                if row.get(k):
                    rec.contact_attrs[k] = row[k]
        rec.contact_attrs["_confidence"] = row.get("confidence")
        return rec


register(CjpPdfLoader())
