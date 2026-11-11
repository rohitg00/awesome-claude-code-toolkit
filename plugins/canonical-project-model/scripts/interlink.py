#!/usr/bin/env python3
"""Interlink the Phase 1 project Knowledge Base with the Plans Atlas.

Deterministic, stdlib only, no network. Reads a Phase 1 KB directory (kb.json,
kb_index.jsonl, curation.json, extracts/) and a plans_atlas.json section, and
writes two files:

  interlinks.json     sheet <-> KB facts, division <-> sheets <-> KB, spec section
                      <-> sheets <-> KB, a back-reference map keyed by KB chunk id,
                      and everything that did not match (never resolved, only listed)
  atlas-chunks.json   records the KB index folds in as atlas_* domains, so
                      `kb.py search` finds the drawings and every fact points back
                      to its sheet. Kinds: sheet (with phases, areas, trades, spec
                      sections, scale, OCR and review flags), sheet_text (the words
                      printed on each sheet), division, spec, trade, area, phase,
                      ignition (blueprint and processed status), atlas_status
                      (sheet counts, search coverage, review items), and the scope
                      index: project_index, detail, sheet_note, clarification, room,
                      schedule, schedule_row, millwork_elevation, door_mark, size_tag
                      and scope_index (one per CSI division)

Join keys, strongest first (each link records `via` and `confidence`):
  sheet_number   normalized sheet number equal                         0.95
  sheet_field    a KB record's own `sheet` field names the sheet        0.90
  trade_sheets   curation trade lists the sheet                         0.85
  spec_section   KB spec section is cited on the sheet in the atlas     0.80
  doc_page       same source document and page                          0.70
  text_mention   a real atlas sheet number appears in the record text   0.60
  division       same CSI division, capped at six sheets                0.40

KB extracts are never edited; this is an overlay. Called by phase1_receiver.py.
"""
import argparse
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

SCHEMA = "ntxp.interlinks/1"
SHEET_TOKEN = re.compile(r"\b[A-Z]{1,3}[-.]?\d{1,3}(?:\.\d{1,2})?[A-Z]?\b")
SPEC_TOKEN = re.compile(r"\b\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b")
ROLE_OF = {"sheet_note": "notes", "schedule_row": "schedules", "submittal": "submittals",
           "product": "products", "requirement": "requirements", "scope_item": "scope",
           "trade": "trades", "general_scope": "other", "phase2_flag": "other"}
CONF = {"sheet_number": 0.95, "sheet_field": 0.90, "trade_sheets": 0.85, "spec_section": 0.80,
        "doc_page": 0.70, "text_mention": 0.60, "division": 0.40}
DIVISION_CAP = 6


def nk(value):
    """Normalized key: A-101, a101 and A1.01 all become A101."""
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def spec_key(value):
    d = re.sub(r"\D", "", str(value or ""))
    return d[:6] if len(d) >= 6 else d


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def load_jsonl(path):
    rows = []
    try:
        for line in Path(path).read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except (OSError, ValueError):
        pass
    return rows


def sheet_refs(text_or_list):
    """Split a field such as 'A-101, A-102 / A-103' into normalized sheet keys."""
    if isinstance(text_or_list, (list, tuple)):
        parts = [str(x) for x in text_or_list]
    else:
        parts = re.split(r"[,;/&]|\band\b|\bthru\b", str(text_or_list or ""), flags=re.I)
    out = []
    for p in parts:
        k = nk(p)
        if k and re.match(r"^[A-Z]{1,3}\d", k):
            out.append(k)
    return out


def title_words(t):
    return {w for w in re.findall(r"[a-z0-9]+", str(t or "").lower()) if len(w) > 2}


def kb_chunks(kb_dir, slug):
    """Chunks from kb_index.jsonl; if the index is missing, derive reference-only chunks."""
    rows = [r for r in load_jsonl(Path(kb_dir) / "kb_index.jsonl")
            if not str(r.get("domain", "")).startswith("atlas_")]
    if rows:
        return rows, False
    ex = Path(kb_dir) / "extracts"
    derived = []
    for domain, fname in (("scope_item", "scope-items"), ("product", "products"), ("requirement", "requirements"),
                          ("sheet_note", "sheet-notes"), ("submittal", "submittals")):
        for i, rec in enumerate(load_json(ex / f"{fname}.json", []) or []):
            derived.append({"id": f"{slug}:{domain}:noindex{i}", "domain": domain, "record": rec,
                            "text": rec.get("text") or rec.get("item") or "", "doc": rec.get("_doc"),
                            "csi_division": rec.get("csi_division")})
    kb = load_json(Path(kb_dir) / "kb.json", {}) or {}
    for i, sh in enumerate(kb.get("sheet_index") or []):
        derived.append({"id": f"{slug}:sheet:noindex{i}", "domain": "sheet", "record": sh,
                        "text": f"{sh.get('sheet_number')} {sh.get('sheet_title')}", "doc": sh.get("_doc"),
                        "page_ref": sh.get("page_index"), "csi_division": None})
    return derived, True


