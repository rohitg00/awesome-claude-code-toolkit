---
name: agentic-self-improvement
description: A self-improving agentic loop for the construction-doc-intelligence pipeline - score each document review against a rubric with the Claude API, capture corrections, and iteratively refine the prompts, annotation schemas, and routing so the pipeline gets sharper every run
---

# Agentic Self-Improvement Loop

The pipeline's kaizen engine. It closes the loop: a review is produced, an independent
grader scores it against a rubric, gaps become corrections, and the corrections become
durable improvements to prompts, schemas, and routing — so the next run is better than the last.
Built on the Claude API (`claude-opus-4-8`).

This is process improvement, not fact generation. It never edits the *evidence* in a
review — it improves *how the pipeline reaches* the review.

## The loop

```
produce → grade (independent) → diff vs rubric → revise → record → repeat
```

1. **Produce.** Run a pipeline stage (e.g. `vendor-bid-leveling`) and capture its
   review envelope plus the inputs (extraction envelope, annotation schema, prompt).
2. **Grade.** A *separate* Claude call — fresh context, the model never sees its own
   reasoning — scores the review against an explicit, gradeable rubric.
3. **Diff.** Turn each unmet criterion into a concrete correction with a citation.
4. **Revise.** Either re-run the stage with the corrections injected, or — when the
   miss is systemic — change the underlying prompt / annotation schema / routing rule.
5. **Record.** Append the lesson to the improvement memory so it survives the session.
6. **Repeat** until the rubric passes, a max-iteration cap is hit, or no new gaps
   surface across K consecutive grades.

## Grading with the Claude API

Use a constrained, structured grader so verdicts are machine-usable. Keep the rubric
and system prompt as a stable cached prefix; vary only the review under test.

```python
import anthropic
client = anthropic.Anthropic()

RUBRIC = """..."""  # explicit, independently checkable criteria — see "Writing rubrics"

resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=8000,
    thinking={"type": "adaptive"},            # let the grader reason; 4.6+ adaptive only
    output_config={
        "effort": "high",                      # grading is correctness-sensitive
        "format": {                            # structured verdict, not prose
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "criteria": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "passed": {"type": "boolean"},
                            "evidence": {"type": "string"},
                            "fix": {"type": "string"},
                        },
                        "required": ["id", "passed", "evidence", "fix"],
                        "additionalProperties": False,
                    }},
                    "verdict": {"type": "string", "enum": ["pass", "revise", "fail"]},
                    "score": {"type": "number"},
                },
                "required": ["criteria", "verdict", "score"],
                "additionalProperties": False,
            },
        },
    },
    system=[{"type": "text", "text": RUBRIC + GRADER_INSTRUCTIONS,
             "cache_control": {"type": "ephemeral"}}],   # stable prefix → cache hits
    messages=[{"role": "user", "content": review_under_test}],
)
```

Notes grounded in the current API: `claude-opus-4-8` uses **adaptive thinking only**
(no `budget_tokens`); control depth with `output_config.effort`. Use
`output_config.format` (not the deprecated `output_format`) for the structured verdict.
Cache the rubric+instructions prefix so repeated grading is cheap; put the varying
review *after* the breakpoint. Check `stop_reason` before reading content.

## Independence & robustness

- **Grader ≠ author.** Score in a separate call with its own context; a model grading
  its own visible reasoning inflates the score.
- **Adversarial verify high-stakes findings.** For a recommendation that releases
  money or approves fabrication, fan out 2–3 independent verifier calls each prompted
  to *refute* the finding; keep it only if a majority fail to refute. Run them in
  parallel (one user message → many calls); they're independent.
- **Ground every verdict in evidence.** A "passed" with no citation is not a pass.

## What gets improved (and what doesn't)

| Improve (process)                         | Never touch (evidence)                     |
| ----------------------------------------- | ------------------------------------------ |
| Stage prompts / review instructions       | Extracted values, quantities, totals       |
| `*_annotation_format` schemas requested   | Quoted binding requirements                |
| Routing / triage rules                    | Citations and provenance                   |
| Which pages/effort/model a stage uses     | The grader's evidence requirement          |

When a miss is one-off, inject the correction and re-run. When it recurs, change the
process artifact (prompt or schema) so the class of miss can't happen again — that's
the difference between patching and improving.

## Improvement memory

Persist lessons so the loop compounds across sessions. One lesson per entry, with a
one-line summary, the trigger, and the durable fix; update an existing note rather than
duplicating; delete notes that prove wrong. (Use a project memory file, or the memory
tool / a memory store if running as a managed agent.) Consult it before running a stage.

## Writing rubrics

Explicit and independently gradeable beats vibes. Good: "every binding RFP requirement
is quoted verbatim with a page citation"; "all invoice line extensions recomputed and
discrepancies flagged"; "the recommendation states a confidence level." Bad: "the
analysis is thorough." If you lack a rubric, have Claude derive one from a known-good
review and reuse it.

## Budgeting the loop

Scale effort to stakes: a quick triage gets one grade; an award recommendation or a
pay decision gets adversarial verification and more iterations. Cap iterations and
stop on convergence (K consecutive clean grades) so the loop terminates.

## Anti-patterns

- Grading with the same context that produced the review.
- Vague rubrics that can't fail anything.
- "Improving" by editing extracted facts or citations.
- Patching one output instead of fixing the recurring process cause.
- Unbounded loops with no convergence/iteration cap.
- Skipping adversarial verification on money/safety-critical recommendations.

## Checklist

- [ ] Independent grader call with a structured, evidence-backed verdict.
- [ ] Rubric explicit and gradeable; stable prefix cached.
- [ ] High-stakes findings adversarially verified in parallel.
- [ ] Systemic misses fixed in the prompt/schema/routing, not just the output.
- [ ] Lesson recorded to improvement memory; consulted next run.
- [ ] Loop has a max-iteration cap and a convergence stop.
