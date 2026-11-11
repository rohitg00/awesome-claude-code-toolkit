"""Judges: the free deterministic JEV judge + cheap, key-gated LLM judges.

LLM judges are OpenAI-compatible chat/completions calls (DeepSeek, xAI Grok,
OpenAI), stateless, activated only when their API key is present — so with no
keys the council still runs, for free, on JEV alone. Models/endpoints are env-
overridable for near-zero-maintenance swaps as pricing changes.
"""
from __future__ import annotations

import json
import os
import urllib.request

from .base import Task, Verdict, register_judge


def _score(opt: dict) -> float:
    if isinstance(opt.get("grade"), (int, float)):
        return float(opt["grade"])
    try:
        from ..enrich.grade import base_grade
        return base_grade(opt.get("source", ""))
    except Exception:
        return 0.4


@register_judge
class JEVJudge:
    name = "jev"
    cost = 0.0

    def available(self) -> bool:
        return True

    def decide(self, task: Task) -> Verdict:
        if not task.options:
            return Verdict(None, 0.0, self.name, 0.0, "no options")
        scored = sorted(((o, _score(o)) for o in task.options), key=lambda x: x[1], reverse=True)
        top, top_s = scored[0]
        second_s = scored[1][1] if len(scored) > 1 else 0.0
        margin = top_s - second_s
        conf = min(1.0, round(top_s * (0.6 + 0.4 * min(margin / 0.3, 1.0)), 4))
        return Verdict(str(top.get("id")), conf, self.name, 0.0,
                       f"highest grade {top_s:.2f}, margin {margin:.2f}")


class _HTTPJudge:
    """OpenAI-compatible chat/completions judge."""
    name = "http"
    cost = 0.5
    endpoint = ""
    model = ""
    key_env = ""

    def available(self) -> bool:
        return bool(os.environ.get(self.key_env))

    def decide(self, task: Task) -> Verdict:
        key = os.environ.get(self.key_env)
        if not key:
            return Verdict(None, 0.0, self.name, 0.0, "no api key")
        opts = "\n".join(
            f"- id={o.get('id')}: {o.get('value')}"
            f"{(' | evidence=' + json.dumps(o.get('evidence'))) if o.get('evidence') else ''}"
            for o in task.options)
        sys_msg = ("You are a terse decision judge for a contacts database. Pick the "
                   "single best option id for the question. Reply ONLY as compact JSON: "
                   '{"choice": "<id or null>", "confidence": 0..1, "rationale": "<short>"}.')
        user = f"Question: {task.question}\nKind: {task.kind}\nOptions:\n{opts}"
        payload = json.dumps({
            "model": os.environ.get(self.key_env + "_MODEL", self.model),
            "messages": [{"role": "system", "content": sys_msg},
                         {"role": "user", "content": user}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }).encode()
        req = urllib.request.Request(
            os.environ.get(self.key_env + "_ENDPOINT", self.endpoint), data=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.load(resp)
            content = data["choices"][0]["message"]["content"]
            out = json.loads(content)
            return Verdict(
                None if out.get("choice") in (None, "null") else str(out.get("choice")),
                float(out.get("confidence", 0.0)), self.name, self.cost,
                str(out.get("rationale", "")))
        except Exception as exc:  # any failure -> abstain, never crash the council
            return Verdict(None, 0.0, self.name, 0.0, f"error: {exc}")


@register_judge
class DeepSeekJudge(_HTTPJudge):
    name = "deepseek"
    cost = 0.1
    endpoint = "https://api.deepseek.com/chat/completions"
    model = "deepseek-chat"
    key_env = "DEEPSEEK_API_KEY"


@register_judge
class GrokJudge(_HTTPJudge):
    name = "grok"
    cost = 0.2
    endpoint = "https://api.x.ai/v1/chat/completions"
    model = "grok-3-mini"
    key_env = "XAI_API_KEY"


@register_judge
class OpenAIJudge(_HTTPJudge):
    name = "openai"
    cost = 0.3
    endpoint = "https://api.openai.com/v1/chat/completions"
    model = "gpt-4o-mini"
    key_env = "OPENAI_API_KEY"
