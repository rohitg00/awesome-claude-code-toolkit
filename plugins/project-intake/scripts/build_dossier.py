#!/usr/bin/env python3
"""
build_dossier.py — deterministic project-intake builder.

Turns a set of construction documents into a project dossier and emits a
handoff.json the construction-doc-intelligence orchestrator consumes.

It does NOT re-implement OCR — it shells out to the mistral-ocr4 skill's client
(`mistral_ocr.py`), which talks to OCR4. Mistral extracts; this script only names
the folder, fans out extraction, writes files, and builds the handoff. Reasoning
(dedup/normalization across docs) is left to the orchestrator's skills.

Pipeline:  resolve+slug project title -> projects/<slug>/ -> per-doc OCR (blocks +
dossier annotation schema, run concurrently) -> _raw/ + extracts/* + index.md ->
handoff.json

Stdlib only (Python 3.10+). Reads MISTRAL_API_KEY from the environment for real
runs; --dry-run needs no key and makes no API calls.
"""

import argparse
import csv
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent
# Reuse the mistral-ocr4 skill's CLI rather than duplicating an HTTP client.
DEFAULT_CLIENT = (
    PLUGIN_DIR.parent / "mistral-ocr4" / "agent-skill" / "scripts" / "mistral_ocr.py"
)
DEFAULT_SCHEMAS = PLUGIN_DIR / "schemas"
HANDOFF_VERSION = "1.0"
MAX_WORKERS = 8

IMAGE_RE = re.compile(r"\.(png|jpe?g|tiff?|webp|avif)(\?|#|$)", re.I)


def log(msg):
    sys.stderr.write(msg + "\n")


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return s or "untitled-project"


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def strip_query(s: str) -> str:
    """Drop query string / fragment so transient signed-URL tokens never leak
    into a doc_id (which must be stable across re-runs)."""
    return s.split("?", 1)[0].split("#", 1)[0]


def base_name(src: str) -> str:
    if is_url(src):
        return strip_query(src).rstrip("/").split("/")[-1] or "document"
    return Path(src).stem or "document"


def doc_id_for(i: int, src: str) -> str:
    """Stable per-document id, shared by the real path and the dry-run plan."""
    return f"doc{i:03d}-{slugify(base_name(src))}"


