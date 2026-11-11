---
name: construction-doc-pipeline
description: Master orchestration skill for reviewing complex RFP, vendor, invoicing, submittal, and engineering/design documents end-to-end - routes documents through Mistral OCR4 extraction, the right domain-review skill, senior-PM judgment, presentation, and a self-improvement loop
---

# Construction Document Intelligence — Pipeline

The orchestration layer that turns a pile of construction documents into reviewed,
risk-flagged, decision-ready output. It chains existing tools and skills; it does
not duplicate them.

**The spine of the whole system:**
> **Mistral OCR4 extracts. Claude reasons. The pipeline routes.**
> Extraction is delegated to the `mistral-ocr4` MCP layer; reasoning is owned by
> Claude wearing the `lean-pm-judgment` hat; the pipeline decides which document
> goes to which reviewer and how the results come together. Each stage is a
> separate, swappable node connected by a stable contract.

## Stages

1. **Intake & triage.** Inventory the documents; classify each (RFP/solicitation,
   vendor bid/quote, invoice/pay-app, submittal, engineering/design). Conversational
   intent (the plugin's `UserPromptSubmit` hook) or an explicit `/construction-doc-intelligence:review`
   kicks this off. Run classification in parallel across the set.
2. **Extract.** Hand each document to **`mistral-ocr4`** (`ocr_process`, fan out
   per-document / per-page-range, Batch for bulk). Request a per-doc-type
   `*_annotation_format` schema so structured fields come back with the text.
   The output is the **extraction envelope** — the contract below.
3. **Review.** Route each envelope to its domain skill:
   - RFP / solicitation / addenda → **`rfp-analysis`**
   - Vendor / subcontractor bids → **`vendor-bid-leveling`**
   - Invoices / pay applications → **`invoice-reconciliation`**
   - Submittals / product data / shop drawings → **`submittal-review`**
   - Drawings / specs / calcs → **`engineering-design-review`**
   Reviews for independent documents run concurrently.
4. **Judge.** Apply **`lean-pm-judgment`** across the reviewed results — prioritize
   by risk and value, make decisive recommendations, surface what's missing, and
   generate the RFIs / clarifications / go-no-go calls a senior PM would.
5. **Present.** Synthesize into the requested deliverable (summary memo, compliance
   matrix, leveling sheet, pay recommendation, coordination/RFI log). Always carry
   citations (source doc, page index, bbox) and confidence through to the output.
6. **Improve.** Feed outcomes back through **`agentic-self-improvement`** — score the
   review against a rubric, capture corrections, and refine prompts/schemas/routing
   for next time.

## The handoff seam (extraction envelope)

Every downstream skill depends only on this shape from `mistral-ocr4`, never on
how it was produced:

- `pages[].index`, `pages[].markdown` — reading-order text per page.
- `pages[].blocks[]` — paragraph blocks with `bbox` + structural `label`
  (title, table, list, figure, caption, header, footer, signature, …).
- `pages[].images[]` — extracted figures / cut sheets / drawing crops.
- `document_annotation` / per-block annotations — schema-defined fields.
- `confidence` — per page/word; low-confidence regions are flagged, never silently trusted.
- **Provenance** — source doc id/path, page ranges, model, annotation schema used.

Downstream skills emit a parallel **review envelope**: `{ doc_id, doc_type,
findings[], risks[], recommendations[], citations[], open_questions[], confidence }`.
Keep these shapes stable so any node can be replaced without touching the others.

## Operating principles (lean management)

- **Pull, don't push.** Do the minimum extraction and analysis the decision needs;
  don't OCR every page at max settings when triage shows only the bid schedule matters.
- **Surface risk early.** A blocking exclusion, a missing addendum, an over-billing
  found in stage 3 short-circuits the rest — report it immediately.
- **Single source of truth.** Quote binding language verbatim with citations; never
  paraphrase a requirement, price, or dimension into the output.
- **Parallel by default.** Independent documents, pages, and reviews fan out; only
  synthesis is a barrier.
- **Agentic independence.** Choose input modes, schemas, models, and routing yourself
  from `lean-pm-judgment`; ask the user only for genuinely decision-changing gaps.

## Boundaries — don't duplicate

- Extraction lives in `mistral-ocr4`. Don't re-OCR or re-implement file I/O here.
- Reasoning lives in the domain skills + `lean-pm-judgment`. Don't push it into Mistral.
- Self-improvement lives in `agentic-self-improvement`. Don't hardcode tuning here.

## Anti-patterns

- Running stages strictly serially when documents are independent.
- Letting OCR'd numbers (bid amounts, quantities, totals) flow to a recommendation
  without an arithmetic/confidence re-check.
- Dropping citations or provenance during synthesis.
- Asking Mistral to compare, score, or decide.
- Boiling the ocean — full max-effort extraction before triage narrows scope.

## Checklist

- [ ] Documents inventoried and classified (in parallel).
- [ ] Each routed to `mistral-ocr4` with a doc-type annotation schema.
- [ ] Each envelope routed to the correct domain review skill (concurrently).
- [ ] `lean-pm-judgment` applied: risks ranked, recommendations decisive, gaps listed.
- [ ] Output carries citations + confidence; binding language quoted verbatim.
- [ ] Outcome fed to `agentic-self-improvement` for the next iteration.
