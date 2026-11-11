# Mini model council — contact decisions (F2b)

A near-zero-cost decision layer for contact qualification (which value / which
match / which class). Distinct from the document-parsing council in
`plugins/canonical-project-model`.

## Doctrine

- **JEV decides for free.** The deterministic `JEVJudge` scores options by their
  JEV grade and decides. If its confidence ≥ `JEV_CONFIDENCE` (0.75), that's the
  answer — **zero tokens spent**.
- **Escalate only when uncertain**, and only to the **cheapest available** LLM
  judge(s), within a per-decision cost budget. LLM judges vote; the router tallies
  a weighted vote and returns one verdict with full provenance. LLMs contribute a
  vote, never the write.
- **No keys → still works**, for free, on JEV alone. Keys are opt-in per model.

## Judges (cheap, OpenAI-compatible, key-gated)

| Judge | Env key | Default model | Rel. cost | Notes |
|---|---|---|---|---|
| `jev` | — | (deterministic) | **0.0** | always on; the default decider |
| `deepseek` | `DEEPSEEK_API_KEY` | `deepseek-chat` | 0.1 | cheapest LLM; ~$0.27/$1.10 per M tok (verify current) |
| `grok` | `XAI_API_KEY` | `grok-3-mini` | 0.2 | xAI, cheap mini tier |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` | 0.3 | OpenAI; swap to a nano tier as available |

Each model, endpoint, and the model id are env-overridable
(`<KEY>_MODEL`, `<KEY>_ENDPOINT`) so pricing/model swaps need no code change —
near-zero maintenance. Adding a judge is a ~10-line subclass of `_HTTPJudge`.

**ChatGPT "decisions"**: implemented via OpenAI chat/completions with
`response_format: json_object` (a structured decision). If/when the Responses API
adds a better structured-decision surface, point `OPENAI_API_KEY_ENDPOINT` at it.

## Use

```bash
ntxp council task.json        # {kind, question, options:[{id,value,grade?,evidence?}]}
```
or the `council_decide` MCP tool. Returns `{choice, confidence, cost, mode,
voters, provenance}`.

## Where it plugs in

- **Enrichment**: pick the best candidate value for a field (options = the
  proposed `enrichment_candidates`, each with its JEV grade).
- **LinkedIn match**: decide whether a proposed profile is the person (options =
  candidate profiles + evidence) before `confirm_linkedin`.
- **Classification**: choose a label/role/contact-type when several are plausible.
