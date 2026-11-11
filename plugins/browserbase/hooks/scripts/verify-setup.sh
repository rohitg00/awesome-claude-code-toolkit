#!/usr/bin/env bash
# verify-setup.sh  (SessionStart hook)
# Auto-discovers BROWSERBASE_API_KEY from all known credential locations,
# registers it where missing, and emits a context hint with the result.
# If no key is found, hints to run the OAuth login flow.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

FOUND_KEY=""
FOUND_IN=""
REGISTERED=()

# ─── Search for the key across all known locations ──────────────────────────

if [ -n "${BROWSERBASE_API_KEY:-}" ]; then
  FOUND_KEY="$BROWSERBASE_API_KEY"
  FOUND_IN="environment variable"
fi

if [ -z "$FOUND_KEY" ]; then
  for envfile in .env .env.local .env.development .env.production; do
    if [ -f "$envfile" ] && grep -q "^BROWSERBASE_API_KEY=" "$envfile" 2>/dev/null; then
      val=$(grep "^BROWSERBASE_API_KEY=" "$envfile" | head -1 | cut -d= -f2-)
      if [ -n "$val" ] && [[ "$val" != "<"* ]] && [[ "$val" != "\${"* ]]; then
        FOUND_KEY="$val"
        FOUND_IN="$envfile"
        break
      fi
    fi
  done
fi

if [ -z "$FOUND_KEY" ]; then
  for mcpfile in mcp-configs/browserbase.json .mcp.json; do
    if [ -f "$mcpfile" ]; then
      val=$(grep -oP '"BROWSERBASE_API_KEY"\s*:\s*"\K[^"]+' "$mcpfile" 2>/dev/null || true)
      if [ -n "$val" ] && [[ "$val" != "<"* ]] && [[ "$val" != "\${"* ]]; then
        FOUND_KEY="$val"
        FOUND_IN="$mcpfile"
        break
      fi
    fi
  done
fi

if [ -z "$FOUND_KEY" ]; then
  for settings in .claude/settings.local.json .claude/settings.json "$HOME/.claude/settings.json"; do
    if [ -f "$settings" ]; then
      val=$(grep -oP '"BROWSERBASE_API_KEY"\s*:\s*"\K[^"]+' "$settings" 2>/dev/null || true)
      if [ -n "$val" ] && [[ "$val" != "<"* ]] && [[ "$val" != "\${"* ]]; then
        FOUND_KEY="$val"
        FOUND_IN="$settings"
        break
      fi
    fi
  done
fi

if [ -z "$FOUND_KEY" ]; then
  for profile in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    if [ -f "$profile" ]; then
      val=$(grep -oP 'export BROWSERBASE_API_KEY=["'"'"']?\K[^"'"'"'\s]+' "$profile" 2>/dev/null || true)
      if [ -n "$val" ] && [[ "$val" != "<"* ]]; then
        FOUND_KEY="$val"
        FOUND_IN="$profile"
        break
      fi
    fi
  done
fi

# ─── No key found — hint to run OAuth login ─────────────────────────────────
if [ -z "$FOUND_KEY" ]; then
  msg="[browserbase] No API key found. Run /browserbase:setup to log in via browser popup and auto-configure credentials. The login flow opens Browserbase in your browser, you paste your API key, and it is validated and saved to .env, shell profile, and MCP configs automatically."
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$msg\"}}"
  exit 0
fi

# ─── Auto-register into locations that are missing it ────────────────────────

if [ -f .env ]; then
  if ! grep -q "^BROWSERBASE_API_KEY=" .env 2>/dev/null; then
    echo "BROWSERBASE_API_KEY=$FOUND_KEY" >> .env
    REGISTERED+=(".env")
  fi
else
  echo "BROWSERBASE_API_KEY=$FOUND_KEY" > .env
  REGISTERED+=(".env (created)")
fi

# mcp-configs/browserbase.json and .mcp.json both reference ${BROWSERBASE_API_KEY}
# by env-var expansion, so they resolve automatically once .env/the environment
# is set — nothing to write there, and doing so would risk committing a live
# secret into a tracked repo file.

# ─── Emit notification ──────────────────────────────────────────────────────
if [ ${#REGISTERED[@]} -gt 0 ]; then
  locs=$(printf ", %s" "${REGISTERED[@]}")
  locs="${locs:2}"
  msg="[browserbase] Auto-registered BROWSERBASE_API_KEY (found in $FOUND_IN) into: $locs. No action needed."
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$msg\"}}"
else
  if ! command -v browse &>/dev/null; then
    msg="[browserbase] API key is configured but the browse CLI is not installed. Run: npm install -g browse@latest"
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$msg\"}}"
  fi
fi
