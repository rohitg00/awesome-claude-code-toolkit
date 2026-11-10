"""F2b — mini model council (JEV default + cheap LLM escalation)."""
from ntxp_contacts.council import Council, decide
from ntxp_contacts.council.base import Task, Verdict
from ntxp_contacts.council.judges import DeepSeekJudge, JEVJudge


def test_jev_decides_for_free_when_confident():
    task = {"kind": "pick_value", "question": "best phone?",
            "options": [{"id": "A", "value": "x", "grade": 0.92},
                        {"id": "B", "value": "y", "grade": 0.40}]}
    out = decide(task)
    assert out["choice"] == "A"
    assert out["mode"] == "jev-only"
    assert out["cost"] == 0.0


def test_escalates_when_uncertain_but_still_decides_with_no_keys():
    task = {"kind": "pick_value", "question": "best email?",
            "options": [{"id": "A", "value": "x", "grade": 0.50},
                        {"id": "B", "value": "y", "grade": 0.48}]}
    out = decide(task)               # no API keys -> no LLM judges available
    assert out["mode"] == "escalated"
    assert out["choice"] in ("A", "B")
    assert out["cost"] == 0.0        # nothing spent
    assert len(out["provenance"]) == 1  # JEV only


class _Fake:
    name = "fake"
    cost = 0.1

    def available(self):
        return True

    def decide(self, task):
        return Verdict("B", 0.9, "fake", 0.1, "test")


def test_escalation_consults_llm_and_votes():
    council = Council(judges={"jev": JEVJudge(), "fake": _Fake()})
    task = Task("pick_value", "best?",
                [{"id": "A", "grade": 0.50}, {"id": "B", "grade": 0.48}])
    out = council.decide(task)
    judges = [p["judge"] for p in out["provenance"]]
    assert "fake" in judges and out["cost"] == 0.1
    assert out["choice"] == "B"       # fake's high-confidence vote wins


def test_llm_judge_gated_on_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert DeepSeekJudge().available() is False
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    assert DeepSeekJudge().available() is True


def test_abstain_on_no_options():
    out = decide({"kind": "pick_value", "question": "?", "options": []})
    assert out["choice"] is None


# -- persisted answers + effectiveness (Supabase-backed in production) ------------

def test_answers_persist_and_effectiveness(tmp_path):
    from ntxp_contacts.council import effectiveness, list_answers
    from ntxp_contacts.db import connect, migrate
    c = connect(tmp_path / "c.db")
    migrate(c)
    sure = {"kind": "pick_value", "question": "phone?",
            "options": [{"id": "A", "grade": 0.95}, {"id": "B", "grade": 0.3}]}
    unsure = {"kind": "pick_value", "question": "email?",
              "options": [{"id": "A", "grade": 0.5}, {"id": "B", "grade": 0.48}]}
    r1 = decide(sure, conn=c)
    r2 = decide(unsure, conn=c)
    assert r1["answer_id"] and r2["answer_id"] != r1["answer_id"]
    eff = effectiveness(c)
    assert eff["decisions"] == 2 and eff["resolved_free_by_jev_pct"] == 50.0
    assert eff["total_cost"] == 0.0
    recent = list_answers(c, 5)
    assert recent[0]["question"] == "email?" and recent[0]["voters"]
    # decision with no conn stays side-effect free
    assert "answer_id" not in decide(sure)


def test_pooler_disables_prepared_statements(monkeypatch):
    from ntxp_contacts.db.pg import _needs_no_prepare
    monkeypatch.delenv("NTXP_PG_NO_PREPARE", raising=False)
    assert _needs_no_prepare("postgresql://u:p@aws-0-us.pooler.supabase.com:6543/postgres")
    assert _needs_no_prepare("postgresql://u@host:6543/db")
    assert not _needs_no_prepare("postgresql://u@db.xyz.supabase.co:5432/postgres")
    monkeypatch.setenv("NTXP_PG_NO_PREPARE", "1")
    assert _needs_no_prepare("postgresql://u@host:5432/db")
