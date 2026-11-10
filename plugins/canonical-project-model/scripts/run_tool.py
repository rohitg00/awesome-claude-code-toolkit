#!/usr/bin/env python3
"""Execute an NTXP Plans Atlas function-tool call.

API deployments (OpenAI, xAI/Grok, Anthropic) receive a tool call as a name plus
a JSON arguments object, as defined in tools/functions.json. This runner maps
that call onto the deterministic scripts, so every model drives the same code
path and nothing is re-derived by model judgement.

    python scripts/run_tool.py deploy_plans_atlas '{"project": "proj", "event": "bid_confirmed"}'

The script's stdout (JSON) is the tool result to hand back to the model. It is
stdlib-only.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

# tool name -> (script, {json_arg: cli_flag}, {boolean json_arg: cli_flag})
TOOLS = {
    "deploy_plans_atlas": (
        "deploy_atlas.py",
        {"project": "--project", "event": "--event", "const_docs": "--const-docs",
         "pdf_dir": "--pdf-dir", "dossier": "--dossier", "company": "--company"},
        {"force": "--force", "check": "--check", "dry_run": "--dry-run"},
    ),
    "render_plans_atlas_viewer": (
        "build_atlas_html.py",
        {"model": "--model", "out": "--out", "company": "--company"},
        {"fragment": "--fragment"},
    ),
    "project_ignition_blueprint": (
        "ignition.py", {"project": "--project", "today": "--today"}, {}, "blueprint",
    ),
    "project_ignition_process": (
        "ignition.py",
        {"project": "--project", "today": "--today", "astra": "--astra", "opus": "--opus",
         "benchmarks": "--benchmarks", "markup_pct": "--markup-pct"},
        {}, "process",
    ),
    "phase1_receive_atlas_request": (
        "phase1_receiver.py", {"request": "--request"}, {"force": "--force", "no_chain": "--no-chain"}, "receive",
    ),
    "build_scope_index": (
        "scope_index.py", {"model": "--model", "pdf_dir": "--pdf-dir"}, {}, "build",
    ),
    "build_linked_drawing_set": (
        "build_atlas_pdf.py",
        {"pdf": "--pdf", "model": "--model", "out": "--out", "project": "--project",
         "legend_out": "--legend-out", "legend_md": "--legend-md"}, {},
    ),
    "export_sheet_with_markups": (
        "atlas_live.py", {"project": "--project", "sheet": "--sheet", "layers": "--layers", "out": "--out"}, {}, "export",
    ),
    "project_ignition_itb": (
        "ignition.py", {"project": "--project", "today": "--today"}, {"pdf": "--pdf"}, "itb",
    ),
}


def build_argv(name, args):
    if name not in TOOLS:
        raise ValueError(f"unknown tool {name!r}; expected one of {sorted(TOOLS)}")
    script, valued, flags, *rest = TOOLS[name]
    sub = rest[0] if rest else None
    unknown = set(args) - set(valued) - set(flags)
    if unknown:
        raise ValueError(f"unknown argument(s) for {name}: {sorted(unknown)}")
    argv = [sys.executable, str(SCRIPTS / script)]
    if sub:
        argv.append(sub)
    for key, flag in valued.items():
        if args.get(key) not in (None, ""):
            argv += [flag, str(args[key])]
    for key, flag in flags.items():
        if args.get(key) is True:
            argv.append(flag)
    return argv


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: run_tool.py <tool_name> '<arguments-json>'\n")
        return 2
    try:
        args = json.loads(sys.argv[2] or "{}")
        if not isinstance(args, dict):
            raise ValueError("arguments must be a JSON object")
        argv = build_argv(sys.argv[1], args)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2
    proc = subprocess.run(argv, capture_output=True, text=True)
    sys.stderr.write(proc.stderr)
    out = proc.stdout.strip()
    if proc.returncode != 0:
        print(json.dumps({"status": "error", "exit_code": proc.returncode,
                          "detail": (proc.stderr.strip().splitlines() or [""])[-1]}))
        return proc.returncode
    print(out or json.dumps({"status": "ok"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
