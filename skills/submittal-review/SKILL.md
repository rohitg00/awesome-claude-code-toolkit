---
name: submittal-review
description: Reason over an extracted submittal envelope (from mistral-ocr4) to check product data, shop drawings, and samples against the governing spec section, resolve substitutions, and recommend a stamp action with cited deviations - reasoning only, never re-OCR
---

# Submittal Review

This skill is the **reasoning** node for submittals (product data, shop drawings,
samples, material/equipment cut sheets, mill test reports) in the
`construction-doc-pipeline`. It **consumes** the extraction envelope produced by
`mistral-ocr4` and turns it into a cited, marked-up review that the
presentation/synthesis step renders for a PM, architect, or engineer of record.

**The one rule that shapes everything:**
> **Mistral extracts. This skill reasons.**
> Never re-OCR a package you already have an envelope for, and never ask Mistral to
> evaluate compliance, judge an "or-equal," or pick a stamp action. Reading the
> submitted attributes, comparing them against the spec, and deciding the
> reviewer's action — that is this skill's job.

Apply the `lean-pm-judgment` lens throughout: act with the agency of a senior
construction PM / SME. Surface risk early, quote the binding spec language, and
issue a decisive stamp action rather than punting everything to "Revise and
Resubmit."

## Inputs: the extraction envelope

Read (never mutate) the raw Mistral JSON from `ocr_process`:

- `pages[].markdown` — reading-order text; primary source for verbatim quotes of
  ratings, model numbers, and standards.
- `pages[].blocks[]` — each has a `bbox` and structural `label` (title, table,
  figure, signature, stamp, header, footer). Use `label` to find spec/data tables,
  the contractor review stamp, shop-drawing title blocks, and figures.
- `pages[].images[]` — product cut sheets, shop drawings, sample photos. A
  deviation is often buried in a cut-sheet image, not the body text.
- `document_annotation` / per-block annotations — present when an
  `*_annotation_format` schema was requested. Prefer these over regexing markdown.
- `confidence` — per page/word. Ratings, model numbers, and dimensions are exactly
  where OCR fails; never silently trust a low-confidence model_no or rating.

**Provenance is mandatory.** Carry `source_doc_id`, `page` index, `bbox`/`figure`,
and the OCR `model` through to every line of the review. An attribute or deviation
without a page/figure citation is not done.

## Annotation schema to request for submittals

When the upstream `ocr_process` call can take a `document_annotation_format`,
request these fields (capture verbatim — define *what* to capture, not how to
judge it):

```json
{
  "submittal_no": "string",
  "spec_section": "string (CSI MasterFormat, e.g. 08 41 13)",
  "submittal_type": "string (product data | shop drawing | sample | MTR)",
  "manufacturer": "string", "product": "string", "model_no": "string",
  "date": "string",
  "contractor_stamp": "string (present? reviewer/date/disposition)",
  "requested_action": "string (e.g. approval, for record)",
  "substitution_request": "string (yes | no)",
  "referenced_standards": ["string (ASTM/ANSI/UL/etc.)"],
  "dimensions_ratings": [{ "attribute": "string", "value": "string", "page": "int" }],
  "finishes": ["string"],
  "certifications": ["string"],
  "deviations": [{ "note": "string", "page": "int" }],
  "page_references": ["int"]
}
```

Fall back to reading `pages[].markdown` + `blocks[]` (and inspecting cut-sheet
`images[]`) for any field the schema missed; cite by page/figure either way.

## Parallel processing

Submittal logs are long and packages are multi-page. Fan out, don't serialize:

- Hand the upstream `mistral-ocr4` skill all submittals / page ranges in one batch
  so extraction runs concurrently; stitch results by `source_doc_id` + page index.
- Review each submittal's envelope in parallel; keep each unit independent.
- Within a package, attribute every finding to its page/figure so results merge
  cleanly regardless of completion order.

## Pull the governing spec section

You cannot review a submittal without the spec it answers to.

- Read the CSI `spec_section` off the submittal, then load the governing section's
  requirements (its own `mistral-ocr4` envelope, or the project spec already in the
  pipeline). Quote requirements **verbatim** — "shall," "minimum," "or approved
  equal" are load-bearing words.
- Cross-reference **rfp-analysis** `required_submittals` to confirm this submittal
  is actually required and to inherit its CSI mapping.
- If the governing spec section is not available, mark the review `needs-info`
  rather than approving against memory.

## Spec compliance check

The core deliverable. One row per spec-driven attribute:

| attribute | spec requirement (verbatim) | spec source (sec/page) | submitted value | submittal source (page/fig) | result | note |

