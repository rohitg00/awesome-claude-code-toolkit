#!/usr/bin/env python3
"""NTXP Project Ignition: Jev-platformed blueprint -> frontier magic -> Jev processing.

Three stages, one deterministic spine (stdlib only; no network, and no API calls except the
optional `seats` command, which shells out to the logged-in `claude` and `codex` CLIs):

  blueprint   Reads the Canonical Project Record + Plans Atlas and does all the
              upfront deterministic work: division packets (scope, takeoff, specs,
              sheets, price lines), a CPM task skeleton, and typed work orders for
              the two frontier seats (Astra = gpt-6-astra, Opus = claude-opus-5-5)
              plus a Compass work order for cited public $/SF figures.
  process     Takes the raw seat outputs and does the Jev work: schema checks,
              PERT comparison and CPM roll-up, unit-price decisions, confidence
              dating, and a sanity check against localized public $/SF benchmarks.
              Every judgment is a typed enum answer written to jev-judgments.jsonl.
  itb         Generates 8.5 x 11 ITB pages per division package (subcontractor
              safe: scope and quantities only, never our prices) plus an internal
              ignition summary.

Nothing here is final. Prices, durations and ITB text are DRAFTS until the PM
approves them; nothing is sent outward. The frontier models supply numbers; this
script only validates, compares, scores and lays them out. Missing data is
flagged, never invented (no gross SF -> the $/SF check says so).

    python ignition.py blueprint --project <dir>
    python ignition.py seats     --project <dir> [--only astra|opus]   # run the work orders on the real seats
    python ignition.py process   --project <dir> [--astra f] [--opus f] [--benchmarks f]
    python ignition.py itb       --project <dir> [--pdf]
    python ignition.py selftest
"""
import argparse
import csv
import hashlib
import datetime as dt
import html
import json
import math
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEATS = {"astra": {"provider": "openai", "model": "gpt-6-astra", "persona": "Torque (sub-model)"},
         "opus": {"provider": "anthropic", "model": "claude-opus-5-5", "persona": "Keel"}}
BLOCKED_SEATS = ["deepseek (Ledger)", "glm (Mason)"]   # never receive owner, bid or pricing content

# Construction sequence template: phase -> divisions. Phases run finish-to-start.
PHASES = [
    ("P0", "Mobilization, submittals and procurement", ["00", "01"]),
    ("P1", "Selective demolition and sitework", ["02", "31", "32", "33"]),
    ("P2", "Structure and enclosure", ["03", "04", "05", "06", "07"]),
    ("P3", "Rough-in: mechanical, electrical, plumbing, fire, technology", ["21", "22", "23", "25", "26", "27", "28"]),
    ("P4", "Openings, finishes and specialties", ["08", "09", "10", "11", "12", "13", "14"]),
    ("P5", "Conveying, testing and closeout", ["41", "34", "35", "40", "42", "43", "44", "45", "46", "48"]),
]
SHELF_LIFE_DAYS = {"05": 90, "26": 90, "07": 120, "22": 120, "23": 120, "31": 120, "32": 120}
DEFAULT_SHELF_LIFE = 180
BASIS_WEIGHT = {"vendor_quote": 1.0, "book": 0.95, "public_bid": 0.9, "model_estimate": 0.6}
AGREE_WEIGHT = {"agree": 1.0, "minor": 0.85, "divergent": 0.6, "single": 0.75}
PERT_AGREE, PERT_MINOR = 0.15, 0.35
PRICE_AGREE, PRICE_MINOR = 0.10, 0.25
Z80 = 0.8416

BENCH_COLS = ["building_type", "project_type", "region", "state", "year", "basis", "scope",
              "low_psf", "mid_psf", "high_psf", "source", "source_url", "retrieved"]


def log(msg):
    sys.stderr.write(f"[ignition] {msg}\n")


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def today(args=None):
    t = getattr(args, "today", None) if args else None
    return dt.date.fromisoformat(t) if t else dt.date.today()


def division_labels():
    d = load_json(ROOT / "resources" / "masterformat-divisions.json", {}) or {}
    return {x["division"]: x["title"] for x in d.get("divisions", [])}


def div_of(csi):
    m = re.match(r"\s*(\d{2})", str((csi or {}).get("masterformat_division") if isinstance(csi, dict) else csi or ""))
    return m.group(1) if m else None


def phase_of(div):
    for pid, _, divs in PHASES:
        if div in divs:
            return pid
    return "P5"


# ------------------------------------------------------------------ Jev (typed judgments)
class Jev:
    """Typed-answer referee. Every judgment is an enum answer with a rationale, logged
    so the council engine can replay it through the hosted Jev model. The local rules
    here answer first (zero cost); a hosted Jev can overrule by replaying the log."""

    def __init__(self):
        self.log = []

    def judge(self, kind, question, inputs, options, answer, rationale):
        assert answer in options, (kind, answer, options)
        self.log.append({"id": f"J-{len(self.log) + 1:04d}", "kind": kind, "question": question,
                         "input": inputs, "options": options, "answer": answer,
                         "rationale": rationale, "answered_by": "jev-local-rules"})
        return answer

    def stance(self, kind, rel, agree, minor, label):
        ans = "agree" if rel <= agree else "minor" if rel <= minor else "divergent"
        return self.judge(kind, f"Do the two models agree on {label}?", {"relative_gap": round(rel, 4)},
                          ["agree", "minor", "divergent"], ans,
                          f"gap {rel:.1%}; agree <= {agree:.0%}, minor <= {minor:.0%}")


# ------------------------------------------------------------------ project data
def load_project(project):
    project = Path(project)
    if not project.is_dir():
        sys.exit(f"project directory not found: {project}")
    model = project / "model"
    sec = {p.stem: load_json(p, {}) for p in (model / "sections").glob("*.json")} if (model / "sections").is_dir() else {}
    cm = load_json(model / "canonical-model.json", {}) or {}
    ident = sec.get("project_identity") or {}
    cmp_ = cm.get("project", {})
    loc = ident.get("location") or cmp_.get("location") or ""
    if isinstance(loc, dict):
        loc = ", ".join(x for x in (loc.get("city"), loc.get("state")) if x) or loc.get("address") or ""
    facts = {
        "title": ident.get("title") or cmp_.get("title") or project.name.replace("_", " ").replace("-", " "),
        "number": ident.get("number") or cmp_.get("number") or "",
        "owner": ident.get("owner") or cmp_.get("owner") or "",
        "location": str(loc),
        "market_sector": ident.get("market_sector") or "",
        "project_type": ident.get("project_type") or "unknown",
        "delivery_method": ident.get("delivery_method") or cmp_.get("delivery_method") or "",
        "is_joc": bool(cmp_.get("is_joc")),
        "gross_sf": (ident.get("building") or {}).get("gross_sf"),
        "work_area_sf": (ident.get("building") or {}).get("work_area_sf"),
        "occupancy_type": (ident.get("building") or {}).get("occupancy_type") or "",
        "key_dates": ident.get("key_dates") or [],
    }
    return project, model, sec, facts


def parse_days(text):
    m = re.search(r"(\d+)\s*(calendar|working|business|work)?", str(text or ""), re.I)
    if not m:
        return None
    n = int(m.group(1))
    return n * 5 / 7 if (m.group(2) or "calendar").lower() == "calendar" else float(n)