SHEET_TEXT_LIMIT = 6000      # characters of printed sheet text kept per record (search, not a copy of the set)


def concept_name(c):
    return str(c.get("label") or c.get("name") or c.get("title") or c.get("id") or c.get("code") or "")


def sheet_text(words, sheet_id, limit=SHEET_TEXT_LIMIT):
    """Words printed on a sheet, in reading order from the atlas words sidecar, capped."""
    rows = (words or {}).get(sheet_id) or []
    rows = sorted(rows, key=lambda w: (round(float(w[1]), 2), float(w[0])))
    text = " ".join(str(w[4]) for w in rows if len(w) > 4 and w[4])
    return text[:limit], len(rows)


def ignition_record(ignition_dir):
    """A summary of Project Ignition (blueprint and processed output), or None when nothing has run."""
    if not ignition_dir or not Path(ignition_dir).is_dir():
        return None
    bp = load_json(Path(ignition_dir) / "blueprint.json", {}) or {}
    pr = load_json(Path(ignition_dir) / "processed.json", {}) or {}
    if not bp and not pr:
        return None
    sanity = pr.get("sanity") or {}
    rec = {"_kind": "ignition", "status": pr.get("status") or bp.get("status") or "blueprint",
           "draft": True, "divisions": len(bp.get("divisions") or []), "tasks": len(bp.get("tasks") or []),
           "gaps": list(bp.get("gaps") or []), "seats": list(pr.get("seats") or []),
           "expected_calendar_days": pr.get("expected_calendar_days"), "p80_calendar_days": pr.get("p80_calendar_days"),
           "direct_cost": pr.get("direct_cost"), "psf_verdict": sanity.get("verdict"),
           "estimate_psf": sanity.get("estimate_psf"), "sf_basis": sanity.get("sf_basis"),
           "needs_human_review": pr.get("needs_human_review"), "viewer": None}
    rec["text"] = ("Project Ignition (draft, pending PM approval): " + rec["status"] +
                   f"; {rec['divisions']} divisions; expected {rec['expected_calendar_days']} days"
                   + (f" (P80 {rec['p80_calendar_days']})" if rec["p80_calendar_days"] else "") +
                   f"; $/SF {rec['psf_verdict'] or 'not checked'}"
                   + ("; gaps: " + "; ".join(rec["gaps"]) if rec["gaps"] else ""))
    return rec


