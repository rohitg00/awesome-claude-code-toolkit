#!/usr/bin/env python3
"""Smart PreToolUse hook for Claude Code.

Decomposes compound bash commands (&&, ||, ;, |, $(), newlines) into
individual sub-commands and checks each against the allow/deny patterns
in ~/.claude/settings.json.

Source: https://github.com/liberzon/claude-hooks
Author: Yair Liberzon
License: MIT

Input:  JSON on stdin with tool_name and tool_input.command
Output: JSON with {"decision": "allow"/"deny", "reason": "..."} or silent exit
"""

import fnmatch
import json
import os
import re
import sys


def load_settings(path=None):
    """Load and return the permissions dict from settings.json."""
    if path is None:
        path = os.path.expanduser("~/.claude/settings.json")
    path = os.path.expanduser(path)
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_merged_settings(global_path=None):
    """Load and merge all settings layers matching Claude Code's behavior.

    Loads up to three sources and merges their permissions.allow/deny arrays:
      1. Global:        ~/.claude/settings.json (or $CLAUDE_SETTINGS_PATH)
      2. Project:       $CLAUDE_PROJECT_DIR/.claude/settings.json (committed)
      3. Project-local: $CLAUDE_PROJECT_DIR/.claude/settings.local.json (gitignored)
    """
    settings = load_settings(global_path)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        return settings

    # Load both project settings files
    project_shared = load_settings(
        os.path.join(project_dir, ".claude", "settings.json")
    )
    project_local = load_settings(
        os.path.join(project_dir, ".claude", "settings.local.json")
    )

    if not project_shared and not project_local:
        return settings

    # Merge permissions arrays from all layers (deduplicated, order-preserving)
    global_perms = settings.get("permissions", {})
    shared_perms = project_shared.get("permissions", {})
    local_perms = project_local.get("permissions", {})

    merged_allow = list(dict.fromkeys(
        global_perms.get("allow", [])
        + shared_perms.get("allow", [])
        + local_perms.get("allow", [])
    ))
    merged_deny = list(dict.fromkeys(
        global_perms.get("deny", [])
        + shared_perms.get("deny", [])
        + local_perms.get("deny", [])
    ))

    settings.setdefault("permissions", {})
    settings["permissions"]["allow"] = merged_allow
    settings["permissions"]["deny"] = merged_deny

    return settings


def parse_bash_patterns(patterns):
    """Extract command prefixes from Bash(...) permission patterns.

    "Bash(git status:*)" -> "git status"
    "Bash(rm:*)"         -> "rm"
    Non-Bash patterns are skipped.

    Returns a list of (prefix_string, glob_pattern) tuples.
    The glob_pattern is what fnmatch should match against.
    """
    result = []
    for pat in patterns:
        m = re.match(r'^Bash\((.+)\)$', pat)
        if not m:
            continue
        inner = m.group(1)
        # inner is like "git status:*" or "rm:*" or "/Users/yair/...adb*"
        # Split on first ':'
        colon_idx = inner.find(':')
        if colon_idx == -1:
            # Pattern like "Bash(something)" with no colon — treat as exact prefix
            result.append((inner, inner))
        else:
            prefix = inner[:colon_idx]
            suffix = inner[colon_idx + 1:]
            # The glob pattern is prefix + ' ' + suffix (for matching with args)
            # But we also want bare prefix to match (no args)
            glob_pat = prefix + ' ' + suffix if suffix else prefix
            result.append((prefix, glob_pat))
    return result


def command_matches_pattern(cmd, patterns):
    """Check if a command matches any of the parsed Bash patterns.

    Each pattern is (prefix, glob_pattern).
    A command matches if:
      - It equals the prefix exactly (bare command, no args), OR
      - fnmatch(cmd, glob_pattern) is True
    """
    for prefix, glob_pat in patterns:
        if cmd == prefix:
            return True
        if fnmatch.fnmatch(cmd, glob_pat):
            return True
    return False