def build_packets(sec, labels):
    atlas = sec.get("plans_atlas") or {}
    sheets = atlas.get("sheets") or []
    specs = (atlas.get("concepts") or {}).get("specs") or []
    packets = {}

    def pk(div):
        return packets.setdefault(div, {
            "division": div, "label": labels.get(div, f"Division {div}"), "phase": phase_of(div),
            "scope_items": [], "takeoff": [], "cost_lines": [], "trade": None,
            "spec_sections": [], "sheets": [], "price_lines": []})

    for it in (sec.get("scope") or {}).get("items") or []:
        d = div_of(it.get("csi"))
        if d:
            pk(d)["scope_items"].append({"id": it.get("scope_item_id"), "description": it.get("description"),
                                         "uom": it.get("uom") or ""})
    for it in (sec.get("quantity_takeoff") or {}).get("items") or []:
        d = div_of(it.get("csi"))
        if d:
            q = it.get("quantity")
            pk(d)["takeoff"].append({"id": it.get("takeoff_id"), "scope_item_id": it.get("scope_item_id"), "description": it.get("description"),
                                     "quantity": q.get("value") if isinstance(q, dict) else q,
                                     "uom": (q.get("uom") if isinstance(q, dict) else "") or ""})
    for it in (sec.get("estimate_sov") or {}).get("cost_lines") or []:
        d = div_of(it.get("csi"))
        if d:
            r = it.get("unit_rate")
            rate = r.get("amount") if isinstance(r, dict) else r
            joc = it.get("joc_line")
            upb = ((joc or {}).get("upb_unit_price") or {}) if isinstance(joc, dict) else {}
            upb = upb.get("amount") if isinstance(upb, dict) else upb
            anchor_src = "unit_rate" if rate is not None else ("upb_unit_price" if upb is not None else None)
            pk(d)["cost_lines"].append({"id": it.get("cost_line_id"), "scope_item_id": it.get("scope_item_id"), "description": it.get("description"),
                                        "quantity": it.get("quantity") if not isinstance(it.get("quantity"), dict) else it["quantity"].get("value"),
                                        "unit_rate": rate if rate is not None else upb,
                                        "anchor_source": anchor_src,
                                        "joc_line": bool(joc) and anchor_src is not None})
    for tr in (sec.get("trades") or {}).get("trades") or []:
        d = (str(tr.get("masterformat_division") or "")[:2]) or None
        if d:
            pk(d)["trade"] = {"trade_id": tr.get("trade_id"), "name": tr.get("name"),
                              "bid_package_status": tr.get("bid_package_status"), "scope_summary": tr.get("scope_summary") or "",
                              "min_bidders_required": tr.get("min_bidders_required")}
    for t in (atlas.get("concepts") or {}).get("trades") or []:
        if t.get("sheet_ids") or t.get("spec_sections"):
            pk(t["division"])
    for sp in specs:
        d = str(sp.get("division") or "")[:2]
        if d:
            pk(d)["spec_sections"].append({"section": sp.get("section"), "title": sp.get("title") or ""})
    by_sheet = {s.get("sheet_id"): s for s in sheets}
    for t in (atlas.get("concepts") or {}).get("trades") or []:
        for sid in t.get("sheet_ids") or []:
            s = by_sheet.get(sid)
            if s:
                pk(t["division"])["sheets"].append({"sheet_no": s.get("sheet_no"), "title": s.get("title") or "",
                                                    "page": s.get("page")})
    for d, p in packets.items():
        lines, seen = [], set()
        for it in p["takeoff"]:
            lines.append({"line_id": it["id"], "scope_item_id": it.get("scope_item_id"), "description": it["description"],
                          "uom": it["uom"], "quantity": it["quantity"], "quantity_source": "takeoff",
                          "anchor": None, "joc_line": False, "anchor_source": None})
        # A scope item gets its own line only when no takeoff line already covers it.
        covered = {l["scope_item_id"] for l in lines if l.get("scope_item_id")}
        for it in p["scope_items"]:
            if it["id"] and it["id"] not in covered and not any(l["line_id"] == it["id"] for l in lines):
                lines.append({"line_id": it["id"], "scope_item_id": it["id"], "description": it["description"], "uom": it["uom"],
                              "quantity": None, "quantity_source": "unquantified", "anchor": None, "joc_line": False,
                              "anchor_source": None})
        # Cost lines and takeoff lines live in separate ID spaces; they join on scope_item_id.
        for it in p["cost_lines"]:
            hit = next((l for l in lines if l["line_id"] == it["id"]), None) or \
                next((l for l in lines if it.get("scope_item_id") and l.get("scope_item_id") == it["scope_item_id"]
                      and l["anchor"] is None), None)
            if hit:
                hit["anchor"], hit["joc_line"], hit["anchor_source"] = it["unit_rate"], it["joc_line"], it["anchor_source"]
                if hit["quantity"] is None:
                    hit["quantity"] = it["quantity"]
            else:
                lines.append({"line_id": it["id"], "scope_item_id": it.get("scope_item_id"), "description": it["description"], "uom": "",
                              "quantity": it["quantity"], "quantity_source": "cost_line",
                              "anchor": it["unit_rate"], "joc_line": it["joc_line"], "anchor_source": it["anchor_source"]})
        for l in lines:
            if l["line_id"] in seen:
                continue
            seen.add(l["line_id"])
            p["price_lines"].append(l)
        if not p["price_lines"]:
            p["price_lines"].append({"line_id": f"L-{d}-LS", "description": f"Division {d} {p['label']} lump sum (no takeoff yet)",
                                     "uom": "LS", "quantity": 1, "quantity_source": "lump_sum", "anchor": None, "joc_line": False})
        p["evidence"] = {"sheets": len({x["sheet_no"] for x in p["sheets"]}), "spec_sections": len(p["spec_sections"]),
                         "scope_items": len(p["scope_items"]), "takeoff": len(p["takeoff"]),
                         "cost_lines": len(p["cost_lines"]), "trade_package": bool(p["trade"])}
        p["low_evidence"] = not (p["evidence"]["sheets"] or p["evidence"]["scope_items"] or p["evidence"]["takeoff"]
                                 or p["evidence"]["cost_lines"] or p["evidence"]["trade_package"])
        p["sheets"] = sorted({(s["sheet_no"], s["title"], s["page"]): s for s in p["sheets"]}.values(), key=lambda s: s["page"] or 0)
        p["spec_sections"] = sorted({s["section"]: s for s in p["spec_sections"]}.values(), key=lambda s: s["section"] or "")
    return packets


def build_tasks(packets):
    """CPM skeleton: one task per active division, phases finish-to-start."""
    order = [p[0] for p in PHASES]
    by_phase = {pid: [] for pid in order}
    for d in sorted(packets):
        by_phase[packets[d]["phase"]].append(d)
    tasks, prev = [], []
    for pid in order:
        cur = []
        for d in by_phase[pid]:
            tid = f"T-{d}"
            tasks.append({"task_id": tid, "division": d, "label": f"Division {d} {packets[d]['label']}",
                          "phase": pid, "predecessors": list(prev)})
            cur.append(tid)
        if cur:
            prev = cur
    tasks.append({"task_id": "T-CLOSE", "division": None, "label": "Punch list, commissioning and closeout",
                  "phase": "P5", "predecessors": list(prev)})
    return tasks


OUTPUT_CONTRACT = {
    "seat": "astra | opus", "model": "model id", "generated_at": "ISO-8601 timestamp",
    "divisions": [{
        "division": "two-digit CSI division from the blueprint",
        "not_applicable": "true when no work belongs in this division (then give reason and omit pert and prices)", "reason": "",
        "pert": [{"task_id": "from blueprint.tasks", "optimistic": "working days", "most_likely": "working days",
                  "pessimistic": "working days", "basis": "one sentence"}],
        "prices": [{"line_id": "from price_lines", "quantity": "number or null", "uom": "unit",
                    "unit_price": "USD per uom, installed, excluding GC markup", "low": "optional", "high": "optional",
                    "price_basis": "vendor_quote | book | public_bid | model_estimate",
                    "price_date": "YYYY-MM-DD the price is true for, or null", "source": "citation or URL", "notes": ""}],
        "itb": {"scope_narrative": "plain-language scope for subcontractor bidders",
                "inclusions": [], "exclusions": [], "clarifications": [], "required_submittals": [],
                "alternates": [], "risks": []}}],
    "project": {"assumptions": [], "risks": []},
}

RULES = [
    "Answer with JSON only, matching output_contract exactly. No prose outside JSON.",
    "Use only the facts in inputs. Quote spec sections and sheet numbers exactly as given.",
    "Never invent a quantity. If a line has quantity null and is not a lump sum, give your estimated quantity and say so in notes.",
    "Every unit_price needs price_basis, price_date and source. If you cannot cite one, use price_basis 'model_estimate', price_date null and say so.",
    "Give working-day durations as optimistic <= most_likely <= pessimistic for every task listed.",
    "Prices are installed unit costs before general-contractor overhead, profit, bond and insurance.",
    "A division with low_evidence true has no sheet, scope, takeoff, cost line or trade package, only a stray spec mention. Return it with not_applicable true and a one-sentence reason unless the spec text clearly puts work in it.",
    "ITB text is for subcontractors: describe scope and responsibilities, never our budget, our unit prices or our margins.",
]


def make_work_order(seat, bp):
    return {"work_order": "project-ignition", "seat": seat, **SEATS[seat],
            "data_restrictions": "none", "never_send_to": BLOCKED_SEATS,
            "project": bp["project"], "rules": RULES, "output_contract": OUTPUT_CONTRACT,
            "tasks": bp["tasks"], "divisions": bp["divisions"], "project_assumptions_needed": bp["gaps"]}


def compass_order(facts):
    return {"work_order": "public-sf-benchmarks", "seat": "perplexity", "model": "sonar-pro", "persona": "Compass",
            "data_restrictions": "none; contains no owner, bid or pricing content",
            "ask": ("Find public, citable construction cost per square foot figures for this building type and location "
                    "(public bid tabulations, state or agency cost guides, published cost reports). Return CSV rows only, with the "
                    "columns below. Give hard-cost figures unless a source states otherwise. Cite every row; skip rows you cannot cite."),
            "building_type": facts["market_sector"] or facts["occupancy_type"] or "unknown",
            "project_type": facts["project_type"], "region": facts["location"],
            "prefer": ["same city or metro", "same state", "national only as a last resort"],
            "csv_columns": BENCH_COLS, "save_as": "model/ignition/benchmarks.csv"}