def scope_records(scope, viewer_rel):
    """Knowledge-base records for the scope index: one per fact, each pointing at its sheet and box."""
    if not scope:
        return []
    recs = []

    def link(sheet_id, box=None):
        b = ("&box=" + ",".join(str(v) for v in box)) if box else ""
        return f"{viewer_rel}#sheet={quote(str(sheet_id), safe='')}{b}"

    def base(kind, src, **extra):
        return {"_kind": kind, "sheet_id": src.get("sheet_id"), "sheet_no": src.get("sheet_no"),
                "sheet_title": src.get("sheet_title"), "doc": src.get("doc"),
                "page_index": str(max(int(src.get("page") or 1) - 1, 0)),
                "viewer": link(src.get("sheet_id"), src.get("box")), **extra}

    pi = scope.get("project_index") or {}
    addr = pi.get("address") or {}
    party = lambda p: (p or {}).get("name") if isinstance(p, dict) else p        # noqa: E731
    facts = [("Project Title", pi.get("title")), ("Project Number", pi.get("number")),
             ("Project Address", ", ".join(x for x in (addr.get("street"), addr.get("city_state_zip")) if x)),
             ("Project Owner", party(pi.get("owner"))), ("Project Architect", party(pi.get("architect"))),
             ("Project MEP Engineer", party(pi.get("mep_engineer")))]
    facts += [(f"Project Engineer ({e.get('role', '')})", e.get("name")) for e in pi.get("engineers_other") or []]
    recs.append({"_kind": "project_index", "facts": {k: v for k, v in facts if v}, "viewer": viewer_rel,
                 "trades": pi.get("trades") or [], "stats": scope.get("stats") or {},
                 "text": "Project index: " + "; ".join(f"{k}: {v}" for k, v in facts if v)})
    for p in pi.get("pages") or []:
        for d in p.get("details") or []:
            recs.append(base("detail", {**p, "box": d.get("box")}, label=d.get("label"), title=d.get("title"),
                             scale=d.get("scale"), text=f"Detail {d.get('label') or ''} {d.get('title')} on {p.get('sheet_no')}"))
    for b in pi.get("notes") or []:
        for it in b.get("items") or []:
            recs.append(base("sheet_note", {**b, "box": it.get("box")}, heading=b.get("heading"), note_kind=b.get("kind"),
                             no=it.get("no"), divisions=b.get("divisions") or [],
                             csi_division=(b.get("divisions") or [None])[0],
                             text=f"{b.get('sheet_no')} {b.get('heading')} {it.get('no') or ''}: {it.get('text')}"))
    labels = scope.get("clarification_labels") or {}
    for cat, rows in (scope.get("clarifications") or {}).items():
        for c in rows:
            recs.append(base("clarification", c, category=cat, category_label=labels.get(cat, cat),
                             divisions=c.get("divisions") or [], csi_division=(c.get("divisions") or [None])[0],
                             source=c.get("source"), confidence=c.get("confidence"),
                             text=f"{labels.get(cat, cat)} ({c.get('sheet_no')}): {c.get('text')}"))
    for r in pi.get("rooms") or []:
        recs.append(base("room", r, number=r.get("number"), name=r.get("name"), sf=r.get("sf"),
                         perimeter_lf=r.get("perimeter_lf"),
                         text=f"Room {r.get('number')} {r.get('name')}"
                              + (f" {r['sf']:,.0f} SF" if r.get("sf") is not None else " (SF not printed)")))
    for sch in scope.get("schedules") or []:
        recs.append(base("schedule", sch, schedule_id=sch.get("id"), title=sch.get("title"), schedule_type=sch.get("type"),
                         csi_division=sch.get("division"), columns=sch.get("columns"), row_count=sch.get("row_count"),
                         crop=sch.get("crop"), spec_sections=sch.get("spec_sections") or [], method=sch.get("method"),
                         confidence=sch.get("confidence"),
                         text=f"{sch.get('title')} on {sch.get('sheet_no')}: {sch.get('row_count')} rows; columns "
                              + ", ".join(sch.get("columns") or [])))
        for i, row in enumerate(sch.get("rows") or []):
            fields = {k: v for k, v in zip(sch.get("columns") or [], row) if v}
            recs.append(base("schedule_row", sch, schedule_id=sch.get("id"), schedule_type=sch.get("type"),
                             csi_division=sch.get("division"), row=i + 1, tag=row[0] if row else "", fields=fields,
                             text=f"{sch.get('title')} row {row[0] if row else i + 1}: "
                                  + "; ".join(f"{k} {v}" for k, v in fields.items())))
    for m in scope.get("millwork") or []:
        recs.append(base("millwork_elevation", m, elevation_id=m.get("id"), label=m.get("label"), title=m.get("title"),
                         csi_division="06", room_number=m.get("room_number"), cabinet_codes=m.get("cabinet_codes"),
                         finish_codes=m.get("finish_codes"), dimensions_printed=m.get("dimensions_printed"),
                         cabinet_count=None, linear_feet=None, crop=m.get("crop"),
                         text=f"Millwork elevation {m.get('label') or ''} {m.get('title')} on {m.get('sheet_no')}: cabinet codes "
                              + (", ".join(m.get("cabinet_codes") or []) or "none printed") + "; finishes "
                              + (", ".join(m.get("finish_codes") or []) or "none printed") + "; counts and lengths not measured"))
    for d, v in (scope.get("scope") or {}).items():
        for mk in v.get("door_marks") or []:
            ref = (mk.get("plan_refs") or [{}])[0]
            recs.append({"_kind": "door_mark", "mark": mk.get("mark"), "schedule_id": mk.get("schedule_id"),
                         "fields": mk.get("row") or {}, "csi_division": "08", "sheet_id": ref.get("sheet_id"),
                         "sheet_no": ref.get("sheet_no"),
                         "viewer": link(ref["sheet_id"], ref.get("box")) if ref.get("sheet_id") else viewer_rel,
                         "text": f"Door {mk.get('mark')}: " + "; ".join(f"{k} {x}" for k, x in (mk.get("row") or {}).items() if x)
                                 + (f"; on plan {ref.get('sheet_no')}" if ref.get("sheet_no") else "; not found on a plan")})
        for t in v.get("size_tags") or []:
            recs.append({"_kind": "size_tag", "csi_division": d, "tag_type": t.get("type"), "label": t.get("label"),
                         "size": t.get("size"), "tag_count": t.get("tag_count"), "measured_quantity": None,
                         "sheets": [x.get("sheet_no") for x in t.get("sheets") or []], "viewer": viewer_rel,
                         "text": f"{t.get('label')} {t.get('size')}: tagged {t.get('tag_count')} time(s) on "
                                 + ", ".join(x.get("sheet_no") or "" for x in (t.get("sheets") or [])[:8])
                                 + "; a tag count, not a measured length"})
        recs.append({"_kind": "scope_index", "csi_division": d, "division": d, "label": v.get("label"),
                     "schedules": v.get("schedules") or [], "sheets": v.get("sheets") or [],
                     "takeoff": v.get("takeoff") or [], "takeoff_status": v.get("takeoff_status"), "viewer": viewer_rel,
                     "text": f"Scope index Division {d} {v.get('label')}: {len(v.get('schedules') or [])} schedule(s), "
                             f"{len(v.get('sheets') or [])} sheet(s); takeoff: {v.get('takeoff_status')}"})
    return recs


