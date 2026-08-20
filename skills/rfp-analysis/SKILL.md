---
name: rfp-analysis
description: Reason over an extracted RFP/solicitation/bid-package envelope (from mistral-ocr4) to build a compliance matrix, reconcile addenda, rank evaluation criteria, and produce a cited go/no-go recommendation - reasoning only, never re-OCR
---

# RFP / Solicitation Analysis

This skill is the **reasoning** node for RFPs, solicitations, and bid packages in
the `construction-doc-pipeline`. It **consumes** the extraction envelope produced
by `mistral-ocr4` and turns it into a structured, cited analysis that the
presentation/synthesis step renders for an estimator or PM.

**The one rule that shapes everything:**
> **Mistral extracts. This skill reasons.**
> Never re-OCR a document you already have an envelope for, and never ask Mistral
> to evaluate, score, or judge compliance. Reading fields, comparing them against
> requirements, deciding go/no-go — that is this skill's job.

Apply the `lean-pm-judgment` lens throughout: operate with the agency of a senior
construction PM / estimator. Surface risk early, quote binding language, and make
a decisive recommendation rather than hedging.

## Inputs: the extraction envelope

Read (never mutate) the raw Mistral JSON from `ocr_process`:

- `pages[].markdown` — reading-order text; primary source for verbatim quotes.
- `pages[].blocks[]` — each has a `bbox` and structural `label` (title, table,
  list, header, footer, signature). Use `label` to find scope tables, eval-
  criteria tables, and signature/acknowledgement pages (addenda receipts).
- `pages[].images[]` — site plans, logos, stamped pages.
- `document_annotation` / per-block annotations — present when an
  `*_annotation_format` schema was requested. Prefer these over regexing markdown.
- `confidence` — per page/word. Flag low-confidence regions; never silently trust
  a due date or dollar figure pulled from a low-confidence block.

**Provenance is mandatory.** Carry `source_doc_id`, `page` index, `bbox`, and the
OCR `model` through to every citation in your output. A requirement without a
page/bbox citation is not done.

## Annotation schema to request for RFPs

When the upstream `ocr_process` call can take a `document_annotation_format`,
request these fields (capture verbatim — define *what* to capture, not how to
judge it):

```json
{
  "solicitation_no": "string",
  "issuing_owner": "string",
  "due_date": "string", "due_time": "string", "time_zone": "string",
  "submission_method": "string",
  "site": "string", "project_location": "string",
  "scope_items": ["string"],
  "required_submittals": ["string"],
  "evaluation_criteria": [{ "criterion": "string", "weight": "string", "page": "int" }],
  "insurance_requirements": ["string"],
  "bonding_requirements": ["string"],
  "wage_requirements": "string",
  "addenda": [{ "number": "string", "date": "string", "page": "int" }],
  "qa_deadline": "string", "pre_bid_meeting": "string",
  "page_references": ["int"]
}
```

Fall back to reading `pages[].markdown` + `blocks[]` for any field the schema
missed; cite by page index either way.

## Parallel processing

RFP packages are large and arrive as base RFP + multiple addenda + exhibits. Fan
out, don't serialize:

- Hand the upstream `mistral-ocr4` skill all documents / page ranges in one batch
  so extraction runs concurrently; stitch results by page index.
- Analyze each addendum's envelope in parallel, then reconcile (below).
- Keep each unit of work independent; cite by `source_doc_id` + page index so
  results merge cleanly regardless of completion order.

## Build the compliance matrix

The core deliverable. One row per binding requirement:

| requirement (verbatim) | source (doc/page/bbox) | type | how we address it | status | owner | risk |

- **Quote requirements verbatim.** Binding language ("shall", "must", "will be
  deemed non-responsive") loses meaning when paraphrased. Paste the exact text.
- Derive rows from `scope_items`, `required_submittals`, insurance/bonding,
  wage/prevailing-wage, certifications, format/page-limit, and submission-method
  requirements.
- `status` ∈ {addressed, partial, gap, needs-info, n/a}. Every `gap` and
  `needs-info` feeds the missing-information list and the go/no-go.
- Hand required-submittal rows to **submittal-review** for downstream tracking.

## Reconcile addenda against the base RFP

Addenda supersede the base. Reconciliation is non-negotiable:

- Enumerate every addendum from the `addenda[]` annotation **and** by scanning for
  acknowledgement/signature blocks — a missing addendum is a classic disqualifier.
- For each, produce a change list: field/clause changed, old value, new value,
  effective doc/page. Mark what **supersedes** prior text.
- Re-point compliance-matrix rows to the governing (latest) source. Note any
  conflict where two addenda touch the same clause.
- Verify the bid due date/time against the **latest** addendum, not the base RFP.

## Rank evaluation criteria

- Extract `evaluation_criteria[]` **verbatim** with stated weights/points.
- Normalize to a ranking by weight; flag criteria with no stated weight as a
  judgment risk. Distinguish pass/fail gates from scored/weighted criteria.
- Map each criterion to where our response/strengths will satisfy it; this drives
  win-theme emphasis for the synthesis step.

## Go / no-go recommendation

Make the call. Structure it as:

- **Recommendation:** Go / No-Go / Conditional-Go (state the conditions).
- **Rationale:** tied to scope fit, evaluation weighting, schedule, and capacity.
- **Key risks:** ranked; each cites the requirement (doc/page) that drives it.
- **Missing-information list:** open items, each as a question for the Q&A
  deadline, with the `qa_deadline` date attached.
- **Critical dates:** Q&A deadline, pre-bid meeting, due date/time/zone — from the
  latest governing source.

Cross-references: feed incoming bids to **vendor-bid-leveling**; feed required
submittals to **submittal-review**. Hand the full structured result (matrix +
addenda reconciliation + criteria ranking + recommendation, all with provenance)
to the presentation/synthesis step.

## Anti-Patterns

- Paraphrasing binding requirements instead of quoting them verbatim.
- Missing or skipping an addendum — and trusting the base RFP's due date.
- Asking Mistral to "tell me if we're compliant" or to score eval criteria.
- Re-OCRing a document that already has an extraction envelope.
- Ignoring low-confidence OCR regions on load-bearing fields (dates, dollars,
  bond amounts) instead of flagging them for human verification.
- Emitting a requirement, risk, or recommendation with no page/bbox citation.
- Hedging the go/no-go into a non-answer instead of a decisive, conditioned call.
- Mutating extracted values to "clean them up" before analysis.

## Checklist

- [ ] Consumed the `mistral-ocr4` envelope; did not re-OCR.
- [ ] RFP annotation schema requested upstream; markdown/blocks used for gaps.
- [ ] OCR + analysis fanned out across pages and all addenda in parallel.
- [ ] Compliance matrix built; every requirement quoted verbatim with doc/page/bbox.
- [ ] All addenda enumerated and reconciled; matrix points to governing source.
- [ ] Evaluation criteria extracted verbatim and ranked by weight.
- [ ] Due date/time verified against the latest addendum.
- [ ] Low-confidence regions on critical fields flagged.
- [ ] Go/no-go made with rationale, ranked risks, and missing-info list.
- [ ] Provenance (source_doc_id, page, bbox, model) preserved end to end.
- [ ] Hand-offs set: vendor-bid-leveling (bids), submittal-review (submittals).