def cmd_blueprint(args):
    project, model, sec, facts = load_project(args.project)
    labels = division_labels()
    packets = build_packets(sec, labels)
    gaps = []
    if not facts["gross_sf"] and facts.get("work_area_sf"):
        gaps.append(f"gross_sf missing: $/SF uses the stated work area ({facts['work_area_sf']:,.0f} SF), not the whole building")
    elif not facts["gross_sf"]:
        gaps.append("gross_sf missing: the $/SF sanity check stays off until the PM supplies it")
    if not facts["location"]:
        gaps.append("location missing: benchmark matching falls back to national")
    if not packets:
        gaps.append("no divisions found in scope, takeoff, trades or atlas: run the project intake and Plans Atlas first")
    quant_gaps = [l["line_id"] for p in packets.values() for l in p["price_lines"] if l["quantity"] is None]
    if quant_gaps:
        gaps.append(f"{len(quant_gaps)} price line(s) have no quantity; seats will be asked to estimate and flag them")
    tasks = build_tasks(packets)
    out = model / "ignition"
    bp = {"stage": "blueprint", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
          "status": "draft_pending_pm_approval", "project": facts, "gaps": gaps, "tasks": tasks,
          "divisions": [packets[d] for d in sorted(packets)],
          "target_days": parse_days((sec.get("schedule") or {}).get("contract_duration"))}
    write_json(out / "blueprint.json", bp)
    for seat in SEATS:
        write_json(out / "work-orders" / f"{seat}.json", make_work_order(seat, bp))
    write_json(out / "work-orders" / "compass.json", compass_order(facts))
    (out / "raw").mkdir(parents=True, exist_ok=True)
    print(json.dumps({"status": "blueprint_ready", "divisions": len(packets), "tasks": len(tasks),
                      "price_lines": sum(len(p["price_lines"]) for p in packets.values()),
                      "gaps": gaps, "out": str(out),
                      "next": "run work-orders/astra.json and opus.json on those seats, save replies to raw/astra.json and raw/opus.json, "
                              "have Compass fill benchmarks.csv, then run: ignition.py process"}, indent=2))


# ------------------------------------------------------------------ validation
def validate_output(raw, bp):
    problems = []
    if not isinstance(raw, dict) or not isinstance(raw.get("divisions"), list):
        return ["output is not an object with a 'divisions' list"]
    task_ids = {t["task_id"] for t in bp["tasks"]}
    line_ids = {l["line_id"] for d in bp["divisions"] for l in d["price_lines"]}
    for d in raw["divisions"]:
        for p in d.get("pert") or []:
            tid = p.get("task_id")
            if tid not in task_ids:
                problems.append(f"unknown task_id {tid!r}")
                continue
            o, m, pe = p.get("optimistic"), p.get("most_likely"), p.get("pessimistic")
            if not all(isinstance(v, (int, float)) and v >= 0 for v in (o, m, pe)) or not o <= m <= pe:
                problems.append(f"{tid}: need numbers with optimistic <= most_likely <= pessimistic (got {o}, {m}, {pe})")
        for pr in d.get("prices") or []:
            lid = pr.get("line_id")
            if lid not in line_ids:
                problems.append(f"unknown line_id {lid!r}")
            elif not isinstance(pr.get("unit_price"), (int, float)) or pr["unit_price"] < 0:
                problems.append(f"{lid}: unit_price must be a non-negative number")
    return problems


SEAT_CLI = {   # logged-in CLIs: no API key is read, stored or passed by this script
    "opus": lambda model, last: ["claude", "-p", "--model", model, "--output-format", "text", "--max-turns", "1"],
    "astra": lambda model, last: ["codex", "exec", "-m", model, "--skip-git-repo-check", "-s", "read-only",
                                  "--output-last-message", str(last), "-"]}


def extract_json(text):
    """The outermost JSON object in a model reply (fences and chatter tolerated), or None."""
    text = re.sub(r"```(?:json)?", "", text or "")
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        return obj
    return None


SEAT_PROMPT_VERSION = "1"   # bump when seat_prompt changes, so cached answers are not reused against a new prompt


def seat_prompt(order, problems=None):
    fix = ("\nYour previous reply failed validation. Fix exactly these and return the whole object again:\n- "
           + "\n- ".join(problems)) if problems else ""
    return ("You are a seat in the NTXP Project Ignition procedure. Answer the work order below independently.\n"
            "Reply with ONE JSON object that follows work_order.output_contract and nothing else: no prose, no code fences.\n"
            "Use only task_id and line_id values that appear in the work order. Never invent quantities, dates or sources; "
            "use null when unknown. Mark a division not_applicable only when nothing in its packet needs work.\n"
            + fix + "\n\nWORK ORDER:\n" + json.dumps(order, indent=1))