def build(kb_dir, atlas, viewer_rel="Plans Atlas/plans-atlas.html", request_id="", ignition_dir=None, words=None, scope=None):
    kb_dir = Path(kb_dir)
    kb = load_json(kb_dir / "kb.json", {}) or {}
    slug = (kb.get("project") or {}).get("slug") or kb_dir.name
    curation = load_json(kb_dir / "curation.json", {}) or {}
    chunks, index_missing = kb_chunks(kb_dir, slug)

    sheets = atlas.get("sheets") or []
    by_key = {}
    for s in sheets:
        by_key.setdefault(nk(s.get("sheet_no") or s.get("sheet_id")), s)
    spec_sheets = {}
    for sp in (atlas.get("concepts") or {}).get("specs") or []:
        spec_sheets[spec_key(sp.get("section"))] = (sp, list(sp.get("sheet_ids") or []))
    trade_sheets = {}
    for t in (atlas.get("concepts") or {}).get("trades") or []:
        trade_sheets[str(t.get("division"))] = (t, list(t.get("sheet_ids") or []))
    sheet_by_id = {s["sheet_id"]: s for s in sheets}

    doc_stem = lambda d: nk(Path(str(d or "")).stem)          # noqa: E731
    atlas_by_docpage = {}
    for s in sheets:
        atlas_by_docpage[(doc_stem(s.get("source_doc")), int(s.get("page") or 0))] = s

    links = {s["sheet_id"]: {"notes": [], "schedules": [], "submittals": [], "products": [],
                             "requirements": [], "scope": [], "trades": [], "other": []} for s in sheets}
    via_log = {}          # (sheet_id, chunk_id) -> (via, confidence)
    backrefs = {}

    def attach(chunk, sheet_id, via):
        if sheet_id not in links:                        # a concept may name a sheet this set does not hold
            return
        cid = chunk["id"]
        key = (sheet_id, cid)
        conf = CONF[via]
        if key in via_log and via_log[key][1] >= conf:
            return
        via_log[key] = (via, conf)
        role = ROLE_OF.get(chunk.get("domain"), "other")
        if cid not in links[sheet_id][role]:
            links[sheet_id][role].append(cid)
        refs = backrefs.setdefault(cid, [])
        refs[:] = [r for r in refs if r["sheet_id"] != sheet_id]
        refs.append({"sheet_id": sheet_id, "via": via, "confidence": conf})

    # 1. sheet-to-sheet: KB sheet index <-> atlas sheet
    kb_sheet_chunk, title_conflicts = {}, []
    matched_kb_sheets = set()
    for c in chunks:
        if c.get("domain") != "sheet":
            continue
        rec = c.get("record") or {}
        s, via = by_key.get(nk(rec.get("sheet_number"))), "sheet_number"
        if s is None:
            try:
                page = int(rec.get("page_index")) + 1
            except (TypeError, ValueError):
                page = 0
            # No usable page means no page match: page 0 would pair with any sheet that also lacks one.
            s, via = (atlas_by_docpage.get((doc_stem(rec.get("_doc") or c.get("doc")), page)) if page else None), "doc_page"
        if s is None:
            continue
        sid = s["sheet_id"]
        kb_sheet_chunk[sid] = {"chunk": c["id"], "via": via, "confidence": CONF[via],
                               "kb_sheet_number": rec.get("sheet_number"), "kb_title": rec.get("sheet_title")}
        matched_kb_sheets.add(c["id"])
        if via == "sheet_number":
            kw, aw = title_words(rec.get("sheet_title")), title_words(s.get("title"))
            if kw and aw and len(kw & aw) / len(kw | aw) < 0.34:
                title_conflicts.append({"sheet_id": sid, "sheet_no": s.get("sheet_no"),
                                        "kb_title": rec.get("sheet_title"), "atlas_title": s.get("title")})
    # 2. every other KB chunk -> sheets
    for c in chunks:
        dom = c.get("domain")
        if dom in ("sheet", "contact", "date", "lesson", "pricing"):
            continue
        rec = c.get("record") or {}
        text = " ".join(str(x) for x in (c.get("text"), rec.get("text"), rec.get("item")) if x)
        hit = False
        for k in sheet_refs(rec.get("sheet")):
            if k in by_key:
                attach(c, by_key[k]["sheet_id"], "sheet_field")
                hit = True
        if dom == "trade":
            for k in sheet_refs(rec.get("sheets")):
                if k in by_key:
                    attach(c, by_key[k]["sheet_id"], "trade_sheets")
                    hit = True
            for sp in rec.get("spec_sections") or []:
                for sid in spec_sheets.get(spec_key(sp), (None, []))[1]:
                    attach(c, sid, "spec_section")
                    hit = True
        sp_keys = {spec_key(rec.get("spec_section"))} | {spec_key(m) for m in SPEC_TOKEN.findall(text)}
        for k in sp_keys:
            for sid in spec_sheets.get(k, (None, []))[1]:
                attach(c, sid, "spec_section")
                hit = True
        for tok in SHEET_TOKEN.findall(text.upper()):
            k = nk(tok)
            if len(k) >= 3 and k in by_key:
                attach(c, by_key[k]["sheet_id"], "text_mention")
                hit = True
        if not hit and dom in ("submittal", "product", "scope_item", "requirement"):
            div = str(c.get("csi_division") or rec.get("csi_division") or "")[:2]
            for sid in (trade_sheets.get(div, (None, []))[1])[:DIVISION_CAP]:
                attach(c, sid, "division")

    # 3. divisions and specs
    divisions, specs = {}, {}
    kb_by_div = {}
    for c in chunks:
        d = str(c.get("csi_division") or (c.get("record") or {}).get("csi_division") or "")[:2]
        if d:
            kb_by_div.setdefault(d, {}).setdefault(c.get("domain"), []).append(c["id"])
    div_files = {}
    for f in (kb_dir / "knowledge-base" / "Divisions").glob("*") if (kb_dir / "knowledge-base" / "Divisions").is_dir() else []:
        m = re.match(r"(\d{2})", f.name)
        if m:
            div_files[m.group(1)] = f.relative_to(kb_dir).as_posix()
    labels = {t.get("division"): t.get("label") for t in (atlas.get("concepts") or {}).get("trades") or []}
    for d in sorted(set(kb_by_div) | set(trade_sheets)):
        t = trade_sheets.get(d, ({}, []))
        divisions[d] = {"label": labels.get(d) or "", "atlas_sheets": t[1],
                        "specs": list(t[0].get("spec_sections") or []) if t[0] else [],
                        "kb_counts": {k: len(v) for k, v in sorted(kb_by_div.get(d, {}).items())},
                        "kb_division_file": div_files.get(d),
                        "itb_package": ("ignition/itb/itb-packages.html" if ignition_dir and (Path(ignition_dir) / "itb" / "itb-packages.html").exists() else None)}
    for key, (sp, sids) in spec_sheets.items():
        kb_ids = sorted({cid for sid in sids for role in links.get(sid, {}).values() for cid in role
                         if any(r["via"] == "spec_section" and r["sheet_id"] == sid for r in backrefs.get(cid, []))})
        specs[sp.get("section")] = {"title": sp.get("title") or "", "division": sp.get("division"),
                                    "atlas_sheets": sids, "kb_chunks": kb_ids[:50]}

    def anchor(sid):
        return f"{viewer_rel}#sheet={quote(sid, safe='')}"

    out_sheets = {}
    for s in sheets:
        sid = s["sheet_id"]
        out_sheets[sid] = {"sheet_no": s.get("sheet_no"), "title": s.get("title"), "page": s.get("page"),
                           "source_doc": s.get("source_doc"), "divisions": list(s.get("divisions") or []),
                           "viewer": anchor(sid), "kb_sheet": kb_sheet_chunk.get(sid),
                           "links": {k: v for k, v in links[sid].items() if v},
                           "link_counts": {k: len(v) for k, v in links[sid].items() if v}}
    unmatched_atlas = [sid for sid in links if sid not in kb_sheet_chunk]
    unmatched_kb = []
    for c in chunks:
        if c.get("domain") == "sheet" and c["id"] not in matched_kb_sheets:
            rec = c.get("record") or {}
            unmatched_kb.append({"chunk": c["id"], "sheet_number": rec.get("sheet_number"),
                                 "sheet_title": rec.get("sheet_title"), "doc": rec.get("_doc")})
    stats = {"atlas_sheets": len(sheets), "kb_sheets_matched": len(kb_sheet_chunk),
             "kb_chunks_linked": len(backrefs), "links": len(via_log),
             "title_conflicts": len(title_conflicts), "atlas_sheets_without_kb": len(unmatched_atlas),
             "kb_sheets_without_atlas": len(unmatched_kb), "kb_index_missing": index_missing}
    review = []
    if unmatched_kb:
        review.append(f"{len(unmatched_kb)} sheet(s) in the KB sheet index were not found in the drawing PDFs "
                      f"(e.g. {', '.join(str(u['sheet_number']) for u in unmatched_kb[:5])}): the set may be incomplete.")
    if title_conflicts:
        review.append(f"{len(title_conflicts)} sheet title(s) differ between the KB and the atlas; both are kept.")
    if index_missing:
        review.append("kb_index.jsonl was missing, so links point at provisional ids; rebuild the index and re-run.")
    interlinks = {"schema": SCHEMA, "request_id": request_id, "kb_slug": slug, "viewer": viewer_rel,
                  "stats": stats, "sheets": out_sheets, "divisions": divisions, "specs": specs,
                  "chunk_backrefs": backrefs,
                  "unmatched": {"atlas_sheets": unmatched_atlas, "kb_sheets": unmatched_kb},
                  "title_conflicts": title_conflicts, "needs_review": review}

    # 4. chunk records for the KB index
    recs = []
    trades_all = (atlas.get("concepts") or {}).get("trades") or []
    trade_labels = {}
    for t in trades_all:
        trade_labels.setdefault(str(t.get("division")), concept_name(t))
    spec_titles = {spec_key(sp.get("section")): sp.get("title") for sp in (atlas.get("concepts") or {}).get("specs") or []}
    sheet_trades, sheet_specs = {}, {}
    for t in trades_all:
        for sid in t.get("sheet_ids") or []:
            sheet_trades.setdefault(sid, []).append(concept_name(t))
    for sec, (sp, sids) in spec_sheets.items():
        for sid in sids:
            sheet_specs.setdefault(sid, []).append(sp.get("section"))
    for s in sheets:
        sid = s["sheet_id"]
        sh = out_sheets[sid]
        body, nwords = sheet_text(words, sid)
        phases = [concept_name(p) for p in s.get("phases") or []]
        areas = [concept_name(a) for a in s.get("areas") or []]
        flags = []
        if s.get("searchable") is False:
            flags.append("not searchable: no text layer and OCR did not read it")
        if s.get("ocr"):
            flags.append("text read by OCR: check the title block")
        if s.get("declared_scale") in (None, ""):
            flags.append("no declared scale")
        for n in s.get("needs_review") or []:
            flags.append(str(n))
        recs.append({"_kind": "sheet", "sheet_id": sid, "sheet_no": s.get("sheet_no"), "title": s.get("title"),
                     "discipline": s.get("discipline"), "divisions": sh["divisions"],
                     "csi_division": (sh["divisions"] or [None])[0], "doc": s.get("source_doc"),
                     "page_index": str(max(int(s.get("page") or 1) - 1, 0)), "viewer": sh["viewer"],
                     "kb_sheet_chunk": (sh["kb_sheet"] or {}).get("chunk"), "kb_links": sh["links"],
                     "kb_title": (sh["kb_sheet"] or {}).get("kb_title"),
                     "trades": sorted(set(sheet_trades.get(sid, []))), "spec_sections": sorted(set(sheet_specs.get(sid, []))),
                     "phases": phases, "areas": areas, "declared_scale": s.get("declared_scale"),
                     "searchable": s.get("searchable") is not False, "ocr": bool(s.get("ocr")),
                     "words": nwords, "image": s.get("image"), "thumbnail": s.get("thumbnail"),
                     "review_flags": flags,
                     "text": " ".join(x for x in [str(s.get("sheet_no") or ""), str(s.get("title") or ""),
                                                   ", ".join(sheet_trades.get(sid, [])), ", ".join(areas), ", ".join(phases)] if x)})
        if body:
            recs.append({"_kind": "sheet_text", "sheet_id": sid, "sheet_no": s.get("sheet_no"), "viewer": sh["viewer"],
                         "text": body, "words": nwords, "truncated": nwords and len(body) >= SHEET_TEXT_LIMIT})
    for d, v in divisions.items():
        recs.append({"_kind": "division", "division": d, "csi_division": d, "label": v["label"],
                     "atlas_sheets": v["atlas_sheets"], "specs": v["specs"], "kb_counts": v["kb_counts"],
                     "kb_division_file": v["kb_division_file"], "viewer": viewer_rel,
                     "text": f"Division {d} {v['label']}: {len(v['atlas_sheets'])} sheet(s), {len(v['specs'])} spec section(s)"})
    for sec, v in specs.items():
        recs.append({"_kind": "spec", "section": sec, "title": v["title"], "csi_division": v["division"],
                     "atlas_sheets": v["atlas_sheets"], "kb_chunks": v["kb_chunks"], "viewer": viewer_rel,
                     "text": f"Spec section {sec} {v['title']}"})
    for t in trades_all:
        sids = list(t.get("sheet_ids") or [])
        recs.append({"_kind": "trade", "division": str(t.get("division")), "label": concept_name(t),
                     "atlas_sheets": sids, "spec_sections": list(t.get("spec_sections") or []), "viewer": viewer_rel,
                     "text": f"Trade {concept_name(t)} (division {t.get('division')}): " + ", ".join(sids)})
    for kind, key in (("area", "areas"), ("phase", "phases")):
        for c in (atlas.get("concepts") or {}).get(key) or []:
            sids = list(c.get("sheet_ids") or [])
            recs.append({"_kind": kind, "name": concept_name(c), "atlas_sheets": sids, "viewer": viewer_rel,
                         "text": f"{kind.capitalize()} {concept_name(c)}: " + ", ".join(sids)})
    recs.extend(scope_records(scope, viewer_rel))
    ig = ignition_record(ignition_dir)
    if ig:
        recs.append(ig)
    search = atlas.get("search") or {}
    recs.append({"_kind": "atlas_status", "sheets": len(sheets), "sheets_searchable": search.get("sheets_indexed"),
                 "sheets_not_searchable": list(search.get("sheets_not_searchable") or []),
                 "sheets_with_ocr": sum(1 for s in sheets if s.get("ocr")),
                 "source_documents": (atlas.get("source_set") or {}).get("documents") or [],
                 "needs_review": list(atlas.get("needs_review") or []) + list(review),
                 "generated_at": atlas.get("generated_at"), "viewer": viewer_rel,
                 "text": f"Plans Atlas: {len(sheets)} sheet(s); " + (f"{search.get('sheets_indexed')} searchable" if search else "")
                         + ("; review: " + "; ".join(atlas.get("needs_review") or []) if atlas.get("needs_review") else "")})
    return interlinks, recs


