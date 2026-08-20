# /construction-doc-intelligence:improve

Run the self-improvement loop over a completed (or sampled) document review. Scores
the review against a rubric, adversarially verifies high-stakes findings, and turns
recurring misses into durable fixes to the pipeline's prompts, annotation schemas,
and routing. Implements the `agentic-self-improvement` skill.

## Steps

1. **Gather.** Collect the review under test plus its inputs — the extraction
   envelope, the annotation schema used, and the stage prompt.
2. **Rubric.** Use (or derive from a known-good review) an explicit, gradeable
   rubric for that document type.
3. **Grade.** Run an *independent* `claude-opus-4-8` call (fresh context,
   `output_config.format` structured verdict) to score each criterion with evidence
   and a `pass | revise | fail` verdict. Cache the rubric prefix.
4. **Verify.** For money- or safety-critical findings (award, pay release, submittal
   approval, field clash), fan out 2–3 parallel verifier calls prompted to refute;
   keep the finding only if a majority fail to refute.
5. **Fix.** One-off miss → inject the correction and re-run the stage. Recurring
   miss → change the underlying prompt / `*_annotation_format` / routing rule so the
   class of error can't recur.
6. **Record.** Append the lesson to improvement memory (one per entry: summary,
   trigger, durable fix); consult it on future runs.
7. **Stop** on rubric pass, max-iteration cap, or K consecutive clean grades.

## Output

A graded verdict with per-criterion evidence, the verified findings, the concrete
process changes applied, and the lesson recorded.

## Rules

- The grader is never the author — separate call, separate context.
- Improve process (prompts/schemas/routing), never evidence (values, quotes,
  citations).
- Every verdict cites evidence; a citation-free "pass" is not a pass.
- The loop must have an iteration cap and a convergence stop.
