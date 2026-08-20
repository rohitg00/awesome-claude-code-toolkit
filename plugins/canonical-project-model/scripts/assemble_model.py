#!/usr/bin/env python3
"""
assemble_model.py — deterministic Canonical Project Record (CPR) assembler.

The reasoning step (reading the project-intake dossier and normalizing each
domain into its section schema) is done by parallel subagents — see
agents/model-orchestrator.md. Those agents write one JSON file per section into
<dossier>/model/sections/. THIS script does the deterministic, non-reasoning part:

  validate each section file against its schema  ->
  assemble canonical-model.json (the single source of truth)  ->
  render project-record.md (human-readable)  ->
  emit model-handoff.json (the downstream contract)

Mirrors project-intake's build_dossier.py philosophy: agents/Claude reason,
this script only validates, stitches, and writes. Stdlib only (Python 3.10+),
no API calls, no network. Safe to run in CI.

Section files are the reasoning output; if a section file is missing the section
is simply omitted (not faked). If a section file is present but malformed it is
flagged in needs_human_review and the run status degrades to 'partial'.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent
DEFAULT_SCHEMAS = PLUGIN_DIR / "schemas"
SCHEMA_VERSION = "1.0"
LOW_CONFIDENCE = 0.60  # values below this are surfaced for human review

# section_key -> (schema filename, const value of the "section" field, key whose
# array length is the section's record count). count_key=None => singleton (1).
SECTIONS = [
    ("project_identity", "project-identity.schema.json", "project_identity", None),
    ("contacts", "contacts.schema.json", "contacts", "contacts"),
    ("quick_links", "quick-links.schema.json", "quick_links", "links"),
    ("scope", "scope.schema.json", "scope", "items"),
    ("quantity_takeoff", "quantity-takeoff.schema.json", "quantity_takeoff", "items"),
    ("estimate_sov", "estimate-sov.schema.json", "estimate_sov", "cost_lines"),
    ("budget", "budget.schema.json", "budget", "lines"),
    ("trades", "trades.schema.json", "trades", "trades"),
    ("subcontractors", "subcontractors.schema.json", "subcontractors", "parties"),
    ("bid_log", "bid-log.schema.json", "bid_log", "bids"),
    ("submittal_log", "submittal-log.schema.json", "submittal_log", "entries"),
    ("critical_path", "critical-path.schema.json", "critical_path", "items"),
    ("schedule", "schedule.schema.json", "schedule", "milestones"),
    ("rfi_log", "rfi-log.schema.json", "rfi_log", "entries"),
    ("safety_plan", "safety-plan.schema.json", "safety_plan", "hazards"),
    ("logistics_plan", "logistics-plan.schema.json", "logistics_plan", "constraints"),
    ("requirements", "requirements.schema.json", "requirements", "requirements"),
    ("activity_stream", "activity-stream.schema.json", "activity_stream", "entries"),
    ("daily_reports", "daily-reports.schema.json", "daily_reports", "reports"),
    ("suggestions", "suggestions.schema.json", "suggestions", "items"),
    ("connectors", "connectors.schema.json", "connectors", "sources"),
]
SECTION_BY_KEY = {s[0]: s for s in SECTIONS}


def log(msg):
    sys.stderr.write(msg + "\n")


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        return {"__parse_error__": str(e)}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def validate_section(key, data, schema):
    """Lightweight, dependency-free validation: enough to catch a section file
    that was written against the wrong schema or is missing its spine. Returns a
    list of human-readable problems (empty = valid). Full JSON-Schema validation
    can be layered on if `jsonschema` is installed; this stays stdlib-only so it
    runs anywhere, matching the rest of the pipeline."""
    problems = []
    if not isinstance(data, dict):
        return [f"{key}: section file is not a JSON object"]
    if "__parse_error__" in data:
        return [f"{key}: invalid JSON ({data['__parse_error__']})"]
    # 1) the "section" discriminator must match the expected const
    _, _, const, _ = SECTION_BY_KEY[key]
    if data.get("section") != const:
        problems.append(
            f"{key}: 'section' is {data.get('section')!r}, expected {const!r}")
    # 2) schema-declared top-level required keys must be present
    for req in schema.get("required", []):
        if req not in data:
            problems.append(f"{key}: missing required key '{req}'")
    return problems


def walk_confidences(obj, acc):
    """Collect every provenance.confidence float anywhere in a section, and note
    low-confidence values so they can be surfaced for review."""
    if isinstance(obj, dict):
        prov = obj.get("provenance")
        if isinstance(prov, dict) and isinstance(prov.get("confidence"), (int, float)):
            c = float(prov["confidence"])
            acc["values"].append(c)
            if c < LOW_CONFIDENCE:
                label = (obj.get("description") or obj.get("text")
                         or obj.get("subject") or obj.get("company") or "value")
                acc["low"].append((label, c, prov.get("source_doc")))
        for v in obj.values():
            walk_confidences(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            walk_confidences(v, acc)


def count_records(key, data):
    _, _, _, count_key = SECTION_BY_KEY[key]
    if count_key is None:
        return 1  # singleton section (project_identity)
    arr = data.get(count_key)
    return len(arr) if isinstance(arr, list) else 0


def short(text, n=80):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def build(args):
    dossier = Path(args.dossier)
    schemas = Path(args.schemas)
    sections_dir = Path(args.sections) if args.sections else dossier / "model" / "sections"
    out_dir = Path(args.out) if args.out else dossier / "model"

    # Project identity for the handoff header comes from the dossier's project.json
    # when present (written by project-intake), else from the identity section.
    proj_json = load_json(dossier / "project.json") or {}
    project = (proj_json.get("project") if isinstance(proj_json, dict) else None) or {}

    if args.dry_run:
        planned = []
        for key, schema_file, _, _ in SECTIONS:
            sf = sections_dir / f"{key}.json"
            planned.append({"section": key, "file": str(sf), "present": sf.exists(),
                            "schema": schema_file})
        print(json.dumps({
            "dry_run": True,
            "dossier": str(dossier),
            "sections_dir": str(sections_dir),
            "out_dir": str(out_dir),
            "expected_sections": planned,
            "outputs": ["model/canonical-model.json", "model/sections/<key>.json",
                        "model/project-record.md", "model/model-handoff.json"],
        }, indent=2))
        return

    # ---- load + validate each section the agents produced ----
    sections_meta = {}       # key -> {path, status, count}
    sections_payload = {}    # key -> section dict (for embedding/reference)
    counts = {}
    conf_by_section = {}
    needs_review = []
    all_conf = []

    for key, schema_file, _, _ in SECTIONS:
        sf = sections_dir / f"{key}.json"
        if not sf.exists():
            continue  # section simply absent — omit, don't fake
        data = load_json(sf)
        schema = load_json(schemas / schema_file) or {}
        problems = validate_section(key, data, schema)
        if problems:
            needs_review.extend(problems)
            sections_meta[key] = {"path": f"sections/{key}.json", "status": "invalid", "count": 0}
            continue
        n = count_records(key, data)
        counts[key] = n
        sections_payload[key] = data
        sections_meta[key] = {
            "path": f"sections/{key}.json",
            "status": "ok" if n > 0 else "empty",
            "count": n,
        }
        # confidence rollup
        acc = {"values": [], "low": []}
        walk_confidences(data, acc)
        if acc["values"]:
            avg = round(sum(acc["values"]) / len(acc["values"]), 3)
            conf_by_section[key] = avg
            all_conf.extend(acc["values"])
        for label, c, doc in acc["low"][:25]:
            needs_review.append(f"{key}: low confidence ({c:.2f}) on \"{short(label, 60)}\""
                                + (f" [{doc}]" if doc else ""))

    # optional orchestrator-supplied meta: conflicts, normalization_log, extra review
    meta = load_json(sections_dir / "_meta.json") or {}
    conflicts = meta.get("conflicts", []) if isinstance(meta, dict) else []
    normalization_log = meta.get("normalization_log", []) if isinstance(meta, dict) else []
    health = meta.get("health", {}) if isinstance(meta, dict) else {}
    if isinstance(meta, dict):
        needs_review.extend(meta.get("needs_human_review", []) or [])
    for c in conflicts:
        if isinstance(c, dict) and c.get("field"):
            needs_review.append(f"conflict: documents disagree on '{c['field']}'")

    # near-duplicate review items (auto-generated + orchestrator-supplied) read as
    # noise on the dashboard — keep first occurrence, preserve order
    needs_review = list(dict.fromkeys(needs_review))

    overall_conf = round(sum(all_conf) / len(all_conf), 3) if all_conf else None

    # ---- write per-section files into the model dir (modular consumers) ----
    for key, data in sections_payload.items():
        write_json(out_dir / "sections" / f"{key}.json", data)

    # ---- assemble canonical-model.json (the single source of truth) ----
    ident = sections_payload.get("project_identity", {})
    joc = ident.get("joc") if isinstance(ident, dict) else None
    model_project = {
        "title": project.get("title") or ident.get("title") or "Untitled Project",
        "slug": project.get("slug") or dossier.name,
        "number": project.get("number") or ident.get("number"),
        "owner": project.get("owner") or ident.get("owner"),
        "location": project.get("location"),
        "delivery_method": ident.get("delivery_method"),
        "contract_type": ident.get("contract_type"),
        "phase": ident.get("phase", "estimate"),
        "is_joc": bool(joc) or ident.get("delivery_method") in ("joc", "idiq"),
    }
    # sections value: embedded object (self-contained) or relative path (modular)
    if args.no_embed:
        sections_value = {k: f"sections/{k}.json" for k in sections_payload}
    else:
        sections_value = dict(sections_payload)

    model = {
        "schema_version": SCHEMA_VERSION,
        "model_version": args.model_version,
        "generated_at": args.generated_at or "",
        "generated_by": "canonical-project-model",
        "source": {
            "dossier_dir": str(dossier),
            "handoff": str(dossier / "handoff.json"),
            "documents": len(proj_json.get("documents", [])) if isinstance(proj_json, dict) else 0,
        },
        "project": model_project,
        "classification": {
            "classification_system": "CSI MasterFormat",
            "masterformat_version": "MasterFormat 2020",
            "sov_standard": "AIA G703",
            "joc_unit_price_book": (joc or {}).get("unit_price_book", "") if isinstance(joc, dict) else "",
        },
        "sections": sections_value,
        "health": health,
        "counts": counts,
        "confidence": {"overall": overall_conf, "by_section": conf_by_section},
        "normalization_log": normalization_log,
        "conflicts": conflicts,
        "needs_human_review": needs_review,
        "next_consumers": ["vendor-bid-leveling", "rfp-analysis", "invoice-reconciliation",
                            "submittal-review", "estimating", "scheduling", "buyout"],
    }
    write_json(out_dir / "canonical-model.json", model)

    # ---- render project-record.md (human-readable projection) ----
    render_record(out_dir / "project-record.md", model, sections_payload, sections_meta)

    # ---- status + handoff ----
    if any(m["status"] == "invalid" for m in sections_meta.values()):
        status = "partial"
    elif sections_payload:
        status = "ready"
    else:
        status = "error"

    handoff = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "project": {k: model_project[k] for k in ("title", "slug", "number", "owner", "is_joc")},
        "source_dossier": str(dossier),
        "model_dir": str(out_dir),
        "model_file": "canonical-model.json",
        "record_md": "project-record.md",
        "sections": sections_meta,
        "counts": counts,
        "confidence": {"overall": overall_conf, "by_section": conf_by_section},
        "needs_human_review": needs_review,
        "next_step": args.next_step,
        "created_at": args.generated_at or "",
    }
    write_json(out_dir / "model-handoff.json", handoff)
    log(f"wrote canonical model: {out_dir / 'canonical-model.json'} (status={status}, "
        f"sections={len(sections_payload)})")
    print(json.dumps(handoff, indent=2))


def render_record(path, model, payload, meta):
    p = model["project"]
    L = [f"# {p['title']} — Canonical Project Record", ""]
    L.append("> Single source of truth assembled by `canonical-project-model`. "
             "Machine-readable companion: `canonical-model.json`. "
             "This layer normalizes and organizes — it does not price, level, or decide.")
    L += ["", "## Project", ""]
    for label, key in [("Number", "number"), ("Owner", "owner"), ("Location", "location"),
                       ("Delivery", "delivery_method"), ("Contract", "contract_type")]:
        L.append(f"- **{label}:** {p.get(key) or '—'}")
    L.append(f"- **JOC / IDIQ:** {'yes' if p.get('is_joc') else 'no'}")
    conf = model["confidence"]["overall"]
    L.append(f"- **Overall extraction confidence:** {conf if conf is not None else '—'}")

    L += ["", "## Sections", "",
          "| Section | Status | Records | Confidence |", "| --- | --- | --- | --- |"]
    for key, *_ in SECTIONS:
        m = meta.get(key)
        if not m:
            L.append(f"| {key} | absent | — | — |")
            continue
        c = model["confidence"]["by_section"].get(key)
        L.append(f"| {key} | {m['status']} | {m['count']} | {c if c is not None else '—'} |")

    # a few high-value highlights pulled straight from the structured data
    ident = payload.get("project_identity", {})
    if isinstance(ident, dict) and ident.get("key_dates"):
        L += ["", "## Key Dates", ""]
        for kd in ident["key_dates"][:12]:
            if isinstance(kd, dict):
                L.append(f"- **{kd.get('label', '—')}:** {kd.get('date') or kd.get('as_written') or '—'}")

    trades = payload.get("trades", {})
    if isinstance(trades, dict) and trades.get("trades"):
        L += ["", "## Trades / Bid Packages", ""]
        for t in trades["trades"][:40]:
            if isinstance(t, dict):
                divs = ", ".join(t.get("csi_divisions", []) or [])
                L.append(f"- `{t.get('trade_id', '?')}` {t.get('name', '—')}"
                         + (f" — Div {divs}" if divs else ""))

    if model["conflicts"]:
        L += ["", "## Conflicts (unresolved)", ""]
        for c in model["conflicts"][:25]:
            if isinstance(c, dict):
                L.append(f"- {c.get('field', 'field')}: documents disagree")

    if model["needs_human_review"]:
        L += ["", "## Needs Human Review", ""]
        for item in model["needs_human_review"][:50]:
            L.append(f"- {item}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Assemble the Canonical Project Record.")
    ap.add_argument("--dossier", required=True,
                    help="Path to projects/<slug>/ (the project-intake dossier).")
    ap.add_argument("--sections",
                    help="Dir of per-section JSON written by the normalizer agents "
                         "(default <dossier>/model/sections).")
    ap.add_argument("--out", help="Output dir (default <dossier>/model).")
    ap.add_argument("--schemas", default=str(DEFAULT_SCHEMAS))
    ap.add_argument("--model-version", type=int, default=1)
    ap.add_argument("--generated-at", help="ISO timestamp to stamp (caller supplies).")
    ap.add_argument("--next-step", default="construction-doc-pipeline:review")
    ap.add_argument("--no-embed", action="store_true",
                    help="Reference sections by relative path instead of embedding them "
                         "inline in canonical-model.json.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan (which section files are present) and exit.")
    build(ap.parse_args())


if __name__ == "__main__":
    main()
