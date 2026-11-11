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
#                                      compiled CLI (needs real fs/network);
#                                      drop into ~/.claude/skills/ for Claude
#                                      Code. Do NOT upload this one to
#                                      claude.ai — its sandbox has no
#                                      persistent config and no guaranteed
#                                      egress to Tesla's API.
#   build/tesla-connector-skill-claudeai.zip
#                                      Minimal connector-only Skill (SKILL.md
#                                      only, no bundled code) — upload THIS
#                                      one at claude.ai → Settings →
#                                      Capabilities → Skills. It just teaches
#                                      Claude to use the tesla_* tools that
#                                      the Tesla connector (.mcpb, or the
#                                      bridge's /mcp custom connector)
#                                      already exposes.
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
# SKILL.md must sit at the zip root (no wrapping folder) — claude.ai's
# uploader requires a top-level SKILL.md or .claude-plugin/plugin.json.
echo "==> Building tesla-connector-skill.zip"
SKILL="$BUILD/skill"
mkdir -p "$SKILL"
cp skill/SKILL.md "$SKILL/SKILL.md"
cp -R "$BUILD/payload/server" "$SKILL/server"
( cd "$SKILL" && zip -qr "$BUILD/tesla-connector-skill.zip" . )

# --- 4. Minimal connector-only Skill (for claude.ai web upload) ---------------
echo "==> Building tesla-connector-skill-claudeai.zip"
SKILL_WEB="$BUILD/skill-web/tesla-connector"
mkdir -p "$SKILL_WEB"
cp skill-connector-only/SKILL.md "$SKILL_WEB/SKILL.md"
( cd "$BUILD/skill-web" && zip -qr "$BUILD/tesla-connector-skill-claudeai.zip" tesla-connector )

echo "==> Done:"
ls -lh "$BUILD"/tesla.mcpb "$BUILD"/tesla-connector-plugin.zip "$BUILD"/tesla-connector-skill.zip "$BUILD"/tesla-connector-skill-claudeai.zip