- `result` ∈ {compliant, deviation, missing, needs-info}.
- Compare each attribute the spec governs: manufacturer/approved-mfr list,
  model, **performance ratings** (load, fire, U-factor, STC, pressure, etc.),
  **referenced standards** (ASTM/ANSI/UL — verify the cited edition), dimensions,
  tolerances, and finishes. A submittal can pass on every line yet cite the wrong
  standard edition — check it.
- Every `deviation` and `missing` carries a citation on **both** sides (spec and
  submittal) and a one-line corrective note.

## Substitution / "or-equal" handling

Do not conflate these — it is the most common reviewer error:

- **Approved equal** — spec permits "or approved equal" or names the product on an
  approved-manufacturers list. Verify it actually meets every salient spec
  characteristic; treat any shortfall as a deviation, not an automatic accept.
- **Substitution request** — a product not named/permitted by the spec. It requires
  a formal substitution form, side-by-side comparison to the specified product,
  cost/schedule impact, and (often) A/E review. Missing any of these → it cannot be
  evaluated as submitted; route to **Revise and Resubmit** or **Rejected**.
- Flag `substitution_request: yes` prominently and state exactly what is required to
  evaluate it.

## Completeness check

- All spec-required data present: every rating, dimension, certification, and
  (for samples) the required sample size/quantity and finish.
- Contractor's review stamp present and signed — an unstamped submittal is
  incomplete; the contractor must review before the A/E does.
- Coordination: drawing dimensions/clearances reconcile with related submittals and
  the contract drawings. Hand drawing-coordination questions to
  **engineering-design-review** and pull its findings back in.

## Status determination (the stamp action)

Make the call. Choose exactly one, with reasons:

- **No Exceptions Taken** — compliant and complete; no corrections.
- **Approved as Noted** — minor deviations the contractor can correct without
  resubmitting; list each noted correction with its citation.
- **Revise and Resubmit** — material deviations, missing required data, or an
  unevaluable substitution; the package must come back. List every required
  correction.
- **Rejected** — does not meet the spec / wrong product / improper substitution;
  state why and what is required instead.

Tie the action to the compliance matrix: any open `deviation`/`missing` that the
contractor cannot fix by note pushes the action to Revise/Reject.

## Output

Hand the synthesis step a structured, cited result:

- **Marked-up review summary** — the per-attribute compliance matrix
  (compliant / deviation / missing) with both-side citations.
- **Recommended stamp action** — one disposition with rationale.
- **Resubmittal instructions** — itemized required corrections, each tied to a
  spec citation, plus the substitution-evaluation checklist when applicable.
- **Open items** — `needs-info` rows and unresolved coordination questions.

Cross-references: **rfp-analysis** (required_submittals + CSI mapping),
**engineering-design-review** (drawing coordination). Preserve provenance end to
end so the presentation step can deep-link every finding.

## Anti-Patterns

- Approving a submittal without pulling and quoting the actual spec section.
- Missing a deviation buried in a cut-sheet image or footnote because only the
  body markdown was read.
- Treating a substitution request as an approved equal (or vice versa).
- Asking Mistral to "tell me if this complies" or to pick a stamp action.
- Re-OCRing a package that already has an extraction envelope.
- Trusting a low-confidence model_no, standard, or rating instead of flagging it.
- Defaulting everything to "Revise and Resubmit" to avoid making the call.
- Ignoring a missing/unsigned contractor stamp.
- Emitting a deviation or stamp action with no page/figure citation.
- Mutating extracted ratings or dimensions to "clean them up" before comparison.

## Checklist

- [ ] Consumed the `mistral-ocr4` envelope; did not re-OCR.
- [ ] Submittal annotation schema requested upstream; markdown/blocks/images used for gaps.
- [ ] Reviews fanned out across submittals and pages in parallel.
- [ ] Governing CSI spec section loaded and quoted verbatim (or marked needs-info).
- [ ] Compliance matrix built: every spec attribute compared, cited on both sides.
- [ ] Referenced standards verified, including edition.
- [ ] Substitution vs. approved-equal correctly classified; requirements stated.
- [ ] Completeness checked: ratings, certifications, sample sizes, contractor stamp.
- [ ] Drawing coordination reconciled with engineering-design-review.
- [ ] Low-confidence regions on ratings/model numbers flagged for human verification.
- [ ] Stamp action chosen (NET / Approved as Noted / Revise & Resubmit / Rejected) with reasons.
- [ ] Resubmittal instructions itemized and tied to citations.
- [ ] Provenance (source_doc_id, page, bbox/figure, model) preserved end to end.
- [ ] Cross-refs honored: rfp-analysis (required submittals), engineering-design-review.