def run_client(client: Path, args: list[str], label: str) -> dict | None:
    """Invoke mistral_ocr.py <args>; return parsed JSON or None on failure."""
    cmd = [sys.executable, str(client), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as e:  # noqa: BLE001
        log(f"[{label}] client invocation failed: {e}")
        return None
    if proc.returncode != 0:
        log(f"[{label}] client error: {proc.stderr.strip()[:500]}")
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        log(f"[{label}] client returned non-JSON: {proc.stdout[:300]}")
        return None


def ocr_command(source: str, file_id: str | None, schema_text: str | None,
                model: str | None, pages: str | None = None,
                blocks: bool = True, table_format: str | None = "markdown") -> list[str]:
    """Single source of truth for assembling an `ocr` invocation (used by both the
    identity pass and the full dossier pass) so the two never drift."""
    args = ["ocr"]
    if blocks:
        args.append("--include-blocks")
    if table_format:
        args += ["--table-format", table_format]
    if pages is not None:
        args += ["--pages", pages]
    if schema_text is not None:
        args += ["--document-annotation-format", schema_text]
    if model:
        args += ["--model", model]
    if file_id:
        args += ["--file-id", file_id]
    elif is_url(source):
        args += (["--image-url", source] if IMAGE_RE.search(source)
                 else ["--document-url", source])
    return args


def upload_local(client: Path, src: str, label: str) -> str | None:
    up = run_client(client, ["files-upload", "--path", src], label)
    return (up or {}).get("id")


def parse_annotation(env: dict) -> dict:
    ann = env.get("document_annotation")
    if isinstance(ann, str):
        try:
            ann = json.loads(ann)
        except json.JSONDecodeError:
            return {}
    return ann if isinstance(ann, dict) else {}


def dict_list(value) -> list[dict]:
    """Defensively coerce a model-supplied field to a list of dict rows. The
    annotation is model output and may be null, a scalar, or a list of scalars."""
    if not isinstance(value, list):
        return []
    return [x for x in value if isinstance(x, dict)]


def str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [x for x in value if isinstance(x, str)]


# The harvested annotation fields, in one place: (agg key, annotation field,
# coercer, per-item wrapper, extract filename). Drives aggregation + dumping so
# the field set lives in a single registry instead of five copy-paste blocks.
EXTRACT_SPEC = [
    ("products", "products", dict_list, None, "products"),
    ("schedules", "schedules", dict_list, None, "schedules"),
    ("contacts", "contacts", dict_list, None, "contacts"),
    ("scope_items", "scope_items", str_list, lambda t: {"text": t}, "scope-items"),
    ("requirements", "requirements", dict_list, None, "requirements"),
]


def collect_tables(env: dict) -> list[dict]:
    out = []
    for page in env.get("pages", []) or []:
        if not isinstance(page, dict):
            continue
        for b in page.get("blocks", []) or []:
            if isinstance(b, dict) and (b.get("label") or "").lower() == "table":
                out.append({
                    "page": page.get("index"),
                    "bbox": b.get("bbox"),
                    "markdown": b.get("markdown") or b.get("text") or "",
                })
    return out


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def resolve_title(explicit, inputs, client, schemas, model, dry_run):
    """Return (title, how, ident_doc, ident_file_id). ident_file_id is the
    file_id of an uploaded first input so the caller can reuse it (no re-upload)."""
    first = inputs[0]
    if explicit:
        return explicit, "explicit", None, None
    if dry_run:
        return base_name(first), "fallback(dry-run)", first, None
    fid = upload_local(client, first, "identity") if not is_url(first) else None
    args = ocr_command(first, fid, (schemas / "identity.schema.json").read_text(),
                       model, pages="0", blocks=False, table_format=None)
    res = run_client(client, args, "identity") or {}
    title = parse_annotation(res).get("project_title")  # parse_annotation always returns a dict
    if title:
        return title, "extracted", first, fid
    return base_name(first), "fallback", first, fid


def process_doc(i, src, client, schema_text, model, fid_cache):
    """Upload (if local & not cached) + OCR one document. Returns a result dict.
    Safe to run concurrently — it touches no shared state."""
    doc_id = doc_id_for(i, src)
    if is_url(src):
        mode, fid = "document_url", None
    else:
        mode = "file_id"
        fid = fid_cache.get(src) or upload_local(client, src, doc_id)
        if not fid:
            return {"doc_id": doc_id, "source": src, "status": "failed",
                    "error": "upload failed", "env": None}
    env = run_client(client, ocr_command(src, fid, schema_text, model), doc_id)
    if env is None:
        return {"doc_id": doc_id, "source": src, "input_mode": mode,
                "status": "failed", "error": "ocr failed", "env": None}
    return {"doc_id": doc_id, "source": src, "input_mode": mode,
            "status": "ok", "env": env}


def build(args):
    inputs = args.inputs
    client = Path(args.client)
    schemas = Path(args.schemas)
    if not args.dry_run and not client.exists():
        log(f"OCR client not found at {client} (set --client)."); sys.exit(2)

    title, how, ident_doc, ident_fid = resolve_title(
        args.project, inputs, client, schemas, args.model, args.dry_run)
    slug = slugify(title)
    out_dir = Path(args.out) / slug
    log(f"project: {title!r} (via {how}) -> {out_dir}")

    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "project": {"title": title, "slug": slug, "identity_via": how},
            "dossier_dir": str(out_dir),
            "max_workers": min(MAX_WORKERS, max(1, len(inputs))),
            "planned": [
                {"input": s, "doc_id": doc_id_for(i, s),
                 "mode": "url" if is_url(s) else "file_id(after upload)"}
                for i, s in enumerate(inputs)],
            "outputs": ["project.json", "_raw/<docid>.ocr.json",
                        "extracts/{products,schedules,contacts,scope-items,requirements}.json",
                        "extracts/product-tables.csv", "index.md", "handoff.json"],
        }, indent=2))
        return

    (out_dir / "_raw").mkdir(parents=True, exist_ok=True)
    (out_dir / "extracts").mkdir(parents=True, exist_ok=True)

    schema_text = (schemas / "dossier.schema.json").read_text()
    fid_cache = {ident_doc: ident_fid} if ident_fid else {}

    # ---- concurrent extraction (fan out; only the OCR I/O is parallel) ----
    workers = min(MAX_WORKERS, max(1, len(inputs)))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(
            lambda p: process_doc(p[0], p[1], client, schema_text, args.model, fid_cache),
            list(enumerate(inputs))))

    # ---- aggregate in input order (single-threaded; no races) ----
    documents, tables, needs_review = [], [], []
    agg = {key: [] for key, *_ in EXTRACT_SPEC}
    identity = {"project_title": title}

    for r in results:
        doc_id = r["doc_id"]
        if r["status"] != "ok":
            documents.append({k: r[k] for k in ("doc_id", "source", "status", "error")
                              if k in r})
            needs_review.append(f"{doc_id}: {r.get('error')}")
            continue
        env = r["env"]
        write_json(out_dir / "_raw" / f"{doc_id}.ocr.json", env)
        ann = parse_annotation(env)
        ident = ann.get("project_identity")
        if isinstance(ident, dict):
            for k, v in ident.items():
                identity.setdefault(k, v)
        for key, field, coerce, wrap, _ in EXTRACT_SPEC:
            for item in coerce(ann.get(field)):
                rec = wrap(item) if wrap else dict(item)
                rec["_doc"] = doc_id
                agg[key].append(rec)
        tables += [{**t, "_doc": doc_id} for t in collect_tables(env)]
        documents.append({
            "doc_id": doc_id, "source": r["source"], "input_mode": r.get("input_mode"),
            "pages": (env.get("usage_info") or {}).get("pages_processed"),
            "status": "ok", "raw": f"_raw/{doc_id}.ocr.json",
        })

    # named views for the sections below
    products, schedules, contacts = agg["products"], agg["schedules"], agg["contacts"]
    scope_items, requirements = agg["scope_items"], agg["requirements"]

    # ---- write extracts ----
    extracts = {}
    def dump(name, key, data):
        if data:
            write_json(out_dir / "extracts" / f"{name}.json", data)
            extracts[key] = f"extracts/{name}.json"
    for key, _field, _coerce, _wrap, name in EXTRACT_SPEC:
        dump(name, key, agg[key])
    if tables:
        csv_path = out_dir / "extracts" / "product-tables.csv"
        with csv_path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["doc_id", "page", "bbox", "markdown"])
            for t in tables:
                w.writerow([t["_doc"], t.get("page"), json.dumps(t.get("bbox")),
                            t.get("markdown")])
        extracts["product_tables"] = "extracts/product-tables.csv"

    # ---- project.json ----
    project = {
        "title": title, "slug": slug,
        "number": identity.get("project_number"),
        "owner": identity.get("owner"),
        "location": identity.get("location"),
        "identity_source": {"doc": ident_doc, "how": how},
    }
    write_json(out_dir / "project.json", {
        "project": project, "documents": documents, "created_by": "project-intake"})

    # ---- index.md ----
    idx = [f"# {title}", "",
           f"- Slug: `{slug}`", f"- Number: {project['number'] or '—'}",
           f"- Owner: {project['owner'] or '—'}", f"- Location: {project['location'] or '—'}",
           "", "## Documents"]
    for d in documents:
        idx.append(f"- `{d['doc_id']}` ({d.get('status')}) — {d['source']}")
    idx += ["", "## Extracts",
            f"- products: {len(products)}", f"- schedules: {len(schedules)}",
            f"- contacts: {len(contacts)}", f"- tables: {len(tables)}",
            f"- scope items: {len(scope_items)}", f"- requirements: {len(requirements)}"]
    (out_dir / "index.md").write_text("\n".join(idx) + "\n")

    # ---- handoff.json (the contract) ----
    ok_docs = [d for d in documents if d.get("status") == "ok"]
    if ok_docs and len(ok_docs) == len(documents):
        status = "ready_for_review"   # every doc succeeded
    elif ok_docs:
        status = "partial"            # some succeeded
    else:
        status = "error"              # none succeeded (or no docs)
    handoff = {
        "schema_version": HANDOFF_VERSION,
        "status": status,
        "project": project,
        "dossier_dir": str(out_dir),
        "documents": documents,
        "extracts": extracts,
        "counts": {"documents": len(documents), "products": len(products),
                   "tables": len(tables), "schedules": len(schedules),
                   "contacts": len(contacts)},
        "needs_human_review": needs_review,
        "next_step": args.next_step,
        "created_at": args.created_at or "",
    }
    write_json(out_dir / "handoff.json", handoff)
    log(f"wrote handoff: {out_dir / 'handoff.json'} (status={status})")
    print(json.dumps(handoff, indent=2))


def main():
    p = argparse.ArgumentParser(description="Build a project dossier from documents.")
    p.add_argument("--inputs", nargs="+", required=True,
                   help="Document paths and/or URLs.")
    p.add_argument("--project", help="Explicit project title (skips extraction).")
    p.add_argument("--out", default="projects", help="Output root (default ./projects).")
    p.add_argument("--schemas", default=str(DEFAULT_SCHEMAS))
    p.add_argument("--client", default=str(DEFAULT_CLIENT),
                   help="Path to mistral-ocr4 mistral_ocr.py.")
    p.add_argument("--model", help="OCR model id (e.g. mistral-ocr-4).")
    p.add_argument("--next-step", default="construction-doc-pipeline:review")
    p.add_argument("--created-at", help="ISO timestamp to stamp (caller supplies).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the plan without calling the API (no key needed).")
    build(p.parse_args())


if __name__ == "__main__":
    main()
