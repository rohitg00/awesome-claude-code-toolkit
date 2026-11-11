#!/usr/bin/env bash
# install.sh — Automated Browserbase plugin setup with OAuth login
# Installs the browse CLI, discovers or obtains credentials via browser login,
# and auto-registers the key across every credential location.
# Notifies the user of every change but does not ask permission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

REGISTERED=()
SKIPPED=()

echo "=== Browserbase Plugin Setup ==="

# ─── 1. Check Node.js ───────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo "ERROR: Node.js is required but not installed."
  echo "Install it from https://nodejs.org or via your package manager."
  exit 1
fi
echo "[ok] Node.js $(node --version)"

# ─── 2. Install browse CLI if missing ────────────────────────────────────────
if command -v browse &>/dev/null; then
  echo "[ok] browse CLI already installed"
else
  echo "[..] Installing browse CLI..."
  npm install -g browse@latest 2>&1 | tail -1
  if command -v browse &>/dev/null; then
    echo "[ok] browse CLI installed"
  else
    echo "ERROR: browse CLI installation failed"
    exit 1
  fi
fi

# Remove deprecated CLIs that shadow browse
for pkg in @browserbasehq/cli @browserbasehq/browse-cli; do
  if npm list -g "$pkg" &>/dev/null 2>&1; then
    echo "[..] Removing deprecated $pkg..."
    npm uninstall -g "$pkg" 2>/dev/null || true
  fi
done

# ─── 3. Locate existing API key ─────────────────────────────────────────────
API_KEY="${BROWSERBASE_API_KEY:-}"

# Search .env files
if [ -z "$API_KEY" ]; then
  for envfile in .env .env.local .env.development .env.production; do
    if [ -f "$envfile" ] && grep -q "^BROWSERBASE_API_KEY=" "$envfile" 2>/dev/null; then
      val=$(grep "^BROWSERBASE_API_KEY=" "$envfile" | head -1 | cut -d= -f2-)
      if [ -n "$val" ] && [[ "$val" != "<"* ]] && [[ "$val" != "\${"* ]]; then
        API_KEY="$val"
        echo "[ok] Found BROWSERBASE_API_KEY in $envfile"
        break
      fi
    fi
  done
fi

# Search MCP configs
if [ -z "$API_KEY" ]; then
  for mcpfile in mcp-configs/browserbase.json .mcp.json; do
    if [ -f "$mcpfile" ]; then
      val=$(grep -oP '"BROWSERBASE_API_KEY"\s*:\s*"\K[^"]+' "$mcpfile" 2>/dev/null || true)
      if [ -n "$val" ] && [[ "$val" != "<"* ]] && [[ "$val" != "\${"* ]]; then
        API_KEY="$val"
        echo "[ok] Found BROWSERBASE_API_KEY in $mcpfile"
        break
      fi
    fi
  done
fi

# Search Claude settings
if [ -z "$API_KEY" ]; then
  for settings in .claude/settings.local.json .claude/settings.json "$HOME/.claude/settings.json"; do
    if [ -f "$settings" ]; then
      val=$(grep -oP '"BROWSERBASE_API_KEY"\s*:\s*"\K[^"]+' "$settings" 2>/dev/null || true)
      if [ -n "$val" ] && [[ "$val" != "<"* ]] && [[ "$val" != "\${"* ]]; then
        API_KEY="$val"
        echo "[ok] Found BROWSERBASE_API_KEY in $settings"
        break
      fi
    fi
  done
fi

# Search shell profiles
if [ -z "$API_KEY" ]; then
  for profile in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    if [ -f "$profile" ]; then
      val=$(grep -oP 'export BROWSERBASE_API_KEY=["'"'"']?\K[^"'"'"'\s]+' "$profile" 2>/dev/null || true)
      if [ -n "$val" ] && [[ "$val" != "<"* ]]; then
        API_KEY="$val"
        echo "[ok] Found BROWSERBASE_API_KEY in $profile"
        break
      fi
    fi
  done
fi

# ─── 4. If no key found, launch OAuth login ──────────────────────────────────
if [ -z "$API_KEY" ]; then
  echo ""
  echo "No API key found. Launching browser login..."
  echo ""

  # Detect headless environment
  if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ] && [[ "$(uname)" != "Darwin" ]]; then
    echo "[headless environment detected — printing URL instead of opening browser]"
    node "$PLUGIN_ROOT/auth/login.js" --headless
  else
    node "$PLUGIN_ROOT/auth/login.js"
  fi

  # After login.js completes, check if key was saved
  if [ -f .env ] && grep -q "^BROWSERBASE_API_KEY=" .env 2>/dev/null; then
    API_KEY=$(grep "^BROWSERBASE_API_KEY=" .env | head -1 | cut -d= -f2-)
  fi

  if [ -z "$API_KEY" ]; then
    echo "ERROR: Login did not produce an API key."
    echo "You can also set it manually:"
    echo "  export BROWSERBASE_API_KEY=bb_live_..."
    exit 1
  fi

  echo ""
  echo "[ok] API key obtained via login"
else
  # Key was found — auto-register it via the login script for consistency
  echo "[..] Auto-registering key across credential locations..."
  node "$PLUGIN_ROOT/auth/login.js" --key "$API_KEY"
fi

export BROWSERBASE_API_KEY="$API_KEY"

# ─── 5. Verify API access ───────────────────────────────────────────────────
echo ""
echo "[..] Verifying API access..."
result=$(browse cloud projects list --json 2>&1 | grep -v "Update available" | grep -v "npm install" | grep -v "DeprecationWarning")
if echo "$result" | grep -q '"id"'; then
  echo "[ok] API key verified — connected to Browserbase"
else
  echo "ERROR: API key verification failed"
  echo "$result"
  exit 1
fi

# ─── 6. Summary ─────────────────────────────────────────────────────────────
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Available commands:"
echo "  /browserbase:scrape-page   — Scrape and extract data from a web page"
echo "  /browserbase:fill-form     — Fill out and submit a web form"
echo "  /browserbase:browse-agent  — Run an open-ended browsing agent"
echo ""
echo "Dashboard: https://www.browserbase.com/sessions"
echo "Docs:      https://docs.browserbase.com"
