---
name: engineering-design-review
description: Reason over OCR-extracted construction drawing sets, specs, and design calculations for coordination, constructability, completeness, and code references - consuming a Mistral OCR4 extraction envelope and producing a cited coordination/RFI log, never re-OCRing or asking Mistral to judge
---

# Engineering & Design Document Review

A reasoning node in the `construction-doc-pipeline`. It **consumes** the
extraction envelope produced by `mistral-ocr4` and applies senior-PM judgment to
drawing sets, specifications, and design calculations — then hands a structured
result to the presentation step.

**The one rule that shapes everything:**
> **Mistral OCR4 extracts. Claude reasons.**
> The envelope is the stable contract. This skill never re-OCRs a page and never
> asks Mistral to evaluate, compare, or flag anything. Coordination, clash
> candidates, completeness, constructability, RFIs — all of that is Claude's job.

## The judgment lens

Apply `lean-pm-judgment`: think like a senior construction PM / engineering SME
in an owner's-rep agency. Lean, constructability-first, decisive. Surface what
actually stops the field from building, drives a change order, or generates an
RFI. Cut noise. Cite everything by sheet number and page index so a coordinator
can verify against the source sheet in seconds.

## What you receive (the extraction envelope)

Raw Mistral JSON from `ocr_process`. Treat it as read-only:

- `pages[].markdown` — reading-order text (general notes, schedule rows, spec body).
- `pages[].blocks[]` — `bbox` + structural `label` (title, table, figure, header,
  footer, …). Use labels to locate title blocks, schedules, and detail callouts.
- `pages[].images[]` — drawing sheets and details (plans, sections, details).
- `document_annotation` / per-block annotations — structured fields when an
  upstream `*_annotation_format` schema was supplied on `ocr_process`.
- `confidence` — per page/word when granularity was set.

**Provenance is sacred.** Preserve sheet_no / page index on every finding. OCR of
drawings is imperfect: treat extracted geometry, dimensions, and figures as
*references to the source sheet*, not ground truth. Flag low-confidence regions
explicitly rather than asserting through them.

## Suggested annotation schema (drawings & specs)

Ask the upstream OCR step to capture these verbatim (define *what* to capture,
never *how to judge it*):

```
title_block { sheet_no, sheet_title, discipline, rev, date, scale, project }
general_notes[]
keynotes[]                      # keyed notes referenced on the sheet
referenced_codes[]              # IBC, ASCE 7, ACI 318, AISC 360, NEC, etc.
detail_references[]             # e.g. "3/A-501", "SIM 5/S-301"
schedules[]                     # door / window / equipment / finish (rows as records)
revision_clouds[]               # cloud + delta tag + description if legible
spec_sections[]                 # CSI section no + title (e.g. 08 11 13)
```

If the envelope lacks these, reason from `markdown` + `blocks` and note the gap.

## Drawing-set inventory & completeness

- [ ] Build the sheet index from the cover/index sheet; list every sheet actually present.
- [ ] Reconcile index vs. present sheets by `sheet_no`; report missing and orphan sheets.
- [ ] Confirm current revision per sheet; flag sheets behind the latest rev or undated.
- [ ] Check discipline coverage (A / S / M / E / P / FP / Civil / Landscape) against project scope; flag missing disciplines.
- [ ] Note half-size/illegible scans and low-`confidence` sheets as completeness risks.

## Cross-discipline coordination (clash candidates)

Reconcile findings **by sheet number** across disciplines and surface conflicts as
**candidate clashes / potential RFIs** — never as confirmed clashes:

- Structural beam depth vs. mechanical duct routing vs. required ceiling height.
- Penetrations through beams/walls/slabs not shown on structural sheets.
- Equipment footprints vs. clearances (code, service, door swing) and access.
- Architectural vs. structural grid/dimension disagreements.
- MEP equipment served by capacities not reflected on the electrical/plumbing sheets.

Each candidate must cite the sheets involved and state that it requires source
verification before it becomes a real clash.

## Spec ↔ drawing consistency

- [ ] Cross-check schedules (door/window/equipment/finish) against the matching spec sections.
- [ ] Compare general notes / keynotes against spec requirements for conflicts.
- [ ] Flag products, ratings, or finishes named on drawings but absent from specs (and vice-versa).
- [ ] Note "or equal" / "by others" / "see spec" references that dead-end.

## Code & standard references

- [ ] Capture every cited code/standard (IBC, ASCE 7, ACI 318, AISC 360, NEC, NFPA, local amendments) with the sheet it appears on.
- [ ] Flag obviously missing or stale references (e.g. superseded edition years) for the engineer of record.
- [ ] **Do not adjudicate code compliance.** Flag for the EOR/AHJ; never assert pass/fail.

## Constructability & RFI generation

Turn ambiguity into drafted RFIs with citations:

- Missing or conflicting dimensions; details that don't close; "TYP" with no basis detail.
- Detail callouts pointing to a detail that isn't on the referenced sheet.
- Sequencing / means-and-methods issues (e.g. embeds shown after pour).
- Conflicts already found in coordination/spec checks that need an answer to build.

Drafted RFI format: question, sheet(s)/detail cited, discipline, assumption if
unanswered, suggested resolution. Keep each RFI buildable-specific, not academic.

## Output

Two deliverables, both cited by sheet number / page index, handed to the
presentation step:

1. **Coordination / RFI log** — rows of `{ issue, sheets_involved, discipline,
   severity, type (clash-candidate | spec-conflict | code-flag | constructability
   | RFI), suggested_resolution, source_verification_needed }`.
2. **Completeness summary** — sheet index reconciliation, current revisions,
   missing disciplines, low-confidence/illegible sheets.

Order by severity. Mark every geometry- or dimension-derived item as
"verify against source sheet."

## Parallel processing

Fan out OCR + review across sheets and disciplines concurrently (the OCR layer is
embarrassingly parallel), then **reconcile by sheet number**. Keep per-sheet
review independent; merge into one log at the end so cross-discipline conflicts
line up on shared `sheet_no` / grid references.

## Cross-references

- `submittal-review` — drawing coordination against approved submittals.
- `rfp-analysis` — scope basis the design set is measured against.
- `mistral-ocr4` — the extraction layer this skill consumes (never bypass it to re-OCR).

## Anti-Patterns

- Trusting OCR'd dimensions, scales, or geometry as exact instead of as references to verify.
- Asserting a clash as confirmed without flagging that the source sheet must be checked.
- Adjudicating code compliance instead of flagging it for the engineer of record.
- Letting Mistral interpret, summarize, or "check" the drawings — extraction only.
- Re-OCRing pages this skill already received in the envelope.
- Ignoring revision clouds / delta tags and reviewing superseded sheets as current.
- Dropping `sheet_no` / page provenance from findings, making them unverifiable.
- Reviewing disciplines in isolation and never reconciling by sheet number.

## Checklist

- [ ] Worked only from the OCR envelope; never re-OCRed or asked Mistral to judge.
- [ ] Sheet index reconciled vs. sheets present; missing disciplines/sheets reported.
- [ ] Current revision confirmed per sheet; revision clouds honored.
- [ ] Cross-discipline conflicts surfaced as clash candidates needing source verification.
- [ ] Schedules/notes cross-checked against spec sections.
- [ ] Cited codes captured; missing/stale ones flagged for the EOR (not adjudicated).
- [ ] Constructability gaps converted to drafted RFIs with sheet/detail citations.
- [ ] Coordination/RFI log + completeness summary produced, every item cited by sheet/page.
- [ ] Geometry/dimension findings marked "verify against source sheet."
- [ ] Reviewed sheets in parallel and reconciled by sheet number.