def order_key(order, mid):
    """Cache key: a seat's answer is reused only while its work order, model and prompt are unchanged."""
    blob = json.dumps({"order": order, "model": mid, "prompt": SEAT_PROMPT_VERSION}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def run_seat(seat, order, bp, out, timeout):
    """One seat's answer, validated and saved. Safe to run concurrently: each seat writes only its own files."""
    mid = SEATS[seat]["model"]
    problems, raw, attempt, t0, cmd = None, None, 0, dt.datetime.now(dt.timezone.utc), []
    for attempt in (1, 2):
        last = out / "raw" / f"{seat}.last.txt"
        cmd = SEAT_CLI[seat](mid, last)
        log(f"{seat}: {cmd[0]} {mid} attempt {attempt}")
        t0 = dt.datetime.now(dt.timezone.utc)
        r = subprocess.run(cmd, input=seat_prompt(order, problems), capture_output=True, text=True, timeout=timeout)
        text = last.read_text() if seat == "astra" and last.exists() else r.stdout
        if r.returncode != 0 and not text.strip():
            raise SystemExit(f"{seat}: {cmd[0]} failed ({r.returncode}): {r.stderr.strip()[:400]}")
        raw = extract_json(text)
        problems = [f"reply contained no JSON object (CLI said: {' '.join(text.split())[:200]!r})"] if raw is None else validate_output(raw, bp)
        if not problems:
            break
        if raw is None and len(text) < 400:     # a short non-JSON reply is an error message (expired login), not a bad answer
            break
    raw = raw if isinstance(raw, dict) else {}
    raw.update(seat=seat, model=mid, generated_at=t0.isoformat(timespec="seconds"),
               run={"via": cmd[0], "attempts": attempt, "validation_problems": problems or [], "cached": False})
    return raw, problems or []


def cmd_seats(args):
    project, model, sec, facts = load_project(args.project)
    out = model / "ignition"
    bp = load_json(out / "blueprint.json")
    if not bp:
        sys.exit("no blueprint.json: run 'ignition.py blueprint' first")
    (out / "raw").mkdir(exist_ok=True)
    seats = [args.only] if args.only else list(SEATS)
    todo = []
    for seat in seats:
        order = load_json(out / "work-orders" / f"{seat}.json")
        if order is None:
            sys.exit(f"missing work order for {seat}")
        if any(b.split()[0] in json.dumps(order.get("seat", "")).lower() for b in BLOCKED_SEATS):
            sys.exit(f"{seat}: refusing to send; seat is blocked for owner/bid/pricing content")
        key = order_key(order, SEATS[seat]["model"])
        cached = None if args.no_cache else load_json(out / "raw" / f"{seat}.cache.json")
        if cached and cached.get("key") == key and cached.get("raw"):
            cached["raw"].setdefault("run", {})["cached"] = True
            write_json(out / "raw" / f"{seat}.json", cached["raw"])
            log(f"{seat}: cache hit, reused the answer for this work order (no model call)")
            continue
        todo.append((seat, order, key))
    # Seats are independent, so run them at the same time: wall-clock time is the slowest seat, not the sum.
    with ThreadPoolExecutor(max_workers=max(1, len(todo))) as pool:
        futures = {pool.submit(run_seat, seat, order, bp, out, args.timeout): (seat, key) for seat, order, key in todo}
        for fut in as_completed(futures):
            seat, key = futures[fut]
            raw, problems = fut.result()
            write_json(out / "raw" / f"{seat}.json", raw)
            if not problems:      # only a clean answer is worth caching
                write_json(out / "raw" / f"{seat}.cache.json", {"key": key, "raw": raw})
            log(f"{seat}: saved raw/{seat}.json ({len(raw.get('divisions') or [])} divisions, {len(problems)} validation problems)")


def good_items(raw):
    """Rows that passed validation, indexed for comparison."""
    pert, prices, itb = {}, {}, {}
    for d in (raw or {}).get("divisions", []):
        for p in d.get("pert") or []:
            try:
                if p["optimistic"] <= p["most_likely"] <= p["pessimistic"]:
                    pert[p["task_id"]] = p
            except (KeyError, TypeError):
                pass
        for pr in d.get("prices") or []:
            if isinstance(pr.get("unit_price"), (int, float)) and pr["unit_price"] >= 0 and pr.get("line_id"):
                prices[pr["line_id"]] = pr
        if d.get("itb"):
            itb[d["division"]] = d["itb"]
    return pert, prices, itb


# ------------------------------------------------------------------ PERT
def pert_stats(p):
    e = (p["optimistic"] + 4 * p["most_likely"] + p["pessimistic"]) / 6
    return e, (p["pessimistic"] - p["optimistic"]) / 6


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def na_divisions(bp, raws):
    """Divisions every answering seat marked not applicable."""
    na = set()
    for d in bp["divisions"]:
        votes = [any(x.get("division") == d["division"] and x.get("not_applicable") for x in raw.get("divisions", []))
                 for raw in raws.values()]
        if votes and all(votes):
            na.add(d["division"])
    return na


def run_pert(bp, items, jev, na=frozenset()):
    out, notes = {}, []
    for t in bp["tasks"]:
        tid = t["task_id"]
        if t.get("division") in na:
            out[tid] = {"task_id": tid, "e": 0.0, "sd": 0.0, "decision": "not_applicable", "stance": None}
            continue
        got = {s: items[s][0].get(tid) for s in items if items[s][0].get(tid)}
        if not got:
            notes.append(f"{tid}: no duration from any seat")
            out[tid] = {"task_id": tid, "e": None, "sd": None, "decision": "no_data", "stance": None}
            continue
        stats = {s: pert_stats(p) for s, p in got.items()}
        if len(stats) == 2:
            (ea, sa), (eo, so) = stats["astra"], stats["opus"]
            mean = (ea + eo) / 2
            rel = abs(ea - eo) / mean if mean else 0
            stance = jev.stance("pert_stance", rel, PERT_AGREE, PERT_MINOR, f"{tid} duration")
            sd = math.sqrt((sa ** 2 + so ** 2) / 2 + ((ea - eo) / 2) ** 2)
            if stance == "divergent":
                e, decision = max(ea, eo), "escalate_use_higher"
                notes.append(f"{tid}: seats diverge ({ea:.1f} vs {eo:.1f} working days); using the higher value until the PM reviews")
            else:
                e, decision = mean, "accept_mean"
            out[tid] = {"task_id": tid, "e": e, "sd": sd, "decision": decision, "stance": stance,
                        "by_seat": {s: {"e": round(v[0], 2), "sd": round(v[1], 2)} for s, v in stats.items()}}
        else:
            s, (e, sd) = next(iter(stats.items()))
            out[tid] = {"task_id": tid, "e": e, "sd": sd * 1.25, "decision": "single_source", "stance": "single",
                        "by_seat": {s: {"e": round(e, 2), "sd": round(sd, 2)}}}
            notes.append(f"{tid}: only {s} gave a duration; spread widened 25%")
    return out, notes


def run_cpm(bp, pert):
    finish, via = {}, {}
    byid = {t["task_id"]: t for t in bp["tasks"]}
    missing = [tid for tid, p in pert.items() if p.get("decision") == "no_data"]
    for t in bp["tasks"]:   # tasks are emitted in dependency order
        preds = [p for p in t["predecessors"] if p in finish]
        start = max((finish[p] for p in preds), default=0.0)
        via[t["task_id"]] = max(preds, key=lambda p: finish[p]) if preds else None
        e = (pert.get(t["task_id"]) or {}).get("e")
        finish[t["task_id"]] = start + (e or 0.0)
    end = max(finish, key=finish.get) if finish else None
    path, cur = [], end
    while cur:
        path.append(cur)
        cur = via[cur]
    path.reverse()
    total = finish.get(end, 0.0)
    var = sum(((pert.get(t) or {}).get("sd") or 0) ** 2 for t in path)
    sd = math.sqrt(var)
    res = {"status": "complete", "critical_path": path, "expected_working_days": round(total, 1),
           "sd_working_days": round(sd, 1), "expected_calendar_days": round(total * 7 / 5),
           "p80_working_days": round(total + Z80 * sd, 1), "p80_calendar_days": round((total + Z80 * sd) * 7 / 5)}
    tgt = bp.get("target_days")
    if tgt and sd > 0:
        res["target_working_days"] = round(tgt, 1)
        res["p_finish_by_target"] = round(normal_cdf((tgt - total) / sd), 3)
    if missing:
        # A task with no usable duration is not a zero-day task: withhold the roll-up.
        res = {"status": "incomplete", "missing_tasks": missing,
               "note": "No expected or P80 duration is published until every applicable task has a usable duration.",
               "lower_bound_working_days": round(total, 1), "critical_path": [],
               "expected_working_days": None, "expected_calendar_days": None,
               "p80_working_days": None, "p80_calendar_days": None}
    return res, byid


# ------------------------------------------------------------------ prices
def freshness(price_date, now):
    if not price_date:
        return 0.4, None
    try:
        age = (now - dt.date.fromisoformat(str(price_date)[:10])).days
    except ValueError:
        return 0.4, None
    f = 1.0 if age <= 90 else 0.9 if age <= 180 else 0.75 if age <= 365 else 0.5
    return f, age


def documented(p):
    return bool(p and p.get("source") and p.get("price_date") and p.get("price_basis") != "model_estimate")


def run_prices(bp, items, jev, now, na=frozenset()):
    lines, flags = [], []
    for d in bp["divisions"]:
        if d["division"] in na:
            continue
        for l in d["price_lines"]:
            lid = l["line_id"]
            got = {s: items[s][1][lid] for s in items if lid in items[s][1]}
            rec = {"line_id": lid, "division": d["division"], "description": l["description"], "uom": l["uom"],
                   "quantity": l["quantity"], "anchor": l["anchor"], "decision": None, "unit_price": None,
                   "confidence": None, "valid_through": None, "price_date": None, "stance": None, "reason": ""}
            qs = [p.get("quantity") for p in got.values() if isinstance(p.get("quantity"), (int, float))]
            if rec["quantity"] is None and qs:
                rec["quantity"], rec["quantity_source"] = sum(qs) / len(qs), "seat_estimate"
                flags.append(f"{lid}: quantity is a model estimate, verify against the drawings")
            elif rec["quantity"] is not None:
                rec["quantity_source"] = l["quantity_source"]
            chosen, stance = None, None
            if l["anchor"] is not None and l["joc_line"]:
                rec.update(decision="contract_price", unit_price=l["anchor"], reason="JOC contract unit price is never overridden")
                rec["confidence"], rec["stance"] = 1.0, "contract"
                if l.get("anchor_source") == "upb_unit_price":
                    rec["confidence"] = 0.9
                    rec["reason"] += "; taken from the unit-price-book line, so the adjusted contract rate (coefficient) is not applied"
                    flags.append(f"{lid}: contract price is the UPB base rate; confirm the adjusted rate with the PM")
                lines.append(rec)
                continue
            if len(got) == 2:
                a, o = got["astra"]["unit_price"], got["opus"]["unit_price"]
                mean = (a + o) / 2
                rel = abs(a - o) / mean if mean else 0
                stance = jev.stance("price_stance", rel, PRICE_AGREE, PRICE_MINOR, f"{lid} unit price")
                da, do = documented(got["astra"]), documented(got["opus"])
                if stance == "agree":
                    rec.update(decision="accept_mean", unit_price=mean, reason=f"seats within {rel:.1%}")
                elif da != do:
                    pick = "astra" if da else "opus"
                    rec.update(decision="accept_documented", unit_price=got[pick]["unit_price"],
                               reason=f"only {pick} cites a dated source ({rel:.1%} apart)")
                    chosen = got[pick]
                elif stance == "minor":
                    rec.update(decision="accept_mean", unit_price=mean, reason=f"minor gap {rel:.1%}, neither or both documented")
                elif l["anchor"] is not None:
                    pick = min(got, key=lambda s: abs(got[s]["unit_price"] - l["anchor"]))
                    rec.update(decision="accept_nearest_anchor", unit_price=got[pick]["unit_price"],
                               reason=f"seats {rel:.1%} apart; took the one nearest the existing CPR rate")
                    chosen = got[pick]
                    flags.append(f"{lid}: seats diverge {rel:.1%}; anchored to existing rate, PM to confirm")
                else:
                    rec.update(decision="escalate", unit_price=mean, reason=f"seats {rel:.1%} apart, no anchor or citation")
                    flags.append(f"{lid}: seats diverge {rel:.1%} with no citation or anchor; mean is provisional")
                if chosen is None:
                    chosen = {"price_date": min((p.get("price_date") for p in got.values() if p.get("price_date")), default=None),
                              "price_basis": min((p.get("price_basis") or "model_estimate" for p in got.values()),
                                                 key=lambda b: BASIS_WEIGHT.get(b, 0.5))}
            elif len(got) == 1:
                s, chosen = next(iter(got.items()))
                stance = "single"
                rec.update(decision="single_source", unit_price=chosen["unit_price"], reason=f"only {s} priced this line")
                jev.judge("price_stance", f"Do the two models agree on {lid} unit price?", {"seats": [s]},
                          ["agree", "minor", "divergent", "single"], "single", "only one seat priced the line")
                flags.append(f"{lid}: priced by {s} only")
            else:
                rec.update(decision="no_price", reason="no seat priced this line")
                flags.append(f"{lid}: no price from either seat")
                lines.append(rec)
                continue
            f, age = freshness(chosen.get("price_date"), now)
            conf = f * BASIS_WEIGHT.get(chosen.get("price_basis"), 0.5) * AGREE_WEIGHT[stance]
            rec["confidence"], rec["stance"] = round(min(conf, 1.0), 3), stance
            rec["price_date"], rec["age_days"] = chosen.get("price_date"), age
            if chosen.get("price_date"):
                try:
                    rec["valid_through"] = (dt.date.fromisoformat(str(chosen["price_date"])[:10])
                                            + dt.timedelta(days=SHELF_LIFE_DAYS.get(d["division"], DEFAULT_SHELF_LIFE))).isoformat()
                except ValueError:
                    pass
            lines.append(rec)
    for r in lines:
        if r["unit_price"] is not None and isinstance(r["quantity"], (int, float)):
            r["extended"] = round(r["unit_price"] * r["quantity"], 2)
            band = (1 - (r["confidence"] or 0)) * 0.5
            r["low"], r["high"] = round(r["extended"] * (1 - band), 2), round(r["extended"] * (1 + band), 2)
        else:
            r["extended"] = None
            if r["unit_price"] is not None:
                flags.append(f"{r['line_id']}: priced but unquantified, so no extended cost")
    by_div = {}
    for r in lines:
        if r["extended"] is not None:
            b = by_div.setdefault(r["division"], {"division": r["division"], "extended": 0.0, "low": 0.0, "high": 0.0})
            b["extended"] += r["extended"]
            b["low"] += r["low"]
            b["high"] += r["high"]
    total = {"extended": round(sum(b["extended"] for b in by_div.values()), 2),
             "low": round(sum(b["low"] for b in by_div.values()), 2),
             "high": round(sum(b["high"] for b in by_div.values()), 2)}
    return lines, {k: {x: round(y, 2) if isinstance(y, float) else y for x, y in v.items()} for k, v in by_div.items()}, total, flags


# ------------------------------------------------------------------ $/SF sanity
def load_benchmarks(path):
    if not path or not Path(path).is_file():
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r.get("source") and (r.get("mid_psf") or r.get("low_psf"))]


