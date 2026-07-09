#!/usr/bin/env python3
"""
agent-guard — a PreToolUse guard hook for Claude Code.

Reads the PreToolUse JSON event on stdin. If the Bash command matches a
pattern drawn from real-world agent accidents (home-dir wipe, force-push to
main, curl|sh, disk overwrite, fork bomb, ...), it returns a `deny` decision
that blocks the call *even under --dangerously-skip-permissions*.

Design choices (honest scope — see PATTERNS.md):
  * Fail OPEN, never closed. On any parse error, unknown tool, or unmatched
    command we exit 0 with no output, so the normal permission flow applies.
    A guard that bricks your session is worse than no guard.
  * Pattern-based, not a sandbox. This is defense-in-depth against the
    *common, catastrophic, irreversible* mistakes — not a security boundary.
  * Zero dependencies. Pure stdlib. Set AGENT_GUARD_DISABLE=1 to bypass.

Exit 0 + deny JSON = block.  Exit 0 + no output = allow (normal flow).
"""
import json
import os
import re
import sys


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[agent-guard] {reason}",
        }
    }))
    sys.exit(0)


# --- rm -rf on a catastrophic target -------------------------------------
# We do NOT block every `rm -rf` (deleting node_modules is fine). We block it
# only when the target is a place that wipes your machine/home/repo root.
_RM_FLAGS = re.compile(r"-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive|--force", re.IGNORECASE)
_CATASTROPHIC_TARGET = re.compile(
    r"(?:^|\s)(?:"
    r"~/?(?:\s|$)"           # home dir:   rm -rf ~   /   ~/
    r"|\$HOME\b"             # $HOME
    r"|/(?:\s|$)"            # filesystem root:  rm -rf /
    r"|/\*"                  # rm -rf /*
    r"|~/\*"                 # rm -rf ~/*
    r"|\$HOME/\*"            # rm -rf $HOME/*
    r"|\.\.(?:/|\s|$)"       # parent traversal: rm -rf ../
    r"|\*\s*$"               # bare trailing wildcard: rm -rf *
    r"|/(?:etc|usr|var|bin|boot|lib|dev|sys|proc)(?:/|\s|$)"  # system dirs
    r")"
)


def check_rm(cmd: str):
    for seg in re.split(r"[;\n]|&&|\|\|", cmd):
        seg = seg.strip()
        if not re.search(r"\brm\b", seg):
            continue
        if not _RM_FLAGS.search(seg):
            continue
        if _CATASTROPHIC_TARGET.search(seg):
            return ("This `rm` is recursive/forced and targets your home dir, "
                    "filesystem root, a system dir, or a bare wildcard — the "
                    "single most common way agents destroy a machine. Blocked. "
                    "Delete a specific named subdirectory instead.")
    return None


# --- other irreversible / high-blast-radius patterns ---------------------
PATTERNS = [
    (re.compile(r"\bgit\s+push\b[^\n]*(?:--force\b|(?<!-)-f\b|--force-with-lease)"
                r"[^\n]*\b(?:origin\s+)?(?:main|master|HEAD)\b"
                r"|\bgit\s+push\b[^\n]*\b(?:origin\s+)?(?:main|master)\b[^\n]*(?:--force\b|(?<!-)-f\b)",
                re.IGNORECASE),
     "Force-push to main/master rewrites shared history and can destroy "
     "teammates' work. Push to a branch, or force-push a feature branch only."),

    (re.compile(r"(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|python\d?|perl|node)\b",
                re.IGNORECASE),
     "Piping a downloaded script straight into a shell runs unreviewed remote "
     "code as you. Download it, read it, then run it."),

    (re.compile(r"(?:\b(?:dd\b[^\n]*\bof=/dev/|mkfs(?:\.\w+)?\s+/dev/)|>\s*/dev/(?:sd|nvme|hd|disk)\w*)",
                re.IGNORECASE),
     "Writing directly to a block device (dd/mkfs/redirect to /dev/sdX) "
     "wipes a disk irrecoverably."),

    (re.compile(r"\bchmod\b[^\n]*-[a-zA-Z]*R[a-zA-Z]*\s+0?777\b"
                r"|\bchmod\b[^\n]*\s0?777\b[^\n]*-[a-zA-Z]*R", re.IGNORECASE),
     "Recursive chmod 777 makes a whole tree world-writable — a serious "
     "security hole. Set the minimal specific permissions instead."),

    (re.compile(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),
     "Fork bomb detected. This will hang or crash the machine."),
]


def main() -> None:
    if os.environ.get("AGENT_GUARD_DISABLE") == "1":
        sys.exit(0)
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except Exception:
        sys.exit(0)  # fail open — never break the session on our account
    if event.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = (event.get("tool_input") or {}).get("command") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        sys.exit(0)

    reason = check_rm(cmd)
    if reason:
        deny(reason)
    for rx, why in PATTERNS:
        if rx.search(cmd):
            deny(why)
    sys.exit(0)  # allow: no decision, normal permission flow applies


if __name__ == "__main__":
    main()
