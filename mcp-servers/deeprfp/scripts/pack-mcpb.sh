#!/usr/bin/env bash
# Build a distributable, installable MCP bundle (.mcpb) for the DeepRFP connector.
#
# The resulting deeprfp.mcpb is a zip containing:
#   manifest.json     install manifest (prompts for the API key)
#   server/index.js    compiled server entry point
#   package.json       runtime metadata
#   node_modules/      production dependencies (so it runs without npm install)
#
# Install it by opening the file in Claude Desktop, or:
#   npx @anthropic-ai/mcpb install deeprfp.mcpb
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUILD_DIR="$ROOT/build/bundle"
OUT="$ROOT/deeprfp.mcpb"

echo "==> Compiling TypeScript"
npm install
npm run build

echo "==> Installing production dependencies into the bundle"
rm -rf "$BUILD_DIR" "$OUT"
mkdir -p "$BUILD_DIR/server"
cp dist/index.js "$BUILD_DIR/server/index.js"
cp manifest.json "$BUILD_DIR/manifest.json"

# Minimal package.json for the bundled runtime.
node -e "const p=require('./package.json');require('fs').writeFileSync('$BUILD_DIR/package.json',JSON.stringify({name:p.name,version:p.version,type:p.type,dependencies:p.dependencies},null,2))"

( cd "$BUILD_DIR" && npm install --omit=dev --no-audit --no-fund --silent )

echo "==> Zipping bundle"
( cd "$BUILD_DIR" && zip -qr "$OUT" . )

echo "==> Done: $OUT"
ls -lh "$OUT"