def state_of(location):
    m = re.search(r",\s*([A-Z]{2})\b", location or "")
    return m.group(1) if m else ""


def pick_benchmark(rows, facts, scope="total"):
    st, loc = state_of(facts["location"]), (facts["location"] or "").lower()
    bt = (facts["market_sector"] or facts["occupancy_type"] or "").lower()

    def fits(r):
        rb = (r.get("building_type") or "").lower()
        rp = (r.get("project_type") or "").lower()
        return (r.get("scope") or "total") == scope and (not bt or not rb or rb in bt or bt in rb) \
            and (not rp or rp == (facts["project_type"] or "").lower())

    def rank(r):
        rg, rs = (r.get("region") or "").lower(), (r.get("state") or "").upper()
        level = 3 if rg and rg in loc else 2 if rs and rs == st else 1 if (rg in ("national", "us", "usa", "")) else 0
        try:
            yr = int(r.get("year") or 0)
        except ValueError:
            yr = 0
        return (level, yr)
    cands = [r for r in rows if fits(r)]
    cands = [r for r in cands if rank(r)[0] > 0]
    return max(cands, key=rank) if cands else None


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def run_sanity(facts, total, by_div, benches, jev, now, markup_pct):
    out = {"checked": False}
    sf, sf_basis = fnum(facts.get("gross_sf")), "gross_sf"
    if not sf:      # a renovation priced per SF of the area being renovated is how renovation benchmarks are quoted
        sf, sf_basis = fnum(facts.get("work_area_sf")), "work_area_sf"
    if not sf:
        out["verdict"] = jev.judge("sanity_psf", "Is the estimate in line with public $/SF?", {"reason": "no gross SF"},
                                   ["within_band", "below_band", "above_band", "no_benchmark", "no_sf"], "no_sf",
                                   "gross_sf is not in the project record")
        out["note"] = "Provide gross SF to enable the check."
        return out
    direct = total["extended"]
    all_in = direct * (1 + markup_pct) if markup_pct else direct
    psf = all_in / sf
    out.update(gross_sf=sf, sf_basis=sf_basis, direct_cost=direct, markup_pct=markup_pct, estimate_psf=round(psf, 2),
               basis="direct cost" + (f" + {markup_pct:.0%} markups" if markup_pct else " only (no markups applied)"))
    b = pick_benchmark(benches, facts)
    if not b:
        out["verdict"] = jev.judge("sanity_psf", "Is the estimate in line with public $/SF?", {"psf": round(psf, 2)},
                                   ["within_band", "below_band", "above_band", "no_benchmark", "no_sf"], "no_benchmark",
                                   "no sourced benchmark row matches this building type and location")
        out["note"] = "Have Compass fill benchmarks.csv from work-orders/compass.json."
        return out
    lo, mid, hi = (fnum(b.get("low_psf")), fnum(b.get("mid_psf")), fnum(b.get("high_psf")))
    lo = lo if lo is not None else (mid * 0.8 if mid else None)
    hi = hi if hi is not None else (mid * 1.2 if mid else None)
    ans = "below_band" if psf < lo else "above_band" if psf > hi else "within_band"
    out["checked"] = True
    out["benchmark"] = {k: b.get(k) for k in BENCH_COLS}
    out["band_psf"] = {"low": lo, "mid": mid, "high": hi}
    out["verdict"] = jev.judge("sanity_psf", "Is the estimate in line with public $/SF?",
                               {"psf": round(psf, 2), "band": [lo, hi]},
                               ["within_band", "below_band", "above_band", "no_benchmark", "no_sf"], ans,
                               f"${psf:,.0f}/SF against ${lo:,.0f}-${hi:,.0f}/SF ({b.get('source')})")
    caveats = []
    if sf_basis == "work_area_sf":
        caveats.append("SF is the stated renovated work area, not the building's gross SF; check it matches the benchmark's basis")
    if (b.get("basis") or "").lower() not in ("", "hard_cost", "direct"):
        caveats.append(f"benchmark basis is '{b.get('basis')}', not direct hard cost")
    try:
        if now.year - int(b.get("year") or now.year) >= 2:
            caveats.append(f"benchmark year {b.get('year')} is {now.year - int(b['year'])} years old; escalate before relying on it")
    except ValueError:
        pass
    out["caveats"] = caveats
    # division share check where division-level benchmarks exist
    shares = []
    for d, v in by_div.items():
        db = pick_benchmark(benches, facts, scope=d)
        if db and fnum(db.get("mid_psf")):
            dpsf = v["extended"] / sf
            dlo = fnum(db.get("low_psf")) or fnum(db["mid_psf"]) * 0.8
            dhi = fnum(db.get("high_psf")) or fnum(db["mid_psf"]) * 1.2
            a = "below_band" if dpsf < dlo else "above_band" if dpsf > dhi else "within_band"
            jev.judge("sanity_psf", f"Is division {d} in line with public $/SF?", {"psf": round(dpsf, 2), "band": [dlo, dhi]},
                      ["within_band", "below_band", "above_band", "no_benchmark", "no_sf"], a, f"division {d} ${dpsf:,.2f}/SF")
            shares.append({"division": d, "psf": round(dpsf, 2), "band": [dlo, dhi], "verdict": a, "source": db.get("source")})
    out["divisions"] = shares
    return out


