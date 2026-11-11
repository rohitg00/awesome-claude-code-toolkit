#!/usr/bin/env bash
# Assemble the installable NTXP API Log skill zip: SKILL.md + README + the
# ntxp_apilog package (from api-log-db/) + install metadata + a freshly
# migrated, empty apilog.db. Usage: build.sh [output.zip]
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
PKG_SRC="$REPO_ROOT/api-log-db/ntxp_apilog"
OUT="${1:-$PWD/ntxp-api-log-skill.zip}"

STAGE="$(mktemp -d)"
DEST="$STAGE/ntxp-api-log"
mkdir -p "$DEST"

# 1. Skill files
cp "$SKILL_DIR/SKILL.md" "$SKILL_DIR/README.md" "$SKILL_DIR/requirements.txt" "$DEST/"
cp "$REPO_ROOT/api-log-db/pyproject.toml" "$DEST/"

# 2. Package code
cp -r "$PKG_SRC" "$DEST/ntxp_apilog"

# 3. A pre-initialized (migrated, empty) database — no secrets, no key.
PYTHONPATH="$DEST" python - "$DEST/apilog.db" <<'PY'
import sys
from ntxp_apilog.db import connect, migrate
conn = connect(sys.argv[1])
migrate(conn)
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.close()
PY
rm -f "$DEST/apilog.db-wal" "$DEST/apilog.db-shm"

# 4. Strip caches (the migrate step above compiles modules) and zip
find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$DEST" -name '*.pyc' -delete
rm -f "$OUT"
( cd "$STAGE" && zip -rq "$OUT" ntxp-api-log )
rm -rf "$STAGE"

echo "Built $OUT"
unzip -l "$OUT"
