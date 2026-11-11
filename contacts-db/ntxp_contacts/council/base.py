"""Council task/verdict shapes and the judge registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Task:
    kind: str                       # pick_value | match | classify
    question: str
    options: list[dict]             # each: {id, value, grade?, source?, evidence?}
    context: dict = field(default_factory=dict)


@dataclass
class Verdict:
    choice: str | None              # option id (or None = abstain)
    confidence: float               # 0..1
    judge: str
    cost: float = 0.0               # relative $ for this call (0 = free)
    rationale: str = ""


class Judge(Protocol):
    name: str
    cost: float                     # relative cost rank (0 = free)

    def available(self) -> bool: ...
    def decide(self, task: Task) -> Verdict: ...


JUDGES: dict[str, Judge] = {}


def register_judge(cls):
    """Class decorator: register a singleton instance of the judge."""
    JUDGES[cls.name] = cls()
    return cls