def cmd_process(args):
    project, model, sec, facts = load_project(args.project)
    out = model / "ignition"
    bp = load_json(out / "blueprint.json")
    if not bp:
        sys.exit("no blueprint.json: run 'ignition.py blueprint' first")
    now = today(args)
    items, problems, present, raws = {}, [], [], {}
    for seat in SEATS:
        path = Path(getattr(args, seat) or out / "raw" / f"{seat}.json")
        raw = load_json(path)
        if raw is None:
            continue
        pr = validate_output(raw, bp)
        problems += [f"{seat}: {p}" for p in pr]
        items[seat] = good_items(raw)
        raws[seat] = raw
        present.append(seat)
    if not items:
        sys.exit("no seat output found: save replies to model/ignition/raw/astra.json and opus.json")
    jev = Jev()
    na = na_divisions(bp, raws)
    for d in sorted(na):
        jev.judge("division_applicability", f"Does division {d} carry work on this project?", {"seats": present},
                  ["applicable", "not_applicable"], "not_applicable", "every seat that answered marked it not applicable")
    pert, pert_notes = run_pert(bp, items, jev, na)
    cpm, _ = run_cpm(bp, pert)
    lines, by_div, total, flags = run_prices(bp, items, jev, now, na)
    benches = load_benchmarks(args.benchmarks or out / "benchmarks.csv")
    sanity = run_sanity(bp["project"], total, by_div, benches, jev, now, args.markup_pct)
    needs = problems + pert_notes + flags
    if cpm["status"] == "incomplete":
        needs.append("schedule roll-up withheld: no usable duration for " + ", ".join(cpm["missing_tasks"]))
    if sanity.get("verdict") in ("below_band", "above_band"):
        needs.append(f"$/SF check: {sanity['verdict']} ({sanity['estimate_psf']}/SF vs {sanity['band_psf']})")
    uncovered = [d["division"] for d in bp["divisions"] if d["division"] not in na
                 if not any(l["division"] == d["division"] and l["unit_price"] is not None for l in lines)]
    if uncovered:
        needs.append("no price for any line in division(s): " + ", ".join(uncovered))
    processed = {"stage": "processed", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                 "status": "draft_pending_pm_approval", "as_of": now.isoformat(), "seats_present": present,
                 "not_applicable_divisions": sorted(na),
                 "pert": {"tasks": list(pert.values()), "schedule": cpm},
                 "prices": {"lines": lines, "by_division": by_div, "totals": total},
                 "sanity": sanity, "needs_human_review": needs,
                 "judgment_counts": {k: sum(1 for j in jev.log if j["kind"] == k) for k in {j["kind"] for j in jev.log}}}
    write_json(out / "processed.json", processed)
    (out / "jev-judgments.jsonl").write_text("\n".join(json.dumps(j) for j in jev.log) + "\n")
    write_json(out / "benchmark-template.json", {"columns": BENCH_COLS})
    print(json.dumps({"status": "processed", "seats": present, "schedule": cpm["status"], "expected_calendar_days": cpm["expected_calendar_days"],
                      "p80_calendar_days": cpm["p80_calendar_days"], "direct_cost": total["extended"],
                      "psf_verdict": sanity.get("verdict"), "needs_human_review": len(needs),
                      "out": str(out / "processed.json")}, indent=2))


# ------------------------------------------------------------------ ITB pages
def merge_itb(items):
    def union(key):
        seen, res = set(), []
        for seat in ("opus", "astra"):
            for x in (items.get(seat) or {}).get(key, []) or []:
                k = re.sub(r"\W+", " ", str(x).lower()).strip()
                if k not in seen:
                    seen.add(k)
                    res.append(str(x))
        return res
    narr = (items.get("opus") or {}).get("scope_narrative") or (items.get("astra") or {}).get("scope_narrative") or ""
    return {"scope_narrative": narr, **{k: union(k) for k in ("inclusions", "exclusions", "clarifications", "required_submittals", "alternates")}}


def esc(x):
    return html.escape(str(x if x is not None else ""))


def bar(frac, color="#1f4e8c", width=180):
    w = max(2, int(width * max(0.0, min(1.0, frac))))
    return (f'<table cellspacing="0" cellpadding="0"><tr><td style="background:{color};width:{w}px;height:8px"></td>'
            f'<td style="background:#e3e8f0;width:{width - w}px;height:8px"></td></tr></table>')


def bullets(items, empty="None stated."):
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>" if items else f"<p><i>{esc(empty)}</i></p>"


def header(title, sub):
    return (f'<table style="width:100%" cellspacing="0" cellpadding="8"><tr><td align="center" style="background:#17304f;color:#ffffff;width:100%">'
            f'<b style="font-size:17pt">{esc(title)}</b><br/><span style="font-size:9pt">{esc(sub)}</span></td></tr>'
            f'<tr><td style="background:#bd9440;height:3px"></td></tr></table>')


def itb_page(d, merged, task, proj, bid_dates, max_lines, max_days):
    dur = (task or {}).get("e")
    rows = "".join(f"<tr><td>{esc(l['description'])}</td><td align='right'>{esc(l['quantity']) if l['quantity'] is not None else 'TBD'}</td>"
                   f"<td>{esc(l['uom'])}</td></tr>" for l in d["price_lines"])
    sheets = ", ".join(esc(s["sheet_no"]) for s in d["sheets"]) or "see drawing index"
    specs = ", ".join(esc(s["section"]) for s in d["spec_sections"]) or "see specifications"
    refs = f"<li><b>Specification sections:</b> {specs}</li><li><b>Drawing sheets:</b> {sheets}</li>"
    if dur:
        refs += f"<li><b>Anticipated duration:</b> about {dur:.0f} working days</li>"
    gauges = f"<p>Line items ({len(d['price_lines'])}): {bar(len(d['price_lines']) / max(max_lines, 1))}</p>"
    if dur:
        gauges += f"<p>Duration ({dur:.0f} working days): {bar(dur / max(max_days, 1), '#bd9440')}</p>"
    return (header(f"INVITATION TO BID: DIVISION {d['division']}", f"{d['label']}  |  {proj['title']}")
            + '<table style="width:100%" cellspacing="0" cellpadding="4"><tr>'
            f"<td><b>PROJECT:</b> {esc(proj['title'])}</td><td><b>OWNER:</b> {esc(proj['owner'] or 'TBD')}</td></tr><tr>"
            f"<td><b>LOCATION:</b> {esc(proj['location'] or 'TBD')}</td>"
            f"<td><b>BID DUE:</b> {esc(bid_dates.get('NTXP Sub Bids Due', 'To be set by the PM'))}</td></tr></table>"
            '<p style="background:#fff3cd;padding:4px"><b>DRAFT:</b> pending PM approval. Not issued.</p>'
            "<h3>SCOPE OVERVIEW</h3>" + (f"<p>{esc(merged['scope_narrative'])}</p>" if merged["scope_narrative"] else "<p><i>Narrative pending.</i></p>")
            + "<h3>INCLUDED IN YOUR BID</h3>" + bullets(merged["inclusions"])
            + "<h3>EXCLUDED</h3>" + bullets(merged["exclusions"])
            + "<h3>CLARIFICATIONS</h3>" + bullets(merged["clarifications"])
            + "<h3>QUANTITIES (verify against the drawings)</h3>"
            f'<table style="width:100%" border="1" cellspacing="0" cellpadding="3"><tr style="background:#eef2f8"><td><b>ITEM</b></td>'
            f'<td align="right"><b>QTY</b></td><td><b>UNIT</b></td></tr>{rows}</table>'
            f"<h3>REFERENCES</h3><ul>{refs}</ul>"
            "<h3>REQUIRED SUBMITTALS</h3>" + bullets(merged["required_submittals"])
            + ("<h3>ALTERNATES</h3>" + bullets(merged["alternates"]) if merged["alternates"] else "")
            + "<h3>HOW THIS PACKAGE COMPARES</h3>" + gauges)


