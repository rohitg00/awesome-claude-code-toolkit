"""JEV qualification / grading engine.

Every contact in the canonical store carries references from one or more sources
(`source_records`). This module grades each contact on four axes and writes a
`contact_grade` row with an exposure/sync gate:

  * **source**        — trust rank of the best source (config.SYSTEM_PRECEDENCE).
  * **recency**       — age of the freshest observation (exponential decay).
  * **corroboration** — how many independent sources resolved to this contact.
  * **distance**      — how far the closest source is from the person themselves
                        (self/CRM = near, public dataset = mid, OCR scan = far).

The grade is a probability in [0, 1] and an A/B/C/D band. Nothing is ever
dropped — outdated or weak contacts keep all their references, but are marked
`is_exposed = 0` / `is_synced = 0` so the UI and outbound sync hold them back.

`score()` is a pure function (no DB) so the policy is unit-tested directly.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from ..config import SYSTEM_PRECEDENCE

# Distance-from-person per source: 0 = the person/their own account; higher =
# more removed. CRM/member rolls are near; event lists mid; OCR scans far.
DISTANCE = {
    "lightfield": 1, "jobtread": 1, "quickbooks": 1, "buildingconnected": 1,
    "quo": 1, "approved_subs": 1, "buildingconnectd": 1, "tips": 1,
    "luncheon": 2, "cjp_pdf": 3,
    # Google Workspace sweep channels (closest -> farthest from the person).
    "gcontacts": 0, "gmail_signature": 0, "people_api": 1, "gmail_from": 1,
    "calendar_organizer": 1, "gmail_to": 2, "calendar_attendee": 2,
    "drive_author": 2,
    "connector:formfill": 1, "connector:schedules": 1,
}
_DEFAULT_DISTANCE = 2

WEIGHTS = {"source": 0.35, "recency": 0.30, "corroboration": 0.20, "distance": 0.15}
FRESH_DECAY_DAYS = 540      # ~18 months to half-ish via exp decay
EXPOSE_MAX_AGE_DAYS = 730   # older than this -> held back regardless of grade
EXPOSE_MIN_GRADE = 0.40     # below this -> held back


def score(source_rank: int, age_days: int | None, corroboration: int,
          min_distance: int | None) -> float:
    """Combine the four axes into a probability grade in [0, 1]."""
    source_s = min(max(source_rank, 0), 100) / 100.0
    recency_s = math.exp(-(age_days or 0) / FRESH_DECAY_DAYS) if age_days is not None else 0.5
    corrob_s = 1.0 - 1.0 / (1 + max(corroboration, 0))      # 1 src .50, 2 .67, 3 .75
    dist = min_distance if min_distance is not None else _DEFAULT_DISTANCE
    distance_s = 1.0 / (1 + max(dist, 0))                   # d0 1.0, d1 .50, d2 .33
    g = (WEIGHTS["source"] * source_s + WEIGHTS["recency"] * recency_s
         + WEIGHTS["corroboration"] * corrob_s + WEIGHTS["distance"] * distance_s)
    return round(g, 4)


def band(g: float) -> str:
    return "A" if g >= 0.8 else "B" if g >= 0.6 else "C" if g >= 0.4 else "D"


def _parse_ts(ts) -> datetime | None:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    s = str(ts).strip()
    if not s:
        return None
    try:  # handles date, 'YYYY-MM-DD HH:MM:SS', and ISO-8601 incl. trailing Z
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _age_days(ts: datetime | None) -> int | None:
    if ts is None:
        return None
    now = datetime.now(timezone.utc) if ts.tzinfo else datetime.utcnow()
    return max(0, (now - ts).days)


@dataclass
class GradeStats:
    graded: int = 0
    exposed: int = 0
    held: int = 0
    bands: dict | None = None

    def as_dict(self) -> dict:
        return {"graded": self.graded, "exposed": self.exposed, "held": self.held,
                "bands": self.bands or {}}


class Grader:
    def __init__(self, conn):
        self.conn = conn
        self.backend = getattr(conn, "backend", "sqlite")

    def _collect(self) -> dict[int, dict]:
        """Per live contact: distinct sources + freshest last_seen observation."""
        rows = self.conn.execute(
            "SELECT sr.contact_id AS cid, sr.source AS source, sr.last_seen_at AS seen "
            "FROM source_records sr JOIN contacts c ON c.contact_id = sr.contact_id "
            "WHERE sr.contact_id IS NOT NULL AND c.is_deleted = 0")
        agg: dict[int, dict] = {}
        for r in rows:
            cid = r["cid"]
            a = agg.setdefault(cid, {"sources": set(), "freshest": None})
            a["sources"].add(r["source"])
            ts = _parse_ts(r["seen"])
            if ts and (a["freshest"] is None or ts > a["freshest"]):
                a["freshest"] = ts
        return agg

    def run(self, apply: bool = True) -> dict:
        agg = self._collect()
        st = GradeStats(bands={"A": 0, "B": 0, "C": 0, "D": 0})
        for cid, a in agg.items():
            sources = a["sources"]
            source_rank = max((SYSTEM_PRECEDENCE.get(s, 0) for s in sources), default=0)
            min_distance = min((DISTANCE.get(s, _DEFAULT_DISTANCE) for s in sources),
                               default=_DEFAULT_DISTANCE)
            age = _age_days(a["freshest"])
            g = score(source_rank, age, len(sources), min_distance)
            b = band(g)
            outdated = age is not None and age > EXPOSE_MAX_AGE_DAYS
            exposed = (g >= EXPOSE_MIN_GRADE) and not outdated
            reason = (f"band {b} ({g:.2f}); {len(sources)} source(s); "
                      f"{'age ' + str(age) + 'd' if age is not None else 'age n/a'}"
                      f"{'; OUTDATED held back' if outdated else ('' if exposed else '; low grade held back')}")
            st.graded += 1
            st.bands[b] += 1
            st.exposed += 1 if exposed else 0
            st.held += 0 if exposed else 1
            if apply:
                self._upsert(cid, g, b, len(sources), min_distance, a["freshest"],
                             age, int(exposed), reason)
        if apply:
            self.conn.commit()
        return st.as_dict()

    def _upsert(self, cid, g, b, sources, min_distance, freshest, age, exposed, reason):
        freshest_param = freshest  # datetime for PG, ISO string for SQLite
        if self.backend != "postgres":
            freshest_param = freshest.strftime("%Y-%m-%d %H:%M:%S") if freshest else None
        self.conn.execute(
            "INSERT INTO contact_grade(contact_id, grade, grade_band, sources, "
            "min_distance, freshest_at, age_days, is_exposed, is_synced, reason, computed_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now')) "
            "ON CONFLICT(contact_id) DO UPDATE SET grade=excluded.grade, "
            "grade_band=excluded.grade_band, sources=excluded.sources, "
            "min_distance=excluded.min_distance, freshest_at=excluded.freshest_at, "
            "age_days=excluded.age_days, is_exposed=excluded.is_exposed, "
            "is_synced=excluded.is_synced, reason=excluded.reason, "
            "computed_at=excluded.computed_at",
            (cid, g, b, sources, min_distance, freshest_param, age, exposed, exposed, reason))

    def get_grade(self, contact_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM contact_grade WHERE contact_id = ?", (contact_id,)).fetchone()
        return dict(row) if row else None
