#!/usr/bin/env python3
"""Install (or remove) the Plans Atlas Phase 1 hooks in a Claude Code settings.json.

Plugin installs already get hooks/hooks.json automatically. Use this for a plain skill
folder or a project:

    python install_hooks.py --settings .claude/settings.json          # this project
    python install_hooks.py --settings ~/.claude/settings.json        # every project
    python install_hooks.py --settings ... --remove

Idempotent, keeps every other hook, writes a .bak first.
"""
import argparse
import json
import shutil
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "phase1_atlas_hook.py"
ENTRIES = {
    "PostToolUse": {"matcher": "Write|Edit|MultiEdit|Bash", "mode": "post", "timeout": 30},
    "SessionStart": {"matcher": None, "mode": "start", "timeout": 30},
}


def command(mode):
    return f'python3 "{SCRIPT}" {mode}'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--settings", required=True)
    ap.add_argument("--remove", action="store_true")
    a = ap.parse_args()
    path = Path(a.settings).expanduser()
    data = json.loads(path.read_text()) if path.exists() else {}
    if path.exists():
        shutil.copy2(path, str(path) + ".bak")
    hooks = data.setdefault("hooks", {})
    changed = []
    for event, spec in ENTRIES.items():
        groups = hooks.setdefault(event, [])
        cmd = command(spec["mode"])
        present = any(h.get("command") == cmd for g in groups for h in g.get("hooks", []))
        if a.remove and present:
            for g in groups:
                g["hooks"] = [h for h in g.get("hooks", []) if h.get("command") != cmd]
            hooks[event] = [g for g in groups if g.get("hooks")]
            changed.append(f"removed {event}")
        elif not a.remove and not present:
            group = {"hooks": [{"type": "command", "command": cmd, "timeout": spec["timeout"]}]}
            if spec["matcher"]:
                group["matcher"] = spec["matcher"]
            groups.append(group)
            changed.append(f"added {event}")
        if not hooks.get(event):
            hooks.pop(event, None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    print(json.dumps({"settings": str(path), "changes": changed or ["none (already up to date)"]}, indent=2))


if __name__ == "__main__":
    main()
