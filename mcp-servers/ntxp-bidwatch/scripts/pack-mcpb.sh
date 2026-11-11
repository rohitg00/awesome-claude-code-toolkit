#!/usr/bin/env bash
# Build a distributable, installable MCP bundle (.mcpb) for NTXP BidWatch.
#
# Produces ntxp-bidwatch.mcpb containing manifest.json, the compiled
# server/ directory, package.json, and production node_modules — so it runs
# without an npm install on the target machine.
#
# Install by opening the file in Claude Desktop, or:
#   npx @anthropic-ai/mcpb install ntxp-bidwatch.mcpb
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUILD_DIR="$ROOT/build/bundle"
OUT="$ROOT/ntxp-bidwatch.mcpb"

echo "==> Compiling TypeScript"
npm install
npm run build

echo "==> Assembling bundle"
rm -rf "$BUILD_DIR" "$OUT"
mkdir -p "$BUILD_DIR/server"
cp -R dist/. "$BUILD_DIR/server/"
cp manifest.json "$BUILD_DIR/manifest.json"
node -e "const p=require('./package.json');require('fs').writeFileSync('$BUILD_DIR/package.json',JSON.stringify({name:p.name,version:p.version,type:p.type,dependencies:p.dependencies},null,2))"

echo "==> Installing production dependencies into the bundle"
( cd "$BUILD_DIR" && npm install --omit=dev --no-audit --no-fund --silent )

echo "==> Zipping bundle"
( cd "$BUILD_DIR" && zip -qr "$OUT" . )

echo "==> Done: $OUT"
ls -lh "$OUT"