def cmd_itb(args):
    project, model, sec, facts = load_project(args.project)
    out = model / "ignition"
    bp, pr = load_json(out / "blueprint.json"), load_json(out / "processed.json", {})
    if not bp:
        sys.exit("no blueprint.json: run 'ignition.py blueprint' first")
    seat_items = {}
    for seat in SEATS:
        raw = load_json(out / "raw" / f"{seat}.json")
        if raw:
            seat_items[seat] = good_items(raw)[2]
    pert = {t["task_id"]: t for t in (pr.get("pert") or {}).get("tasks", [])}
    bid_dates = {k.get("label"): k.get("date") for k in facts["key_dates"] if isinstance(k, dict)}
    max_lines = max((len(d["price_lines"]) for d in bp["divisions"]), default=1)
    max_days = max((t.get("e") or 0 for t in pert.values()), default=1)
    na = set((pr or {}).get("not_applicable_divisions", []))
    pages = []
    for d in bp["divisions"]:
        if d["division"] in na:
            continue
        merged = merge_itb({s: seat_items[s].get(d["division"]) for s in seat_items})
        pages.append(itb_page(d, merged, pert.get(f"T-{d['division']}"), bp["project"], bid_dates, max_lines, max_days))
    idx = header("BID PACKAGE INDEX", f"{bp['project']['title']}  |  {len(pages)} divisions") + "<ul>" + "".join(
        f"<li><b>Division {esc(d['division'])}</b> {esc(d['label'])}: {len(d['price_lines'])} line item(s)</li>" for d in bp["divisions"] if d["division"] not in na) + "</ul>"
    body = idx + "".join(f'<div style="page-break-before:always">{p}</div>' for p in pages)
    css = "body{font-family:Helvetica,Arial,sans-serif;font-size:10pt;color:#1d2330}h3{color:#17304f;border-bottom:1px solid #bd9440}"
    doc = f"<html><head><meta charset='utf-8'><title>ITB packages</title><style>@page{{size:8.5in 11in;margin:0.6in}}{css}</style></head><body>{body}</body></html>"
    (out / "itb").mkdir(parents=True, exist_ok=True)
    (out / "itb" / "itb-packages.html").write_text(doc)
    res = {"status": "itb_ready", "packages": len(pages), "html": str(out / "itb" / "itb-packages.html")}
    if args.pdf:
        try:
            import pymupdf as fitz
        except ImportError:
            try:
                import fitz
            except ImportError:
                fitz = None
        if fitz is None:
            res["pdf"] = "skipped: PyMuPDF not installed"
        else:
            merged_pdf = fitz.open()
            for part in [idx] + pages:                    # one Story per package: page breaks are exact
                tmp = out / "itb" / "_part.pdf"
                story = fitz.Story(html=part, user_css=css)
                writer = fitz.DocumentWriter(str(tmp))
                mediabox = fitz.paper_rect("letter")
                where = mediabox + (43, 43, -43, -43)
                more, n = 1, 0
                while more and n < 20:
                    n += 1
                    dev = writer.begin_page(mediabox)
                    more, _ = story.place(where)
                    story.draw(dev)
                    writer.end_page()
                writer.close()
                with fitz.open(str(tmp)) as piece:
                    merged_pdf.insert_pdf(piece)
                tmp.unlink()
            merged_pdf.save(str(out / "itb" / "itb-packages.pdf"))
            res["pdf"] = str(out / "itb" / "itb-packages.pdf")
    # internal summary (never sent to subs)
    if pr:
        s, c, p = pr["pert"]["schedule"], pr["prices"]["totals"], pr["sanity"]
        rows = "".join(f"<li>{esc(n)}</li>" for n in pr["needs_human_review"][:60])
        internal = (f"<html><head><meta charset='utf-8'><style>@page{{size:8.5in 11in;margin:0.6in}}{css}</style></head><body>"
                    + header("PROJECT IGNITION SUMMARY", "INTERNAL ONLY: contains pricing")
                    + ("<h3>SCHEDULE</h3><ul><li><b>Roll-up withheld:</b> no usable duration for " + esc(", ".join(s.get("missing_tasks", []))) + "</li></ul><ul>" if s.get("status") == "incomplete" else
                       f"<h3>SCHEDULE</h3><ul><li><b>Expected:</b> {s['expected_calendar_days']} calendar days</li><li><b>P80:</b> {s['p80_calendar_days']} calendar days</li>")
                    + (f"<li><b>Chance of meeting the stated duration:</b> {s['p_finish_by_target']:.0%}</li>" if "p_finish_by_target" in s else "")
                    + (f"<li><b>Critical path:</b> {esc(' > '.join(s['critical_path']))}</li></ul>" if s.get("status") != "incomplete" else "</ul>")
                    + f"<h3>COST (DRAFT)</h3><ul><li><b>Direct cost:</b> ${c['extended']:,.0f}</li><li><b>Range:</b> ${c['low']:,.0f} to ${c['high']:,.0f}</li>"
                    + f"<li><b>$/SF check:</b> {esc(p.get('verdict'))}" + (f" at ${p['estimate_psf']:,.0f}/SF" if p.get("estimate_psf") else "") + "</li></ul>"
                    + f"<h3>NEEDS PM REVIEW ({len(pr['needs_human_review'])})</h3><ul>{rows}</ul></body></html>")
        (out / "itb" / "ignition-summary.html").write_text(internal)
        res["summary"] = str(out / "itb" / "ignition-summary.html")
    print(json.dumps(res, indent=2))


