#!/usr/bin/env python3
"""Claude Code hook: NTXP Plans Atlas receiver for the Phase 1 drawing handoff.

  post   PostToolUse (Write, Edit, MultiEdit, Bash). When a tool call writes or names
         <kb>/handoffs/atlas-request.json (the Estimating Phase 1 skill staged a request),
         start phase1_receiver.py in the background. Idempotent, lock-protected, logged to
         <kb>/atlas/hook.log, and silent on anything else.
  start  SessionStart. Report requests that are pending or stale, so nothing waits unseen.

The hook never blocks a turn and never fails one: every error is swallowed and logged.
Set NTXP_PHASE1_HOOKS=off to disable, NTXP_HOOK_SYNC=1 to run the receiver in the foreground.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIVER = ROOT / "scripts" / "phase1_receiver.py"
REQ_RE = re.compile(r"[^\s\"'<>|;&]*atlas-request\.json")


def emit(text, event):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


def request_paths(payload):
    ti = payload.get("tool_input") or {}
    if payload.get("tool_name") in ("Write", "Edit", "MultiEdit"):
        p = str(ti.get("file_path") or "")
        return [p] if p.endswith("atlas-request.json") else []
    cmd = str(ti.get("command") or "")
    if "phase1_receiver.py" in cmd or "atlas-request.json" not in cmd:
        return []                       # the receiver itself, or an unrelated command
    if not re.search(r"(>|\btee\b|\bcp\b|\bmv\b|\binstall\b)", cmd):
        return []                       # reads such as cat or ls do not start a run
    cwd = Path(payload.get("cwd") or ".")
    return [str(cwd / m) if not os.path.isabs(m) else m for m in REQ_RE.findall(cmd)]


def run_receiver(req_path):
    req = json.loads(Path(req_path).read_text())
    out = Path(req["outputs_dir"])
    out.mkdir(parents=True, exist_ok=True)
    lock = out / ".receiver.lock"
    if lock.exists() and time.time() - lock.stat().st_mtime < 1800:
        return "a receiver run is already in progress"
    lock.write_text(str(os.getpid()))
    cmd = [sys.executable, str(RECEIVER), "receive", "--request", str(req_path)]
    log = open(out / "hook.log", "a")
    env = {**os.environ, "NTXP_RECEIVER_LOCK": str(lock)}     # the receiver releases it on every OS
    if os.environ.get("NTXP_HOOK_SYNC") == "1":
        try:
            r = subprocess.run(cmd, stdout=log, stderr=log, timeout=1500, env=env)
            return f"Plans Atlas receiver finished (exit {r.returncode}); see {out}/atlas-response.json"
        finally:
            lock.unlink(missing_ok=True)
    kwargs = {"creationflags": 0x00000008 | 0x00000200} if os.name == "nt" else {"start_new_session": True}
    subprocess.Popen(cmd, stdout=log, stderr=log, env=env, **kwargs)
    return f"Plans Atlas receiver started in the background; results will be in {out}/atlas-response.json (log: hook.log)"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "post"
    if os.environ.get("NTXP_PHASE1_HOOKS") == "off":
        return
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    try:
        if mode == "post":
            notes = []
            for p in request_paths(payload):
                if Path(p).is_file():
                    notes.append(run_receiver(p))
            if notes:
                emit(" | ".join(dict.fromkeys(notes)), "PostToolUse")
        else:
            cwd = Path(payload.get("cwd") or ".")
            lines = []
            for req in list(cwd.glob("handoffs/atlas-request.json")) + list(cwd.glob("*/handoffs/atlas-request.json")) \
                    + list(cwd.glob("*/*/handoffs/atlas-request.json")):
                r = subprocess.run([sys.executable, str(RECEIVER), "status", "--request", str(req)], capture_output=True, text=True, timeout=60)
                st = json.loads(r.stdout or "{}").get("state")
                if st in ("pending", "stale"):
                    lines.append(f"{req.parent.parent.name}: Plans Atlas request is {st}")
            if lines:
                emit("Phase 1 drawing handoffs waiting for the Plans Atlas: " + "; ".join(lines)
                     + ". Run phase1_receiver.py receive --request <path>.", "SessionStart")
    except Exception as exc:        # noqa: BLE001 - a hook must never fail a turn
        sys.stderr.write(f"phase1_atlas_hook: {exc}\n")


if __name__ == "__main__":
    main()