def extract_subshells(command):
    """Extract contents of $() and backtick subshells, recursively.

    Returns a list of subshell content strings.
    """
    subshells = []

    # Extract $(...) — handle nested parens, but skip $((...)) arithmetic
    i = 0
    while i < len(command):
        if command[i] == '$' and i + 1 < len(command) and command[i + 1] == '(' \
                and not (i + 2 < len(command) and command[i + 2] == '('):
            # Find matching closing paren
            depth = 0
            start = i + 2
            j = i + 1
            while j < len(command):
                if command[j] == '(':
                    depth += 1
                elif command[j] == ')':
                    depth -= 1
                    if depth == 0:
                        content = command[start:j]
                        subshells.append(content)
                        # Recurse into content for nested subshells
                        subshells.extend(extract_subshells(content))
                        break
                j += 1
            i = j + 1
        else:
            i += 1

    # Extract backtick subshells (no nesting)
    parts = command.split('`')
    # Odd-indexed parts are inside backticks
    for idx in range(1, len(parts), 2):
        content = parts[idx]
        if content.strip():
            subshells.append(content)
            subshells.extend(extract_subshells(content))

    return subshells


def strip_heredocs(command):
    """Strip heredoc bodies from a command, leaving just the <<DELIM marker.

    Heredocs like <<'EOF'\\n...\\nEOF are replaced with the marker only
    (body removed).  This prevents heredoc content lines from being treated
    as sub-commands when we split on newlines.
    """
    lines = command.split('\n')
    result = []
    heredoc_delim = None
    i = 0

    while i < len(lines):
        if heredoc_delim is not None:
            # Inside heredoc body — look for the terminator line
            if lines[i].strip() == heredoc_delim:
                heredoc_delim = None
            i += 1
            continue

        # Check for heredoc marker: <<[-]?['"]?WORD['"]?
        m = re.search(r'<<-?\s*[\'"]?(\w+)[\'"]?', lines[i])
        if m:
            heredoc_delim = m.group(1)

        result.append(lines[i])
        i += 1

    return '\n'.join(result)


def split_on_operators(command):
    """Split a command string on &&, ||, ;, |, and newlines.

    Respects quoted strings and $() subshells (doesn't split inside them).
    Returns the top-level command segments.
    """
    # Strip heredoc bodies so their lines aren't treated as commands
    command = strip_heredocs(command)
    # Collapse backslash-newline continuations before parsing
    command = command.replace('\\\n', ' ')

    segments = []
    current = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    paren_depth = 0

    while i < len(command):
        ch = command[i]

        # Handle backslash escaping (not inside single quotes, where \ is literal)
        if ch == '\\' and not in_single_quote and i + 1 < len(command):
            current.append(ch)
            current.append(command[i + 1])
            i += 2
            continue

        # Track quoting
        if ch == "'" and not in_double_quote and paren_depth == 0:
            in_single_quote = not in_single_quote
            current.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single_quote and paren_depth == 0:
            in_double_quote = not in_double_quote
            current.append(ch)
            i += 1
            continue

        if in_single_quote or in_double_quote:
            current.append(ch)
            i += 1
            continue

        # Track $() subshell depth — consume $( as a single token
        if ch == '$' and i + 1 < len(command) and command[i + 1] == '(':
            paren_depth += 1
            current.append('$')
            current.append('(')
            i += 2
            continue
        if ch == '(' and paren_depth > 0:
            paren_depth += 1
            current.append(ch)
            i += 1
            continue
        if ch == ')' and paren_depth > 0:
            paren_depth -= 1
            current.append(ch)
            i += 1
            continue

        if paren_depth > 0:
            current.append(ch)
            i += 1
            continue

        # Split on operators at top level
        if ch == '&' and i + 1 < len(command) and command[i + 1] == '&':
            segments.append(''.join(current))
            current = []
            i += 2
            continue
        if ch == '|' and i + 1 < len(command) and command[i + 1] == '|':
            segments.append(''.join(current))
            current = []
            i += 2
            continue
        if ch == ';':
            segments.append(''.join(current))
            current = []
            i += 1
            continue
        if ch == '|':
            segments.append(''.join(current))
            current = []
            i += 1
            continue
        if ch == '\n':
            segments.append(''.join(current))
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    segments.append(''.join(current))
    return [s.strip() for s in segments if s.strip()]


