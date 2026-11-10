#!/usr/bin/env python3
"""NTXP Plans Atlas: receiver for the Estimating Phase 1 drawing handoff.

The Phase 1 skill (ntxp-estimating-phase-1-intake) stages a request when a project's
drawings are ready (`handoffs/atlas-request.json`). This receiver does the rest, with
no questions asked, and writes everything the later steps need back into the KB:

  1. seed      project_identity, scope and trades sections of the Canonical Project
               Record from the KB (only when absent or still exactly as seeded;
               a section a person or another tool edited is never touched)
  2. deploy    deploy_atlas.py on the drawings, event kb_initial_review, with the
               Project Ignition blueprint (idempotent: unchanged drawings do nothing)
  3. interlink KB <-> atlas join (interlink.py): sheets, notes, schedules, submittals,
               scope, trades, specs and divisions
  4. respond   <outputs_dir>/atlas-response.json, plans_atlas.json, interlinks.json,
               atlas-chunks.json; then, if the Estimating skill is installed beside
               this one, its atlas_bridge.py receive folds it all into kb_index.jsonl

    python phase1_receiver.py receive --request <kb>/handoffs/atlas-request.json
    python phase1_receiver.py status  --request <...>
    python phase1_receiver.py fixture --out <dir>      # synthetic KB + drawings for tests
    python phase1_receiver.py selftest

Stdlib only. Deploying needs PyMuPDF (as deploy_atlas.py does). Never edits KB extracts,
never deletes, never writes outside <outputs_dir> and <project_root>.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQ_SCHEMA, RESP_SCHEMA = "ntxp.atlas-request/1", "ntxp.atlas-response/1"
SEEDED = "phase1-receiver"
STATES = {"alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
          "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
          "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
          "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
          "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
          "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY", "north carolina": "NC",
          "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
          "rhode island": "RI", "south carolina": "SC", "south dakota": "SD", "tennessee": "TN", "texas": "TX",
          "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
          "wisconsin": "WI", "wyoming": "WY"}


def log(msg):
    sys.stderr.write(f"[phase1-receiver] {msg}\n")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(path)


def sha256_text(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


# ------------------------------------------------------------------ KB -> CPR sections
def parse_location(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    m = re.search(r"^(?P<addr>.*?),?\s*(?P<city>[A-Za-z .'-]+?),\s*(?P<st>[A-Za-z .]+?)\.?\s*(?P<zip>\d{5})?(?:-\d{4})?$", raw)
    if m:
        st = m.group("st").strip()
        st = st.upper() if len(st) == 2 else STATES.get(st.lower(), st)
        out = {"city": m.group("city").strip(), "state": st}
        if m.group("addr"):
            out["address"] = m.group("addr").strip(" ,")
        if m.group("zip"):
            out["zip"] = m.group("zip")
        return out
    return {"address": raw}


DELIVERY_PATTERNS = (
    (r"design[\s-]*build|\bd/b\b", "design_build"), (r"cm\s*(?:at|@)\s*r|cmar|construction manager at[\s-]*risk", "cm_at_risk"),
    (r"cm\s*agen|cm as agent", "cm_agency"), (r"\bjoc\b|job order", "joc"), (r"idiq|indefinite", "idiq"),
    (r"design[\s-]*assist", "design_assist"), (r"\bipd\b|integrated project", "ipd"),
    (r"design[\s-]*bid[\s-]*build|\bdbb\b|hard bid|sealed bid|low bid", "design_bid_build"))


def map_delivery(raw):
    """Phase 1 keeps the delivery method as written (CSP, CMAR, ...); the CPR wants its enum.
    Returns an enum value, or None for a blank (the key is then omitted)."""
    t = str(raw or "").strip().lower()
    if not t:
        return None
    for pat, val in DELIVERY_PATTERNS:
        if re.search(pat, t):
            return val
    return "other"


def parse_date(text):
    t = str(text or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y", "%B %d %Y"):
        try:
            return dt.datetime.strptime(t, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def seed_sections(kb_dir, model_dir):
    """Write CPR sections from the KB. Returns {section: 'written'|'refreshed'|'kept'|'skipped'}."""
    kb_dir = Path(kb_dir)
    project = (load_json(kb_dir / "project.json", {}) or {}).get("project") or \
              (load_json(kb_dir / "kb.json", {}) or {}).get("project") or {}
    curation = load_json(kb_dir / "curation.json", {}) or {}
    ex = kb_dir / "extracts"
    sections = {}

    ident = {"section": "project_identity", "title": project.get("title") or kb_dir.name,
             "number": project.get("number") or "", "owner": project.get("owner") or ""}
    dm = map_delivery(project.get("delivery_method"))
    if dm:
        ident["delivery_method"] = dm
    loc = parse_location(project.get("location"))
    if loc:
        ident["location"] = loc
    m = re.match(r"^\s*([\d,]+(?:\.\d+)?)\s*(?:GSF|SF|S\.F\.|sq\.?\s*ft\.?|square feet)\b", str(project.get("gross_area") or ""), re.I)
    if m:
        ident["building"] = {"gross_sf": float(m.group(1).replace(",", ""))}     # as printed, never derived
    dates = []
    for d in load_json(ex / "dates.json", []) or []:
        dates.append({"label": d.get("label") or "", "date": parse_date(d.get("value")), "as_written": str(d.get("value") or ""),
                      "provenance": {"source_doc": d.get("_doc"), "page": None, "confidence": None}})
    if dates:
        ident["key_dates"] = dates
    sections["project_identity"] = ident

    assigned = {}
    for a in curation.get("division_assignments") or []:
        if not (isinstance(a, dict) and a.get("record") and a.get("csi_division")):
            continue
        rec = a["record"]      # the schema makes this the exact extract record (an object)
        key = (rec.get("text") or rec.get("item") or rec.get("name") or "") if isinstance(rec, dict) else str(rec)
        if str(key).strip():
            assigned[str(key).strip().lower()] = str(a["csi_division"])[:2]
    items = []
    for rec in load_json(ex / "scope-items.json", []) or []:
        text = (rec.get("text") or "").strip()
        if not text:
            continue
        div = str(rec.get("csi_division") or assigned.get(text.lower()) or "")[:2]
        item = {"scope_item_id": "SI-" + hashlib.sha1(text.encode()).hexdigest()[:8], "description": text,
                "provenance": {"source_doc": rec.get("_doc"), "page": None, "confidence": None}}
        if div.isdigit():
            item["csi"] = {"masterformat_division": div}
        items.append(item)
    if items:
        sections["scope"] = {"section": "scope", "items": items}

    trades = []
    for t in curation.get("trades") or []:
        div = str(t.get("csi_division") or "")[:2]
        if not (t.get("trade") and div.isdigit()):
            continue
        trades.append({"trade_id": f"TR-{div}-{re.sub(r'[^a-z0-9]+', '-', str(t['trade']).lower()).strip('-')[:16]}",
                       "name": t["trade"], "masterformat_division": div, "scope_summary": t.get("scope") or "",
                       "self_perform": bool(t.get("self_perform")), "bid_package_status": "not_started",
                       "spec_notes": [{"text": f"Governing specification section {sp}", "spec_section": str(sp), "kind": "general",
                                       "provenance": {"source_doc": "curation.json", "page": None, "confidence": None}}
                                      for sp in (t.get("spec_sections") or [])],
                       "provenance": {"source_doc": "curation.json", "page": None, "confidence": None}})
    if trades:
        sections["trades"] = {"section": "trades", "trades": trades}

    result = {}
    sec_dir = Path(model_dir) / "sections"
    for name, content in sections.items():
        path = sec_dir / f"{name}.json"
        digest = sha256_text(content)
        existing = load_json(path)
        if existing is None and not path.exists():
            state = "written"
        elif isinstance(existing, dict) and existing.get("_seeded_by") == SEEDED:
            body = {k: v for k, v in existing.items() if not k.startswith("_seed")}
            if sha256_text(body) == existing.get("_seed_hash"):
                state = "refreshed" if digest != existing.get("_seed_hash") else "kept"
            else:
                state = "kept"       # edited since seeding
        else:
            state = "kept"           # authored by a person or another tool
        if state in ("written", "refreshed"):
            write_json(path, {**content, "_seeded_by": SEEDED, "_seed_hash": digest})
        result[name] = state
    return result


# ------------------------------------------------------------------ staging + deploy
def stage_drawings(request, staging):
    """Link (or copy) each requested PDF into a clean staging folder. Two sources with the
    same basename get distinct staged names; a source file is never opened for writing."""
    staging = Path(staging)
    staging.mkdir(parents=True, exist_ok=True)
    for f in staging.iterdir():
        if f.is_symlink() or f.is_file():
            f.unlink()
    n = 0
    for d in request.get("drawings") or []:
        src = Path(d["path"])
        if not src.is_file():
            continue
        dest = staging / src.name
        if dest.exists() or dest.is_symlink():
            tag = re.sub(r"[^A-Za-z0-9_-]+", "-", str(d.get("doc_id") or n))[:40]
            dest = staging / f"{src.stem} [{tag}]{src.suffix}"
            k = 2
            while dest.exists() or dest.is_symlink():
                dest = staging / f"{src.stem} [{tag}-{k}]{src.suffix}"
                k += 1
        try:
            os.symlink(src, dest)
        except OSError:
            if dest.exists() or dest.is_symlink():
                continue
            shutil.copy2(src, dest)
        n += 1
    return n


def find_bridge():
    env = os.environ.get("NTXP_ESTIMATING_BRIDGE")
    cands = [Path(env)] if env else []
    for sib in ("ntxp-estimating-phase-1-intake", "NTXP-Estimating-Phase-1-Intake"):
        cands.append(HERE.parent.parent / sib / "scripts" / "atlas_bridge.py")
    home = Path.home() / ".claude" / "skills"
    cands += list(home.glob("*/atlas_bridge.py")) + list(home.glob("*/scripts/atlas_bridge.py"))
    cands += list(home.glob("synced/*/ntxp-estimating-phase-1-intake/scripts/atlas_bridge.py"))
    return next((c for c in cands if c.is_file()), None)


def validate_request(req):
    problems = []
    if req.get("schema") != REQ_SCHEMA:
        problems.append(f"schema must be {REQ_SCHEMA}")
    for k in ("request_id", "kb_path", "outputs_dir", "project_root", "drawings"):
        if k not in req:
            problems.append(f"missing {k}")
    return problems


def receive(request_path, force=False, chain=True):
    request_path = Path(request_path).resolve()
    req = load_json(request_path)
    if not isinstance(req, dict):
        raise SystemExit(f"{request_path}: not a readable request")
    problems = validate_request(req)
    if problems:
        raise SystemExit("invalid request: " + "; ".join(problems))
    kb_dir, out_dir, root = Path(req["kb_path"]), Path(req["outputs_dir"]), Path(req["project_root"])
    out_dir.mkdir(parents=True, exist_ok=True)
    resp_path = out_dir / "atlas-response.json"
    prior = load_json(resp_path)
    review, errors = [], []
    for u in req.get("unresolved_drawings") or []:
        review.append(f"drawing {u.get('doc_id')} not available locally ({u.get('reason')}); it is not in the atlas")

    model_dir = root / "model"
    seeded = seed_sections(kb_dir, model_dir)
    staging = out_dir / "staging" / "drawings"
    staged = stage_drawings(req, staging)
    base = {"schema": RESP_SCHEMA, "request_id": req["request_id"], "received_at": now(),
            "kb_path": str(kb_dir), "outputs_dir": str(out_dir), "project_root": str(root),
            "seeded_sections": seeded, "needs_review": review, "errors": errors}
    if not staged:
        resp = {**base, "status": "no_drawings", "atlas": {"sheets": 0},
                "note": "No drawing PDFs were available locally; the atlas builds when plans arrive."}
        write_json(resp_path, resp)
        print(json.dumps({"status": "no_drawings", "response": str(resp_path)}, indent=2))
        return resp

    cmd = [sys.executable, str(HERE / "deploy_atlas.py"), "--project", str(root), "--pdf-dir", str(staging),
           "--event", req.get("event") or "kb_initial_review", "--ignite"]
    if force:
        cmd.append("--force")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        deploy = json.loads(proc.stdout)
    except ValueError:
        deploy = {"status": "error", "error": (proc.stderr.strip().splitlines() or ["no output"])[-1]}
    if deploy.get("status") == "error" or proc.returncode not in (0,):
        errors.append(deploy.get("error") or "deploy_atlas.py failed")
        resp = {**base, "status": "error", "deploy": deploy}
        write_json(resp_path, resp)
        print(json.dumps({"status": "error", "detail": errors[-1], "response": str(resp_path)}, indent=2))
        return resp

    if deploy.get("status") == "no_drawings" or not (model_dir / "sections" / "plans_atlas.json").exists():
        resp = {**base, "status": "no_drawings", "deploy_status": deploy.get("status"), "atlas": {"sheets": 0},
                "note": deploy.get("note") or "None of the requested PDFs is a drawing set (for example letter-size "
                                              "documents); the atlas builds when plans arrive."}
        write_json(resp_path, resp)
        print(json.dumps({"status": "no_drawings", "response": str(resp_path)}, indent=2))
        return resp
    section = model_dir / "sections" / "plans_atlas.json"
    atlas = load_json(section, {}) or {}
    viewer = deploy.get("atlas")
    viewer_rel = Path(os.path.relpath(viewer, kb_dir)).as_posix() if viewer else "Plans Atlas/plans-atlas.html"
    sys.path.insert(0, str(HERE))
    import interlink
    stats, il_review, _ = interlink.run(kb_dir, section, out_dir, viewer_rel, req["request_id"],
                                        ignition_dir=(model_dir / "ignition") if (model_dir / "ignition").exists() else None)
    review += il_review + [str(x) for x in (atlas.get("needs_review") or [])][:20]
    shutil.copy2(section, out_dir / "plans_atlas.json")
    # Index Legend and scope index: a copy in the knowledge base, so every later step (and the Drive export) has them.
    legend = {}
    viewer_dir = Path(viewer).parent if viewer else None
    for key, src, name in (("scope_index", model_dir / "sections" / "scope_index.json", "scope_index.json"),
                           ("index_legend_pdf", viewer_dir / "Index Legend.pdf" if viewer_dir else None, "Index Legend.pdf"),
                           ("index_legend_md", viewer_dir / "INDEX-LEGEND.md" if viewer_dir else None, "INDEX-LEGEND.md")):
        if src and Path(src).is_file():
            shutil.copy2(src, out_dir / name)
            legend[key] = name
    crops = model_dir / "atlas" / "crops"
    if crops.is_dir():
        shutil.copytree(crops, out_dir / "crops", dirs_exist_ok=True)
        legend["crops"] = "crops/"
    if not legend.get("index_legend_pdf"):
        review.append("the Index Legend was not built for this set (needs PyMuPDF); the knowledge base has no legend copy")
    ign = deploy.get("ignition") or {}
    resp = {**base, "status": "ok", "deploy_status": deploy.get("status"),
            "atlas": {"sheets": len(atlas.get("sheets") or []), "links": len(atlas.get("links") or []),
                      "atlas_version": deploy.get("atlas_version"), "viewer_path": viewer, "viewer_rel": viewer_rel},
            "outputs": {"plans_atlas": "plans_atlas.json", "interlinks": "interlinks.json",
                        "chunks": "atlas-chunks.json", "viewer": viewer, **legend,
                        "linked_sets": deploy.get("linked_sets") or [],
                        "blueprint": str(model_dir / "ignition" / "blueprint.json") if ign else None,
                        "work_orders": str(model_dir / "ignition" / "work-orders") if ign else None},
            "interlink": {"stats": stats}, "ignition": {k: ign.get(k) for k in ("status", "divisions", "tasks", "price_lines", "gaps")} if ign else None,
            "needs_review": review, "errors": errors}
    write_json(resp_path, resp)
    log(f"atlas {deploy.get('status')}: {resp['atlas']['sheets']} sheets, {stats['links']} KB links")

    bridge = find_bridge() if (chain and req.get("chain", True)) else None
    if bridge:
        r = subprocess.run([sys.executable, str(bridge), "receive", "--kb", str(kb_dir), "--quiet"], capture_output=True, text=True)
        resp["chained"] = {"bridge": str(bridge), "exit": r.returncode,
                           "detail": (r.stdout.strip().splitlines() or [""])[-1] if r.returncode else "ok"}
        write_json(resp_path, resp)
    print(json.dumps({"status": "ok", "sheets": resp["atlas"]["sheets"], "kb_links": stats["links"],
                      "needs_review": len(review), "chained": bool(bridge), "response": str(resp_path)}, indent=2))
    return resp


def status(request_path):
    req = load_json(request_path) or {}
    resp = load_json(Path(req.get("outputs_dir", ".")) / "atlas-response.json") or {}
    state = "no_request" if not req else "pending" if not resp else \
        "current" if resp.get("request_id") == req.get("request_id") else "stale"
    print(json.dumps({"state": state, "request_id": req.get("request_id"), "response_status": resp.get("status")}, indent=2))


# ------------------------------------------------------------------ fixture + selftest
def make_fixture(out):
    """Synthetic Phase 1 KB with a two-sheet drawing PDF. Test data only."""
    import pymupdf as fitz
    out = Path(out)
    kb = out / "projects" / "demo-clinic"
    (kb / "extracts").mkdir(parents=True, exist_ok=True)
    dr = out / "drawings"
    dr.mkdir(exist_ok=True)
    doc = fitz.open()
    for no, title, body in (("A-101", "FIRST FLOOR PLAN", "SEE SHEET A-201 FOR ENLARGED PLANS. CEILINGS PER SPEC 09 51 13."),
                            ("A-201", "ENLARGED PLANS", "REFER TO A-101. PROVIDE ACOUSTICAL CEILING TILE PER SPEC 09 51 13.")):
        p = doc.new_page(width=3024, height=2160)
        p.insert_text((2850, 1950), no, fontsize=53, fontname="hebo")
        p.insert_text((2640, 2030), title, fontsize=25, fontname="hebo")
        p.insert_text((200, 300), body, fontsize=22)
        for i in range(30):
            p.insert_text((200, 400 + i * 30), f"TYPICAL NOTE {i} CONTRACTOR SHALL VERIFY ALL DIMENSIONS IN FIELD", fontsize=20)
    pdf = dr / "Demo Clinic Drawings.pdf"
    doc.save(str(pdf))
    project = {"title": "Demo Clinic Renovation", "slug": "demo-clinic", "number": "DC-1", "owner": "Demo ISD",
               "location": "100 Main St, Dallas, Texas 75201", "gross_area": "12,000 GSF", "delivery_method": "CSP"}
    (kb / "project.json").write_text(json.dumps({"project": project, "documents": [
        {"doc_id": "demo-clinic-drawings", "source": str(pdf), "status": "ok", "pages": 2}]}))
    sheets = [{"sheet_number": "A101", "sheet_title": "First Floor Plan", "discipline": "A", "scales": ["1/8\" = 1'-0\""],
               "page_index": "0", "_doc": "demo-clinic-drawings"},
              {"sheet_number": "A201", "sheet_title": "Enlarged Plans", "discipline": "A", "scales": [], "page_index": "1",
               "_doc": "demo-clinic-drawings"},
              {"sheet_number": "A901", "sheet_title": "Not In The Set", "discipline": "A", "scales": [], "page_index": "8",
               "_doc": "demo-clinic-drawings"}]
    (kb / "kb.json").write_text(json.dumps({"project": project, "sheet_index": sheets, "extracts": {}, "counts": {}}))
    ex = kb / "extracts"
    (ex / "sheets.json").write_text(json.dumps([{**s, "_doc": "demo-clinic-drawings"} for s in sheets]))
    (ex / "scope-items.json").write_text(json.dumps([{"text": "Replace acoustical ceilings per A-101", "csi_division": "09", "_doc": "demo-clinic-drawings"}]))
    (ex / "sheet-notes.json").write_text(json.dumps([{"sheet": "A-101", "note_type": "general", "key": "1", "text": "Verify ceiling height", "_doc": "demo-clinic-drawings"}]))
    (ex / "submittals.json").write_text(json.dumps([{"spec_section": "09 51 13", "csi_division": "09", "item": "Ceiling tile samples", "kind": "sample", "_doc": "demo-clinic-drawings"}]))
    (ex / "dates.json").write_text(json.dumps([{"label": "Bid Due", "value": "11/05/2026", "_doc": "demo-clinic-drawings"}]))
    for n in ("products", "requirements", "contacts", "schedules", "rooms", "measurements"):
        (ex / f"{n}.json").write_text("[]")
    (kb / "curation.json").write_text(json.dumps({"general_scope": "Ceiling replacement.", "trades": [
        {"trade": "Acoustical Ceilings", "scope": "ACT replacement", "sheets": ["A-101", "A-201"], "spec_sections": ["09 51 13"],
         "csi_division": "09", "self_perform": False}], "division_assignments": []}))
    (kb / "lifecycle.json").write_text(json.dumps({"phase": "bid", "phases": {}, "history": []}))
    (kb / "handoff.json").write_text(json.dumps({"schema_version": "1", "status": "ok", "project": project, "next_step": "phase-2:quantity-takeoff"}))
    return {"kb": str(kb), "drawings": [str(pdf)], "out": str(out)}


def request_for(kb, pdfs, rid="fixture-1"):
    kb = Path(kb)
    return {"schema": REQ_SCHEMA, "request_id": rid, "event": "kb_initial_review", "created_at": now(),
            "project": {"slug": kb.name}, "kb_path": str(kb), "outputs_dir": str(kb / "atlas"),
            "project_root": str(kb / "atlas" / "project"),
            "drawings": [{"path": p, "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest(), "doc_id": Path(p).stem} for p in pdfs],
            "unresolved_drawings": [], "chain": False}


def selftest():
    tmp = Path(tempfile.mkdtemp(prefix="phase1-recv-"))
    fx = make_fixture(tmp)
    req_path = Path(fx["kb"]) / "handoffs" / "atlas-request.json"
    write_json(req_path, request_for(fx["kb"], fx["drawings"]))
    resp = receive(req_path, chain=False)
    assert resp["status"] == "ok" and resp["atlas"]["sheets"] == 2, resp
    kb = Path(fx["kb"])
    for f in ("plans_atlas.json", "interlinks.json", "atlas-chunks.json", "atlas-response.json",
              "scope_index.json", "Index Legend.pdf", "INDEX-LEGEND.md"):
        assert (kb / "atlas" / f).is_file(), f
    assert resp["outputs"]["index_legend_pdf"] == "Index Legend.pdf" and resp["outputs"]["linked_sets"], resp["outputs"]
    il = load_json(kb / "atlas" / "interlinks.json")
    s = il["sheets"]["A-101"]
    assert s["kb_sheet"]["chunk"] is not None or il["stats"]["kb_index_missing"], il["stats"]
    assert s["links"].get("notes"), "KB sheet note must link to A-101"
    assert any(u["sheet_number"] == "A901" for u in il["unmatched"]["kb_sheets"]), "sheet missing from the set must be flagged"
    sec = load_json(kb / "atlas" / "project" / "model" / "sections" / "project_identity.json")
    assert sec["location"]["state"] == "TX" and sec["building"]["gross_sf"] == 12000.0 and sec["_seeded_by"] == SEEDED, sec
    assert resp["seeded_sections"]["scope"] == "written" and resp["seeded_sections"]["trades"] == "written"
    bp = load_json(kb / "atlas" / "project" / "model" / "ignition" / "blueprint.json")
    assert bp and any(d["division"] == "09" for d in bp["divisions"]), "ignition blueprint seeded from KB scope"
    # a person's edit to a seeded section is never overwritten
    sec_path = kb / "atlas" / "project" / "model" / "sections" / "scope.json"
    edited = load_json(sec_path)
    edited["items"].append({"scope_item_id": "HAND", "description": "added by hand"})
    write_json(sec_path, edited)
    resp2 = receive(req_path, chain=False)
    assert resp2["seeded_sections"]["scope"] == "kept", resp2["seeded_sections"]
    assert "HAND" in json.dumps(load_json(sec_path))
    # two sources with one basename must both stage, and neither source may change
    d2 = tmp / "other"
    d2.mkdir()
    twin = d2 / Path(fx["drawings"][0]).name
    shutil.copy2(fx["drawings"][0], twin)
    before = [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (fx["drawings"][0], twin)]
    stg = tmp / "stg"
    n = stage_drawings({"drawings": [{"path": fx["drawings"][0], "doc_id": "one"}, {"path": str(twin), "doc_id": "two"}]}, stg)
    after = [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (fx["drawings"][0], twin)]
    assert n == 2 and len(list(stg.iterdir())) == 2 and before == after, (n, list(stg.iterdir()))
    # a request whose PDFs are all non-drawings is a normal no_drawings answer
    import pymupdf as fitz
    letter = tmp / "letter.pdf"
    ld = fitz.open()
    ld.new_page(width=612, height=792).insert_text((72, 72), "Specification text")
    ld.save(str(letter))
    kb2 = Path(make_fixture(tmp / "second")["kb"])
    r2 = request_for(kb2, [str(letter)], "fixture-2")
    write_json(kb2 / "handoffs" / "atlas-request.json", r2)
    resp3 = receive(kb2 / "handoffs" / "atlas-request.json", chain=False)
    assert resp3["status"] == "no_drawings" and json.loads((kb2 / "atlas" / "atlas-response.json").read_text())["status"] == "no_drawings"
    # seeded trades follow the schema (spec_notes is an array of objects)
    trades = load_json(kb / "atlas" / "project" / "model" / "sections" / "trades.json")
    assert isinstance(trades["trades"][0]["spec_notes"], list) and trades["trades"][0]["spec_notes"][0]["spec_section"] == "09 51 13", trades
    assert [map_delivery(x) for x in ("Design-Build", "CMAR", "CM at Risk", "JOC", "Competitive Sealed Proposal", "", None, "Design Bid Build")] == \
        ["design_build", "cm_at_risk", "cm_at_risk", "joc", "other", None, None, "design_bid_build"]
    assert "delivery_method" in load_json(kb / "atlas" / "project" / "model" / "sections" / "project_identity.json"), "CSP maps to a valid enum value"
    cur = load_json(kb / "curation.json")
    cur["division_assignments"] = [{"record": {"text": "Seal expansion joints"}, "csi_division": "07", "why": "joint sealants"}]
    write_json(kb / "curation.json", cur)
    ex = kb / "extracts" / "scope-items.json"
    items = load_json(ex)
    items.append({"text": "Seal expansion joints", "_doc": "demo-clinic-drawings"})
    write_json(ex, items)
    kb3 = tmp / "third"
    shutil.copytree(kb, kb3 / "projects" / "demo-clinic")
    shutil.rmtree(kb3 / "projects" / "demo-clinic" / "atlas")
    seeded3 = seed_sections(kb3 / "projects" / "demo-clinic", kb3 / "model")
    sc = load_json(kb3 / "model" / "sections" / "scope.json")["items"]
    assert next(i for i in sc if i["description"] == "Seal expansion joints")["csi"]["masterformat_division"] == "07", sc
    print("phase1_receiver selftest passed:", tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("receive")
    r.add_argument("--request", required=True)
    r.add_argument("--force", action="store_true")
    r.add_argument("--no-chain", action="store_true", help="Do not call the Estimating bridge afterwards.")
    s = sub.add_parser("status")
    s.add_argument("--request", required=True)
    f = sub.add_parser("fixture")
    f.add_argument("--out", required=True)
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "receive":
        try:
            receive(a.request, a.force, not a.no_chain)
        finally:        # a hook that started this run passes its lock file; release it on every OS
            lock = os.environ.get("NTXP_RECEIVER_LOCK")
            if lock:
                Path(lock).unlink(missing_ok=True)
    elif a.cmd == "status":
        status(a.request)
    elif a.cmd == "fixture":
        print(json.dumps(make_fixture(a.out), indent=2))
    else:
        selftest()


if __name__ == "__main__":
    main()
