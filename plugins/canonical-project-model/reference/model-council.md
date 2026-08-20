# Parsing Model Council — escalation blueprint

## Doctrine

**Single-model path is the default.** Mistral OCR4 extracts; Claude reasons. That
pipeline handles the overwhelming majority of document parsing without help.

**The council is an exception path, for document parsing only.** It exists for the
narrow slice of cases where a single reasoning pass is not enough to trust the
result — not as a standing multi-model pipeline.

Claude retains **final authority** on intent, normalization, and anything written to
the canonical model. Council members contribute **evidence, never verdicts**. A
second model can raise a flag, propose a value, or confirm a reading — it cannot
decide what goes in the model. That decision, and the responsibility for it, stays
with Claude.

## Roster & roles

| Member | Role | Used for |
|---|---|---|
| **Gemini** (vision) | Second-pass vision/OCR | Google OCR cross-check on low-confidence regions; reading drawings/schedules as images; "fix it as a vision" tasks — re-reading a bad crop, verifying a dimension against the sheet image. |
| **Claude** | Wisdom & intent | Interprets what the user/document actually means; adjudicates disagreements between members; owns final normalization and **all writes** to the canonical model. |
| **GPT ("Luna")** | Bulk action-taking | High-volume microtasks — per-page field checks, row-by-row table verification, checklist sweeps; microtask reviews; drafting the council's findings report. |

## Trigger policy — when to convene

The council does **not** convene all the time. It convenes only when one of these
trips:

1. **Ambiguous input.** The user's ask is vague about what a document says, or what
   they want done with it.
2. **Disengaged user + non-trivial stakes.** Replies are short, low-signal, or
   incurious, and getting the parse wrong would matter. The council raises quality
   on its own rather than asking the user to spell things out.
3. **Fails the sniff test.** The single-model draft doesn't read like an
   industry-grade construction answer — wrong units, implausible quantities,
   non-CSI framing, missing scope language.
4. **Low confidence on binding values.** OCR4 confidence is below threshold on
   prices, quantities, or dates, or documents disagree with each other.

**Otherwise: do not convene.** Default path only.

## Flow

1. **OCR4 extract.** The dossier's verbatim extraction, as always.
2. **Gate check.** Evaluate the four triggers above against the extract and the
   single-model draft.
3. **If tripped, convene:**
   a. **Gemini vision** re-reads only the flagged regions/pages as images and
      returns values + confidence — not the whole document.
   b. **GPT Luna** fans out microtask verifications across the flagged set and
      drafts a findings report.
   c. **Claude adjudicates.** Agreements become normalized values with provenance
      noting corroboration. Disagreements go to `conflicts` / `needs_human_review` —
      never silently resolved.
4. **Log it.** Council invocation and every member's findings are recorded in
   `normalization_log`, including which trigger fired.

## Cost guards

- **Capped convenings.** Default: at most **one convening per document set per
  sync**. Escalate only the flagged regions — never re-run whole documents through
  the council.
- **Crops, not documents.** Members receive the specific crops/snippets relevant to
  the flag, not full documents, wherever possible.
- **Name the trigger.** Every convening states which of the four triggers fired.
  No trigger named, no convening.

## Wiring (stubs)

Council members are reached through **env-configured, Anthropic-/OpenAI-/
Google-compatible endpoints** chosen by the operator — e.g. `GEMINI_API_KEY`,
`OPENAI_API_KEY` / model ids set in env, or MCP connectors where available. This
file is the blueprint, not the wiring: no tool integration is assumed beyond what
the operator configures. Execution itself can run on cheaper models — the blueprint
is authored once by frontier intelligence and stored with the toolkit.

## Never

- The council never prices, levels bids, or decides awards.
- It never overrides provenance rules — a value still enters the model only if a
  document supports it.
- Members never receive reasoning authority; Claude's adjudication is the only path
  to a write.
