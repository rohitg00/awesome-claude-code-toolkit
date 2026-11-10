#!/usr/bin/env python3
"""Package the NTXP Plans Atlas for a specific AI platform, and restore it there.

ChatGPT Knowledge and Grok project files are flat (no folders) and capped in
count (a Custom GPT allows 20 Knowledge files). This script builds a flat bundle
that fits those limits, and it ships inside the bundle so the sandbox can rebuild
the original folder layout before the scripts run.

    # on your machine: build the upload set
    python scripts/platform_pack.py pack --target chatgpt --out dist/chatgpt
    python scripts/platform_pack.py pack --target grok    --out dist/grok
    python scripts/platform_pack.py pack --target claude  --out dist/claude

    # inside ChatGPT Code Interpreter / a Grok code sandbox: restore the layout
    python /mnt/data/platform_pack.py setup --src /mnt/data --to /mnt/data/ntxp

It is stdlib-only.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # the plugin / skill root
BUNDLE = "schemas.bundle.json"
FLAT_LIMIT = 20

# Files every flat target carries (relative to ROOT). Schemas travel as one bundle.
FLAT_CORE = ["AGENTS.md", "config/defaults.yaml",
             "resources/masterformat-divisions.json"]
FLAT_SCRIPTS = ["assemble_model.py", "build_atlas_data.py", "build_atlas_html.py",
                "build_dashboard_html.py", "build_workbook.py", "build_atlas_pdf.py", "atlas_ocr.py", "ignition.py", "interlink.py", "phase1_receiver.py", "deploy_atlas.py", "scope_index.py", "atlas_shell.py",
                "run_tool.py", "platform_pack.py"]   # compress_pdf.py and atlas_live.py ship in the full skill only (20-file limit)
ADAPTER = {"chatgpt": "chatgpt/gpt-instructions.md",
           "grok": "grok/grok-instructions.md"}

# Where each flat file goes when the layout is restored.
RESTORE = {"AGENTS.md": "AGENTS.md", "defaults.yaml": "config/defaults.yaml",
           "masterformat-divisions.json": "resources/masterformat-divisions.json",
           "gpt-instructions.md": "chatgpt/gpt-instructions.md",
           "grok-instructions.md": "grok/grok-instructions.md"}


def log(msg):
    sys.stderr.write(f"[platform-pack] {msg}\n")


def bundle_schemas():
    return {p.name: json.loads(p.read_text()) for p in sorted((ROOT / "schemas").glob("*.json"))}


def pack_flat(target, out):
    out.mkdir(parents=True, exist_ok=True)
    files = FLAT_CORE + [f"scripts/{s}" for s in FLAT_SCRIPTS] + [ADAPTER[target]]
    for rel in files:
        shutil.copy2(ROOT / rel, out / Path(rel).name)
    (out / BUNDLE).write_text(json.dumps(bundle_schemas(), indent=1))
    count = len(list(out.iterdir()))
    if count > FLAT_LIMIT:
        raise SystemExit(f"{count} files exceeds the {FLAT_LIMIT}-file platform limit")
    log(f"{target}: {count} flat files -> {out} (limit {FLAT_LIMIT})")
    return count


def pack_claude(out, name=None):
    """Claude skill folder: root SKILL.md is Claude-native, so the nested adapter
    SKILL.md is left out to keep exactly one SKILL.md in the upload. `name`
    rewrites the frontmatter name (for example to install as ntxp-plans-atlas)."""
    if out.exists():
        shutil.rmtree(out)
    skill_md = ROOT.parent.parent / "skills" / "canonical-project-model" / "SKILL.md"
    if not skill_md.exists():
        skill_md = ROOT / "SKILL.md"
    shutil.copytree(ROOT, out, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".claude-plugin", "hooks", "commands", "claude"))
    shutil.copy2(skill_md, out / "SKILL.md")
    if name:
        text = (out / "SKILL.md").read_text()
        text = re.sub(r"^name: .*$", f"name: {name}", text, count=1, flags=re.M)
        (out / "SKILL.md").write_text(text)
    count = sum(1 for p in out.rglob("*") if p.is_file())
    log(f"claude: {count} files -> {out}")
    return count


def setup(src, to):
    """Rebuild the folder layout from a flat upload so the scripts find each other."""
    for d in ("scripts", "schemas", "resources", "config", "chatgpt", "grok"):
        (to / d).mkdir(parents=True, exist_ok=True)
    restored = 0
    for f in src.iterdir():
        if not f.is_file() or f.name == BUNDLE:
            continue
        if f.suffix == ".py":
            dest = to / "scripts" / f.name
        elif f.name in RESTORE:
            dest = to / RESTORE[f.name]
        else:
            continue
        shutil.copy2(f, dest)
        restored += 1
    bundle = src / BUNDLE
    if bundle.exists():
        for name, schema in json.loads(bundle.read_text()).items():
            (to / "schemas" / name).write_text(json.dumps(schema, indent=2))
            restored += 1
    else:
        log(f"warning: {BUNDLE} not found in {src}; schemas not restored")
    log(f"restored {restored} files into {to}")
    print(json.dumps({"status": "ready", "root": str(to),
                      "deploy": f"python {to}/scripts/deploy_atlas.py --project <dir> --event <event>"}))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack", help="Build an upload set for a platform.")
    p.add_argument("--target", required=True, choices=["chatgpt", "grok", "claude"])
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--name", help="Claude target only: skill name to write into SKILL.md.")
    s = sub.add_parser("setup", help="Restore the folder layout from a flat upload.")
    s.add_argument("--src", required=True, type=Path)
    s.add_argument("--to", required=True, type=Path)
    a = ap.parse_args()
    if a.cmd == "pack":
        n = pack_claude(a.out, a.name) if a.target == "claude" else pack_flat(a.target, a.out)
        print(json.dumps({"status": "packed", "target": a.target, "files": n, "out": str(a.out)}))
    else:
        setup(a.src, a.to)


if __name__ == "__main__":
    main()