def write_if_changed(path, obj):
    """Atomic write; returns True when the content changed."""
    path = Path(path)
    new = json.dumps(obj, indent=1, sort_keys=True)
    if path.exists() and path.read_text() == new:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new)
    tmp.replace(path)
    return True


def run(kb_dir, atlas_path, out_dir, viewer_rel, request_id="", ignition_dir=None):
    atlas = load_json(atlas_path)
    if not isinstance(atlas, dict) or not atlas.get("sheets"):
        raise SystemExit(f"{atlas_path}: no plans_atlas sheets to interlink")
    model_dir = Path(atlas_path).resolve().parent.parent          # model/sections/plans_atlas.json -> model/
    words = load_json(model_dir / "atlas-words.json", {}) or {}
    ignition_dir = ignition_dir or (model_dir / "ignition")
    scope = load_json(model_dir / "sections" / "scope_index.json")
    inter, recs = build(kb_dir, atlas, viewer_rel, request_id, ignition_dir, words, scope)
    inter["built_at"] = None      # keep the file byte-stable between identical runs
    changed = write_if_changed(Path(out_dir) / "interlinks.json", inter)
    changed |= write_if_changed(Path(out_dir) / "atlas-chunks.json", recs)
    return inter["stats"], inter["needs_review"], changed