def _skip_shell_value(cmd, i):
    """Skip past one shell 'word' value starting at position i.

    Handles quoted strings, $() subshells (tracking paren depth), and
    bare non-whitespace runs.  Returns the index just past the value.
    """
    if i >= len(cmd):
        return i

    # Quoted value
    if cmd[i] == '"':
        i += 1
        while i < len(cmd) and cmd[i] != '"':
            if cmd[i] == '\\' and i + 1 < len(cmd):
                i += 2
            else:
                i += 1
        if i < len(cmd):
            i += 1  # skip closing quote
        return i
    if cmd[i] == "'":
        i += 1
        while i < len(cmd) and cmd[i] != "'":
            i += 1
        if i < len(cmd):
            i += 1  # skip closing quote
        return i

    # Unquoted value — consume non-whitespace, tracking $() depth
    paren_depth = 0
    while i < len(cmd):
        ch = cmd[i]
        if ch == '$' and i + 1 < len(cmd) and cmd[i + 1] == '(':
            paren_depth += 1
            i += 2
            continue
        if ch == '(' and paren_depth > 0:
            paren_depth += 1
            i += 1
            continue
        if ch == ')' and paren_depth > 0:
            paren_depth -= 1
            i += 1
            continue
        if paren_depth > 0:
            i += 1
            continue
        if ch in (' ', '\t'):
            break
        i += 1
    return i


def strip_env_vars(cmd):
    """Strip leading environment variable assignments (FOO=bar cmd ...).

    Returns the command with env var prefixes removed.
    Correctly handles values containing $() subshells.
    """
    while True:
        m = re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', cmd)
        if not m:
            break
        # Find end of value (respecting quotes and $() depth)
        i = _skip_shell_value(cmd, m.end())
        # If nothing follows the assignment, this IS the command — keep it
        rest = cmd[i:].lstrip()
        if not rest:
            break
        cmd = rest
    return cmd


def strip_redirections(cmd):
    """Strip output/input redirections from a command.

    Removes patterns like >file, >>file, 2>&1, <file, etc.
    """
    # Remove redirections: N>file, N>>file, N>&N, <file, <<word, <<<word
    cmd = re.sub(r'\d*>>?\s*&?\d*\S*', '', cmd)
    cmd = re.sub(r'<<<?\s*\S+', '', cmd)
    # Simple input redirection: < file
    cmd = re.sub(r'<\s*\S+', '', cmd)
    return cmd.strip()


# Shell keywords that are structural, not commands to approve/deny.
# These appear as segments after splitting on ;/newlines in for/while/if blocks.
SHELL_KEYWORDS = frozenset({
    'do', 'done', 'then', 'else', 'elif', 'fi', 'esac', '{', '}',
    'break', 'continue',
})

# Keywords that can prefix a command when joined by ; (e.g. "do echo hello").
# These should be stripped to expose the real command underneath.
_KEYWORD_PREFIX_RE = re.compile(
    r'^(do|then|else|elif)\s+'
)

# Patterns for shell compound statement headers (for, while, until, if, case).
# These introduce control flow but aren't executable commands themselves.
_COMPOUND_HEADER_RE = re.compile(
    r'^(for|while|until|if|case|select)\b'
)


def strip_keyword_prefix(cmd):
    """Strip leading shell keyword prefix from a command.

    "do echo hello" -> "echo hello"
    "then git status" -> "git status"
    """
    m = _KEYWORD_PREFIX_RE.match(cmd)
    if m:
        return cmd[m.end():]
    return cmd


def is_shell_structural(cmd):
    """Return True if cmd is a shell keyword or compound-statement header."""
    if cmd in SHELL_KEYWORDS:
        return True
    if _COMPOUND_HEADER_RE.match(cmd):
        return True
    return False


def is_standalone_assignment(cmd):
    """Return True if cmd is purely a variable assignment (no following command).

    e.g. "result=$(curl ...)" or "FOO=bar" — these are not commands to check.
    The subshell contents, if any, are extracted and checked separately.
    """
    m = re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', cmd)
    if not m:
        return False
    # Check if the entire string is consumed by the assignment value
    end = _skip_shell_value(cmd, m.end())
    rest = cmd[end:].strip()
    return rest == ''


