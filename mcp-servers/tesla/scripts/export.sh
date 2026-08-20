#!/usr/bin/env bash
# Export the Tesla connector as three prepackaged, self-contained artifacts
# (Claude packaging architecture — no repo clone or npm install on the target):
#
#   build/tesla.mcpb                   MCP Bundle — one-click install in Claude
#                                      Desktop (or `npx @anthropic-ai/mcpb install`)
#   build/tesla-connector-plugin.zip   Claude Code plugin with the compiled
#                                      server embedded (bootstrap uses the
#                                      bundled copy; MCP server + /setup +
#                                      /dashboard commands + skill + hook)
#   build/tesla-connector-skill.zip    Prepackaged Agent Skill — SKILL.md +
#                                      compiled CLI; drop into ~/.claude/skills/
#                                      or upload to claude.ai
#
# Usage: scripts/export.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
PLUGIN_SRC="$REPO_ROOT/plugins/tesla-connector"
BUILD="$ROOT/build"
cd "$ROOT"

echo "==> Compiling TypeScript"
npm install --no-audit --no-fund
npm run build

echo "==> Staging the shared self-contained server payload"
rm -rf "$BUILD"
PAYLOAD="$BUILD/payload/server"
mkdir -p "$PAYLOAD"
cp -R dist "$PAYLOAD/dist"
cp -R public "$PAYLOAD/public"
mkdir -p "$PAYLOAD/scripts"
cp scripts/get-refresh-token.mjs "$PAYLOAD/scripts/"
node -e "const p=require('./package.json');require('fs').writeFileSync('$PAYLOAD/package.json',JSON.stringify({name:p.name,version:p.version,type:p.type,bin:p.bin,dependencies:p.dependencies},null,2))"
( cd "$PAYLOAD" && npm install --omit=dev --no-audit --no-fund --silent )

# --- 1. MCP Bundle (.mcpb) ----------------------------------------------------
echo "==> Building tesla.mcpb"
MCPB="$BUILD/mcpb"
mkdir -p "$MCPB"
cp -R "$PAYLOAD/dist/." "$MCPB/server/"
cp -R "$PAYLOAD/node_modules" "$MCPB/node_modules"
cp -R "$PAYLOAD/public" "$MCPB/public"
cp "$PAYLOAD/package.json" "$MCPB/package.json"
cp manifest.json "$MCPB/manifest.json"
( cd "$MCPB" && zip -qr "$BUILD/tesla.mcpb" . )

# --- 2. Self-contained Claude Code plugin -------------------------------------
echo "==> Building tesla-connector-plugin.zip"
PLUG="$BUILD/plugin/tesla-connector"
mkdir -p "$PLUG"
cp -R "$PLUGIN_SRC/." "$PLUG/"
cp -R "$BUILD/payload/server" "$PLUG/server"   # bootstrap prefers ../../mcp-servers/tesla, falls back to this bundled copy
( cd "$BUILD/plugin" && zip -qr "$BUILD/tesla-connector-plugin.zip" tesla-connector )

# --- 3. Prepackaged Agent Skill ------------------------------------------------
echo "==> Building tesla-connector-skill.zip"
SKILL="$BUILD/skill/tesla-connector"
mkdir -p "$SKILL"
cp skill/SKILL.md "$SKILL/SKILL.md"
cp -R "$BUILD/payload/server" "$SKILL/server"
( cd "$BUILD/skill" && zip -qr "$BUILD/tesla-connector-skill.zip" tesla-connector )

echo "==> Done:"
ls -lh "$BUILD"/tesla.mcpb "$BUILD"/tesla-connector-plugin.zip "$BUILD"/tesla-connector-skill.zip