def selftest():
    tmp = Path(tempfile.mkdtemp(prefix="interlink-"))
    (tmp / "extracts").mkdir()
    kb = {"project": {"slug": "demo"}, "sheet_index": [
        {"sheet_number": "A101", "sheet_title": "First Floor Plan", "page_index": "0", "_doc": "set"},
        {"sheet_number": "A999", "sheet_title": "Phantom Sheet", "page_index": "9", "_doc": "set"}]}
    (tmp / "kb.json").write_text(json.dumps(kb))
    (tmp / "curation.json").write_text("{}")
    idx = [
        {"id": "demo:sheet:s1", "domain": "sheet", "record": kb["sheet_index"][0], "text": "A101", "doc": "set"},
        {"id": "demo:sheet:s2", "domain": "sheet", "record": kb["sheet_index"][1], "text": "A999", "doc": "set"},
        {"id": "demo:sheet_note:n1", "domain": "sheet_note", "record": {"sheet": "A-101", "text": "Demo wall"}, "text": "Demo wall"},
        {"id": "demo:submittal:u1", "domain": "submittal", "record": {"spec_section": "09 51 13", "csi_division": "09", "item": "ACT"}, "text": "ACT", "csi_division": "09"},
        {"id": "demo:scope_item:c1", "domain": "scope_item", "record": {"text": "Replace ceilings per A-101 and M-9"}, "text": "Replace ceilings per A-101 and M-9"},
        {"id": "demo:product:p1", "domain": "product", "record": {"name": "Lay-in tile", "csi_division": "09"}, "text": "Lay-in tile", "csi_division": "09"}]
    (tmp / "kb_index.jsonl").write_text("\n".join(json.dumps(x) for x in idx))
    atlas = {"sheets": [{"sheet_id": "A-101", "sheet_no": "A-101", "title": "FIRST FLOOR PLAN", "page": 1,
                         "source_doc": "set.pdf", "divisions": ["09"]},
                        {"sheet_id": "A-201", "sheet_no": "A-201", "title": "ELEVATIONS", "page": 2,
                         "source_doc": "set.pdf", "divisions": ["09"]}],
             "concepts": {"trades": [{"division": "09", "label": "Finishes", "sheet_ids": ["A-101", "A-201"],
                                      "spec_sections": ["09 51 13"]}],
                          "specs": [{"section": "09 51 13", "division": "09", "title": "ACT", "sheet_ids": ["A-101"]}]}}
    words = {"A-101": [[0.5, 0.1, 0.6, 0.2, "CEILING"], [0.1, 0.1, 0.2, 0.2, "FIRST"]]}
    inter, recs = build(tmp, atlas, "Plans Atlas/plans-atlas.html", "rid", None, words)
    s = inter["sheets"]["A-101"]
    assert s["kb_sheet"]["chunk"] == "demo:sheet:s1" and s["kb_sheet"]["via"] == "sheet_number", s
    assert "demo:sheet_note:n1" in s["links"]["notes"], s["links"]
    assert "demo:submittal:u1" in s["links"]["submittals"], s["links"]
    assert "demo:scope_item:c1" in s["links"]["scope"], "text mention of a real sheet"
    assert not any(r["sheet_id"] == "M9" for refs in inter["chunk_backrefs"].values() for r in refs), "unknown sheet ignored"
    assert [u["sheet_number"] for u in inter["unmatched"]["kb_sheets"]] == ["A999"]
    assert inter["unmatched"]["atlas_sheets"] == ["A-201"]
    assert inter["chunk_backrefs"]["demo:product:p1"][0]["via"] == "division", "division fallback"
    assert s["viewer"] == "Plans Atlas/plans-atlas.html#sheet=A-101"
    assert {"sheet", "sheet_text", "division", "spec", "trade", "atlas_status"} <= {r["_kind"] for r in recs}
    sh = next(r for r in recs if r["_kind"] == "sheet" and r["sheet_id"] == "A-101")
    assert sh["trades"] == ["Finishes"] and sh["spec_sections"] == ["09 51 13"], sh
    scope = {"project_index": {"title": "Demo", "owner": {"name": "Test ISD"}, "pages": [], "notes": [
                 {"sheet_id": "A-101", "sheet_no": "A-101", "page": 1, "heading": "GENERAL NOTES", "kind": "general",
                  "items": [{"no": "1", "text": "Signage by owner.", "box": [0.1, 0.1, 0.2, 0.12]}], "divisions": ["09"]}],
                 "rooms": [{"sheet_id": "A-101", "sheet_no": "A-101", "page": 1, "number": "101", "name": "LOBBY", "sf": None,
                            "perimeter_lf": None, "box": [0.4, 0.4, 0.5, 0.45]}]},
             "clarifications": {"exclusions": [{"sheet_id": "A-101", "sheet_no": "A-101", "page": 1, "text": "Signage by owner.",
                                                "divisions": ["10"], "box": [0.1, 0.1, 0.2, 0.12]}]},
             "clarification_labels": {"exclusions": "Exclusions"},
             "schedules": [{"id": "A-101-S1", "sheet_id": "A-101", "sheet_no": "A-101", "page": 1, "title": "DOOR SCHEDULE",
                            "type": "door", "division": "08", "columns": ["MARK", "TYPE"], "rows": [["101A", "A"]],
                            "row_count": 1, "box": [0.5, 0.5, 0.7, 0.6]}],
             "scope": {"23": {"label": "HVAC", "size_tags": [{"type": "duct_rect", "label": "Rectangular duct", "size": "12x8",
                                                             "tag_count": 2, "sheets": [{"sheet_no": "M-101"}]}],
                              "takeoff_status": "no takeoff yet"}}}
    kinds = {}
    for r in scope_records(scope, "v.html"):
        kinds.setdefault(r["_kind"], []).append(r)
    assert {"project_index", "sheet_note", "clarification", "room", "schedule", "schedule_row", "size_tag", "scope_index"} <= set(kinds)
    assert kinds["schedule"][0]["viewer"] == "v.html#sheet=A-101&box=0.5,0.5,0.7,0.6", kinds["schedule"][0]["viewer"]
    assert "SF not printed" in kinds["room"][0]["text"] and kinds["size_tag"][0]["measured_quantity"] is None
    assert kinds["schedule_row"][0]["fields"] == {"MARK": "101A", "TYPE": "A"}
    st = next(r for r in recs if r["_kind"] == "sheet_text")
    assert st["text"] == "FIRST CEILING", st
    (tmp / "atlas.json").write_text(json.dumps(atlas))
    st1 = run(tmp, tmp / "atlas.json", tmp / "o", "v.html", "rid")
    st2 = run(tmp, tmp / "atlas.json", tmp / "o", "v.html", "rid")
    assert st1[2] is True and st2[2] is False, "second identical run must not rewrite files"
    print("interlink selftest passed:", tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("build", help="Write interlinks.json and atlas-chunks.json.")
    r.add_argument("--kb", required=True, type=Path)
    r.add_argument("--atlas", required=True, type=Path, help="plans_atlas.json section.")
    r.add_argument("--out", required=True, type=Path)
    r.add_argument("--viewer", default="Plans Atlas/plans-atlas.html")
    r.add_argument("--request-id", default="")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "selftest":
        selftest()
        return
    stats, review, changed = run(a.kb, a.atlas, a.out, a.viewer, a.request_id)
    print(json.dumps({"status": "interlinked", "changed": changed, "stats": stats, "needs_review": review}, indent=2))


if __name__ == "__main__":
    main()
