"""Council router: JEV decides for free; escalate to the cheapest available LLM
judges only when JEV is uncertain; tally a weighted vote with full provenance."""
from __future__ import annotations

from .base import JUDGES, Task, Verdict

JEV_CONFIDENCE = 0.75     # JEV >= this -> accept without spending a cent
DEFAULT_MAX_COST = 1.0    # relative budget per decision
DEFAULT_ESCALATE = 1      # how many LLM judges to consult on escalation


class Council:
    def __init__(self, judges: dict | None = None):
        from . import judges as _reg  # noqa: F401  (ensures registration)
        self.judges = judges if judges is not None else dict(JUDGES)

    def decide(self, task: Task, jev_threshold: float = JEV_CONFIDENCE,
               max_cost: float = DEFAULT_MAX_COST,
               escalate: int = DEFAULT_ESCALATE) -> dict:
        jev = self.judges["jev"].decide(task)
        verdicts = [jev]
        mode = "jev-only"
        if jev.choice is None or jev.confidence < jev_threshold:
            mode = "escalated"
            llm = sorted((j for n, j in self.judges.items() if n != "jev" and j.available()),
                         key=lambda j: j.cost)
            spent = 0.0
            for j in llm[:escalate]:
                if spent + j.cost > max_cost:
                    break
                v = j.decide(task)
                verdicts.append(v)
                spent += v.cost
        return self._finalize(verdicts, mode)

    @staticmethod
    def _finalize(verdicts: list[Verdict], mode: str) -> dict:
        tally: dict[str, float] = {}
        for v in verdicts:
            if v.choice is not None:
                tally[v.choice] = tally.get(v.choice, 0.0) + max(v.confidence, 0.01)
        cost = round(sum(v.cost for v in verdicts), 4)
        prov = [{"judge": v.judge, "choice": v.choice, "confidence": v.confidence,
                 "cost": v.cost, "rationale": v.rationale} for v in verdicts]
        if not tally:
            return {"choice": None, "confidence": 0.0, "cost": cost, "mode": mode,
                    "provenance": prov}
        choice = max(tally, key=lambda k: tally[k])
        backing = [v for v in verdicts if v.choice == choice]
        share = tally[choice] / sum(tally.values())
        avg = sum(v.confidence for v in backing) / len(backing)
        final = round(0.5 * share + 0.5 * avg, 4)
        return {"choice": choice, "confidence": final, "cost": cost, "mode": mode,
                "voters": sorted(v.judge for v in backing), "provenance": prov}


def save_answer(conn, task: dict, result: dict, contact_id: int | None = None) -> int:
    """Persist a council decision (consensus + provenance + cost) so its
    effectiveness can be audited later. Returns the answer id."""
    import json
    cur_id = None
    sql = ("INSERT INTO council_answers(kind, question, choice, confidence, cost, mode, "
           "voters, provenance, options, contact_id) VALUES (?,?,?,?,?,?,?,?,?,?)")
    params = (task.get("kind", "pick_value"), task.get("question", ""),
              result.get("choice"), float(result.get("confidence", 0.0)),
              float(result.get("cost", 0.0)), result.get("mode", ""),
              json.dumps(result.get("voters", [])),
              json.dumps(result.get("provenance", []), default=str),
              json.dumps(task.get("options", []), default=str),
              contact_id if contact_id is not None else task.get("contact_id"))
    if getattr(conn, "backend", "sqlite") == "postgres":
        cur_id = int(conn.execute(sql + " RETURNING answer_id", params).fetchone()[0])
    else:
        cur_id = int(conn.execute(sql, params).lastrowid)
    conn.commit()
    return cur_id


def list_answers(conn, limit: int = 50) -> list[dict]:
    import json
    out = []
    for r in conn.execute(
            "SELECT answer_id, kind, question, choice, confidence, cost, mode, voters, "
            "contact_id, created_at FROM council_answers ORDER BY answer_id DESC LIMIT ?",
            (limit,)).fetchall():
        d = dict(r)
        d["voters"] = json.loads(d.get("voters") or "[]")
        d["created_at"] = str(d["created_at"])
        out.append(d)
    return out


def effectiveness(conn) -> dict:
    """Consensus-of-effectiveness summary over all persisted answers."""
    rows = conn.execute(
        "SELECT mode, COUNT(*) n, AVG(confidence) conf, SUM(cost) cost "
        "FROM council_answers GROUP BY mode").fetchall()
    total = sum(r["n"] for r in rows)
    free = sum(r["n"] for r in rows if r["mode"] == "jev-only")
    return {
        "decisions": total,
        "resolved_free_by_jev_pct": round(100 * free / total, 1) if total else None,
        "total_cost": round(sum((r["cost"] or 0) for r in rows), 4),
        "by_mode": {r["mode"]: {"n": r["n"], "avg_confidence": round(r["conf"] or 0, 3)}
                    for r in rows},
    }


def decide(task: dict, conn=None, **opts) -> dict:
    """Run the default council on a task dict. If `conn` is given, the decision
    is persisted to council_answers and its id returned as `answer_id`."""
    t = Task(kind=task.get("kind", "pick_value"),
             question=task.get("question", ""),
             options=task.get("options", []),
             context=task.get("context", {}))
    result = Council().decide(t, **opts)
    if conn is not None:
        result["answer_id"] = save_answer(conn, task, result)
    return result