def normalize_command(cmd):
    """Normalize a command by stripping env vars, redirections, and whitespace."""
    cmd = cmd.strip()
    if not cmd:
        return cmd
    cmd = strip_keyword_prefix(cmd)
    cmd = strip_env_vars(cmd)
    cmd = strip_redirections(cmd)
    # Collapse multiple spaces
    cmd = re.sub(r'\s+', ' ', cmd)
    return cmd.strip()


def decompose_command(command):
    """Decompose a compound command into all individual sub-commands.

    Splits on operators, extracts subshell contents, normalizes each.
    Filters out shell structural keywords (for/do/done/etc.) and
    standalone variable assignments (whose subshell contents are checked
    separately).
    Returns a list of normalized command strings.
    """
    all_commands = []

    # Get top-level segments
    segments = split_on_operators(command)

    for seg in segments:
        # Also decompose any subshells found in this segment
        subshells = extract_subshells(seg)
        for sub in subshells:
            sub_segments = split_on_operators(sub)
            for ss in sub_segments:
                normalized = normalize_command(ss)
                if normalized:
                    all_commands.append(normalized)

        # Normalize the top-level segment itself
        normalized = normalize_command(seg)
        if normalized:
            all_commands.append(normalized)

    # Filter out shell structural keywords and standalone assignments
    return [
        cmd for cmd in all_commands
        if not is_shell_structural(cmd) and not is_standalone_assignment(cmd)
    ]


def decide(command, settings):
    """Make a permission decision for a compound command.

    Returns:
        ("allow", reason) if all sub-commands match allow patterns
        ("deny", reason) if any sub-command matches a deny pattern
        (None, None) if we should fall through to normal prompting
    """
    if not command or not command.strip():
        return None, None

    permissions = settings.get("permissions", {})
    allow_patterns = parse_bash_patterns(permissions.get("allow", []))
    deny_patterns = parse_bash_patterns(permissions.get("deny", []))

    sub_commands = decompose_command(command)
    if not sub_commands:
        return None, None

    # Check deny first
    for cmd in sub_commands:
        if command_matches_pattern(cmd, deny_patterns):
            return "deny", f"Sub-command '{cmd}' matches deny pattern"

    # Check if ALL match allow
    all_allowed = True
    for cmd in sub_commands:
        if not command_matches_pattern(cmd, allow_patterns):
            all_allowed = False
            break

    if all_allowed:
        return "allow", "All sub-commands match allow patterns"

    return None, None


_log_lines = []


def _verbose_enabled():
    """Check if verbose logging is enabled.

    Controlled by SMART_APPROVE_VERBOSE env var:
      "1", "true", "yes" → enabled
      "0", "false", "no", unset → disabled
    """
    return os.environ.get("SMART_APPROVE_VERBOSE", "").lower() in ("1", "true", "yes")


def log(msg):
    """Collect verbose log line when enabled."""
    if _verbose_enabled():
        _log_lines.append(msg)


def _build_reason(reason):
    """Build the permissionDecisionReason, appending verbose logs if any."""
    if not _log_lines:
        return reason
    verbose = " | ".join(_log_lines)
    if reason:
        return f"{reason} | {verbose}"
    return verbose


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        log("no valid JSON on stdin, skipping")
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        log(f"tool={tool_name}, not Bash — skipping")
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        log("empty command, skipping")
        sys.exit(0)

    cmd_preview = command[:80].replace('\n', '\\n')
    log(f"checking: {cmd_preview}{'...' if len(command) > 80 else ''}")

    settings_path = os.environ.get("CLAUDE_SETTINGS_PATH")
    settings = load_merged_settings(settings_path)

    sub_commands = decompose_command(command)
    log(f"sub-commands: {sub_commands[:5]}{'...' if len(sub_commands) > 5 else ''}")

    decision, reason = decide(command, settings)

    log(f"decision={decision or 'passthrough'} reason={reason or 'no pattern matched'}")

    if decision is not None:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": _build_reason(reason),
            }
        }
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")
    # else: silent exit — fall through to normal prompting


if __name__ == "__main__":
    main()
