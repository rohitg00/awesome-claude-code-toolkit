#!/bin/bash
# Installs the NTXP Plans Atlas skill (ntxp-plans-atlas) into ~/.claude/skills from
# this repo's source at every session start, so the skill survives ephemeral
# cloud containers and always matches the merged code. In cloud sessions it
# also installs the Python libraries that give the atlas full capability
# (PyMuPDF for drawing extraction, openpyxl/segno/Pillow for the workbook).
set -euo pipefail

REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PACK="$REPO/plugins/canonical-project-model/scripts/platform_pack.py"
DEST="$HOME/.claude/skills/ntxp-plans-atlas"

if [ -f "$PACK" ]; then
  mkdir -p "$HOME/.claude/skills"
  python3 "$PACK" pack --target claude --out "$DEST" --name ntxp-plans-atlas >/dev/null \
    && echo "ntxp-plans-atlas skill installed from repo source" \
    || echo "warning: ntxp-plans-atlas skill install failed" >&2
fi

if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  python3 -m pip install --quiet --disable-pip-version-check \
    pymupdf "openpyxl>=3.1" "segno>=1.6" "Pillow>=10.0" 2>/dev/null \
    && echo "Plans Atlas Python dependencies ready" \
    || echo "warning: could not install Plans Atlas Python dependencies (atlas runs in manifest-only mode)" >&2
fi
exit 0
