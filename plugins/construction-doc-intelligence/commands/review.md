# /construction-doc-intelligence:review

Review one or more construction documents end-to-end and return decision-ready
output. Orchestrates the `construction-doc-pipeline`: extract with `mistral-ocr4`,
route to the right domain-review skill, apply `lean-pm-judgment`, present, and
feed the outcome to `agentic-self-improvement`.

## Steps

1. **Triage.** Inventory the documents and classify each (RFP/solicitation, vendor
   bid/quote, invoice/pay-app, submittal, engineering/design). Classify in parallel.
   Decide, from `lean-pm-judgment`, what the user actually needs to decide and the
   least work that decides it.
2. **Extract.** Hand each document to the **`mistral-ocr4`** MCP (`ocr_process`),
   fanning out per-document / per-page-range; for hundreds of docs use `batch_create`.
   Request a doc-type `*_annotation_format` schema (see each domain skill) so
   structured fields return with the text. Collect the extraction envelopes.
3. **Review.** Route each envelope to its domain skill — `rfp-analysis`,
   `vendor-bid-leveling`, `invoice-reconciliation`, `submittal-review`, or
   `engineering-design-review` — running independent reviews concurrently.
4. **Judge.** Apply `lean-pm-judgment`: rank findings by risk, recompute critical
   numbers, quote binding language verbatim, draft RFIs/clarifications, and make the
   call (award / pay / approve-as-noted / go-no-go) with a stated confidence.
5. **Present.** Synthesize the requested deliverable (memo, compliance matrix,
   leveling sheet, pay recommendation, coordination/RFI log) carrying citations
   (source doc, page index, bbox) and confidence throughout.
6. **Improve.** Pass the result and rubric to `agentic-self-improvement` to score,
   verify high-stakes findings, and record lessons for next time.

## Output

A senior-PM review: recommendation first, ranked risks, cited findings, open
questions / next actions, and confidence.

## Rules

- Mistral extracts; Claude reasons. Never ask Mistral to compare, score, or decide.
- Don't duplicate `mistral-ocr4` (extraction) or the domain skills (reasoning).
- Parallelize independent documents/pages/reviews; only synthesis is a barrier.
- Re-check OCR'd numbers and binding language before they drive a recommendation.
- Make small decisions yourself; escalate only decision-changing gaps.
