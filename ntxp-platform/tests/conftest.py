import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "ntxp-platform", ROOT / "contacts-db", ROOT / "contracts-db", ROOT / "api-log-db"):
    sys.path.insert(0, str(p))
