"""Mini model council for contact-qualification decisions.

Near-zero cost by construction: the deterministic **JEV** judge decides for free
and only escalates to cheap LLM judges (DeepSeek / Grok / OpenAI) when it is
uncertain. LLM judges contribute evidence (a vote), never the final write — the
router tallies a weighted vote and returns one verdict with full provenance.

This is the *decisions* council (which value / which match / which class). The
document-parsing council lives in `plugins/canonical-project-model` and is
separate.
"""
from .base import Task, Verdict, Judge, JUDGES, register_judge
from .router import Council, decide, save_answer, list_answers, effectiveness

__all__ = ["Task", "Verdict", "Judge", "JUDGES", "register_judge", "Council", "decide",
           "save_answer", "list_answers", "effectiveness"]