# ------------------------------------------------------------------ selftest
def selftest():
    tmp = Path(tempfile.mkdtemp(prefix="ignition-"))
    sec = tmp / "model" / "sections"
    sec.mkdir(parents=True)
    write_json(sec / "project_identity.json", {"section": "project_identity", "title": "Selftest Clinic", "owner": "Test ISD",
               "location": "Dallas, TX", "market_sector": "healthcare", "project_type": "renovation",
               "building": {"gross_sf": 10000}, "key_dates": [{"label": "NTXP Sub Bids Due", "date": "2026-11-05"}]})
    write_json(sec / "scope.json", {"section": "scope", "items": [
        {"scope_item_id": "S1", "csi": {"masterformat_division": "09"}, "description": "Replace ceiling tile", "uom": "SF"},
        {"scope_item_id": "S2", "csi": {"masterformat_division": "26"}, "description": "Relocate panelboard", "uom": "EA"},
        {"scope_item_id": "S3", "csi": {"masterformat_division": "09"}, "description": "Paint walls (no takeoff yet)", "uom": "SF"}]})
    write_json(sec / "quantity_takeoff.json", {"section": "quantity_takeoff", "items": [
        {"takeoff_id": "Q1", "scope_item_id": "S1", "csi": {"masterformat_division": "09"}, "description": "ACT ceiling", "quantity": 2000}]})
    write_json(sec / "estimate_sov.json", {"section": "estimate_sov", "cost_lines": [
        {"cost_line_id": "C1", "csi": {"masterformat_division": "26"}, "description": "JOC panel line", "quantity": 1,
         "unit_rate": 5000, "joc_line": True},
        {"cost_line_id": "EL-9", "scope_item_id": "S1", "csi": {"masterformat_division": "09"}, "description": "ACT cost line",
         "quantity": 2000, "unit_rate": 4.9}]})
    write_json(sec / "plans_atlas.json", {"section": "plans_atlas", "sheets": [{"sheet_id": "A-101", "sheet_no": "A-101", "title": "PLAN", "page": 1}],
               "concepts": {"trades": [{"division": "09", "label": "Finishes", "sheet_ids": ["A-101"], "spec_sections": ["09 51 13"]}],
                            "specs": [{"section": "09 51 13", "division": "09", "title": "Acoustical Panel Ceilings"},
                                      {"section": "34 11 00", "division": "34", "title": "Stray mention"}]}})
    ns = argparse.Namespace(project=str(tmp), today="2026-10-14", astra=None, opus=None, benchmarks=None, markup_pct=0.0, pdf=False)
    cmd_blueprint(ns)
    out = tmp / "model" / "ignition"
    bp = load_json(out / "blueprint.json")
    assert {t["task_id"] for t in bp["tasks"]} == {"T-09", "T-26", "T-34", "T-CLOSE"}
    d09 = next(d for d in bp["divisions"] if d["division"] == "09")
    # cost line EL-9 joins takeoff Q1 on scope_item_id (no double count); S3 stays because it has no takeoff
    assert {l["line_id"] for l in d09["price_lines"]} == {"Q1", "S3"}, d09["price_lines"]
    assert next(l for l in d09["price_lines"] if l["line_id"] == "Q1")["anchor"] == 4.9
    assert len(bp["divisions"]) == 3 and next(d for d in bp["divisions"] if d["division"] == "34")["low_evidence"]
    assert not next(d for d in bp["divisions"] if d["division"] == "09")["low_evidence"] and "gross_sf missing" not in " ".join(bp["gaps"])

    def seat(seat, dur09, price09, basis):
        return {"seat": seat, "model": SEATS[seat]["model"], "generated_at": "2026-10-14T00:00:00Z", "divisions": [
            {"division": "09", "pert": [{"task_id": "T-09", "optimistic": dur09[0], "most_likely": dur09[1], "pessimistic": dur09[2], "basis": "fixture"}],
             "prices": [{"line_id": "Q1", "quantity": 2000, "uom": "SF", "unit_price": price09, "price_basis": basis,
                         "price_date": "2026-09-01" if basis != "model_estimate" else None, "source": "fixture" if basis != "model_estimate" else ""}],
             "itb": {"scope_narrative": f"{seat} narrative", "inclusions": ["Remove existing tile", "Install new ACT"], "exclusions": ["Asbestos abatement"],
                     "clarifications": [], "required_submittals": ["Product data"], "alternates": [], "risks": []}},
            {"division": "26", "pert": [{"task_id": "T-26", "optimistic": 2, "most_likely": 3, "pessimistic": 4, "basis": "fixture"}],
             "prices": [{"line_id": "C1", "unit_price": 9999, "price_basis": "book", "price_date": "2026-09-01", "source": "fixture"}],
             "itb": {"scope_narrative": "", "inclusions": ["Relocate panelboard"], "exclusions": [], "clarifications": [],
                     "required_submittals": [], "alternates": [], "risks": []}},
            {"division": "34", "not_applicable": True, "reason": "stray spec mention"},
            {"division": "00", "pert": [{"task_id": "T-CLOSE", "optimistic": 1, "most_likely": 2, "pessimistic": 3, "basis": "fixture"}]},
            {"division": "01", "pert": [{"task_id": "T-NOPE", "optimistic": 5, "most_likely": 2, "pessimistic": 1}]}], "project": {}}
    write_json(out / "raw" / "astra.json", seat("astra", (4, 6, 14), 5.0, "vendor_quote"))
    write_json(out / "raw" / "opus.json", seat("opus", (5, 7, 12), 5.2, "book"))
    with open(out / "benchmarks.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=BENCH_COLS)
        w.writeheader()
        w.writerow({"building_type": "healthcare", "project_type": "renovation", "region": "Dallas, TX", "state": "TX", "year": "2026",
                    "basis": "hard_cost", "scope": "total", "low_psf": "0.5", "mid_psf": "1.0", "high_psf": "1.5",
                    "source": "SELFTEST FIXTURE (not real data)", "source_url": "", "retrieved": "2026-10-14"})
    cmd_process(ns)
    pr = load_json(out / "processed.json")
    t09 = next(t for t in pr["pert"]["tasks"] if t["task_id"] == "T-09")
    assert abs(t09["by_seat"]["astra"]["e"] - 7.0) < 0.01 and abs(t09["by_seat"]["astra"]["sd"] - 10 / 6) < 0.01, t09
    assert t09["stance"] == "agree" and t09["decision"] == "accept_mean", t09
    line = {l["line_id"]: l for l in pr["prices"]["lines"]}
    assert line["Q1"]["decision"] == "accept_mean" and abs(line["Q1"]["unit_price"] - 5.1) < 1e-6, line["Q1"]
    assert line["C1"]["decision"] == "contract_price" and line["C1"]["unit_price"] == 5000, line["C1"]
    assert line["Q1"]["valid_through"] == "2027-02-28" and 0.8 < line["Q1"]["confidence"] <= 1.0, line["Q1"]
    assert pr["sanity"]["checked"] and pr["sanity"]["verdict"] == "above_band", pr["sanity"]   # 15,200 / 10,000 SF vs fixture band
    assert pr["pert"]["schedule"]["status"] == "complete", pr["pert"]["schedule"]
    assert any("T-NOPE" in n for n in pr["needs_human_review"]), "bad task id should be flagged"
    assert pr["not_applicable_divisions"] == ["34"] and not any("34" in n for n in pr["needs_human_review"] if "$/SF" not in n), pr["needs_human_review"]
    assert next(t for t in pr["pert"]["tasks"] if t["task_id"] == "T-34")["decision"] == "not_applicable"
    cmd_itb(ns)
    page = (out / "itb" / "itb-packages.html").read_text()
    assert "DIVISION 34" not in page and "Remove existing tile" in page and "9999" not in page and "5.1" not in page and "5000" not in page, "ITB must not leak prices"
    assert "Select" not in page and (out / "jev-judgments.jsonl").read_text().strip()
    # a task with no usable duration must withhold the roll-up, never count as zero days
    res, _ = run_cpm(bp, {"T-09": {"e": 7.0, "sd": 1.0, "decision": "accept_mean"}, "T-26": {"decision": "no_data", "e": None, "sd": None},
                          "T-34": {"decision": "not_applicable", "e": 0.0, "sd": 0.0}, "T-CLOSE": {"e": 2.0, "sd": 0.5, "decision": "accept_mean"}})
    assert res["status"] == "incomplete" and res["expected_calendar_days"] is None and res["missing_tasks"] == ["T-26"], res
    # structured location and nested JOC rate (schema-valid shapes)
    write_json(sec / "project_identity.json", {"section": "project_identity", "title": "Selftest Clinic", "market_sector": "healthcare", "project_type": "renovation",
               "location": {"city": "Dallas", "state": "TX", "zip": "75201"}, "building": {"gross_sf": 10000}})
    write_json(sec / "estimate_sov.json", {"section": "estimate_sov", "cost_lines": [
        {"cost_line_id": "C1", "csi": {"masterformat_division": "26"}, "description": "JOC panel line", "quantity": 1,
         "unit_rate": {"amount": None}, "joc_line": {"upb_line_number": "26 24 16", "upb_unit_price": {"amount": 4200}}}]})
    cmd_blueprint(ns)
    bp2 = load_json(out / "blueprint.json")
    assert bp2["project"]["location"] == "Dallas, TX"
    c1 = next(l for d in bp2["divisions"] for l in d["price_lines"] if l["line_id"] == "C1")
    assert c1["anchor"] == 4200 and c1["joc_line"] and c1["anchor_source"] == "upb_unit_price", c1
    cmd_process(ns)                       # must not raise on a structured location
    pr2 = load_json(out / "processed.json")
    l2 = next(l for l in pr2["prices"]["lines"] if l["line_id"] == "C1")
    assert l2["decision"] == "contract_price" and l2["unit_price"] == 4200 and l2["confidence"] == 0.9, l2
    assert pr2["sanity"]["checked"] and pr2["sanity"]["sf_basis"] == "gross_sf", pr2["sanity"]
    # no gross SF but a printed work area: the check runs on that basis and says so
    write_json(sec / "project_identity.json", {"section": "project_identity", "title": "Selftest Clinic", "market_sector": "healthcare", "project_type": "renovation",
               "location": {"city": "Dallas", "state": "TX"}, "building": {"work_area_sf": 3000}})
    cmd_blueprint(ns)
    assert any("work area" in g for g in load_json(out / "blueprint.json")["gaps"])
    cmd_process(ns)
    pr3 = load_json(out / "processed.json")["sanity"]
    assert pr3["checked"] and pr3["sf_basis"] == "work_area_sf" and pr3["gross_sf"] == 3000.0, pr3
    assert any("work area" in c for c in pr3.get("caveats", [])), pr3
    assert extract_json('Sure!\n```json\n{"a": {"b": [1, 2]}, "c": "}"}\n```\nDone') == {"a": {"b": [1, 2]}, "c": "}"}
    assert extract_json("no json here") is None and extract_json('{"broken": ') is None
    # seats: cache hit, then a changed work order re-runs, all without a real model call
    calls = []
    real_run = globals()["run_seat"]
    def fake_run(seat, order, bp, out_dir, timeout):
        calls.append(seat)
        return {"seat": seat, "model": SEATS[seat]["model"], "divisions": [], "run": {"validation_problems": []}}, []
    globals()["run_seat"] = fake_run
    try:
        sns = argparse.Namespace(project=str(tmp), only=None, timeout=5, no_cache=False)
        cmd_seats(sns)
        assert sorted(calls) == ["astra", "opus"], calls
        calls.clear(); cmd_seats(sns)
        assert calls == [], "unchanged work orders must come from the cache"
        ob = load_json(tmp / "model" / "ignition" / "work-orders" / "opus.json")
        ob["divisions"] = (ob.get("divisions") or []) + [{"division": "99"}]
        write_json(tmp / "model" / "ignition" / "work-orders" / "opus.json", ob)
        calls.clear(); cmd_seats(sns)
        assert calls == ["opus"], "a changed work order must be asked again"
        calls.clear(); cmd_seats(argparse.Namespace(project=str(tmp), only=None, timeout=5, no_cache=True))
        assert sorted(calls) == ["astra", "opus"], "--no-cache must call every seat"
    finally:
        globals()["run_seat"] = real_run
    print("selftest passed:", tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("blueprint", "process", "itb", "seats"):
        p = sub.add_parser(name)
        p.add_argument("--project", required=True)
        p.add_argument("--today", help="ISO date to treat as today (default: system date).")
        if name == "process":
            p.add_argument("--astra", help="Astra output JSON (default model/ignition/raw/astra.json).")
            p.add_argument("--opus", help="Opus output JSON (default model/ignition/raw/opus.json).")
            p.add_argument("--benchmarks", help="Public $/SF CSV (default model/ignition/benchmarks.csv).")
            p.add_argument("--markup-pct", type=float, default=0.0, help="Markup fraction to add before the $/SF check (e.g. 0.18).")
        if name == "seats":
            p.add_argument("--only", choices=list(SEATS), help="Run one seat only.")
            p.add_argument("--timeout", type=int, default=1500, help="Seconds per seat call (default 1500).")
            p.add_argument("--no-cache", action="store_true", help="Ignore saved answers and call every seat again.")
        if name == "itb":
            p.add_argument("--pdf", action="store_true", help="Also write a letter-size PDF (needs PyMuPDF).")
    sub.add_parser("selftest")
    a = ap.parse_args()
    {"blueprint": cmd_blueprint, "process": cmd_process, "itb": cmd_itb, "seats": cmd_seats}.get(a.cmd, lambda _a: selftest())(a)


if __name__ == "__main__":
    main()
