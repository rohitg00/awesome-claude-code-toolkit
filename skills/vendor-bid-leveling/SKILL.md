---
name: vendor-bid-leveling
description: Apples-to-apples leveling of competing subcontractor/vendor bids - normalizes scope, builds a leveling matrix, detects scope gaps and buried exclusions, validates the low bid, and produces a defensible award recommendation; consumes the Mistral OCR4 extraction envelope and does the reasoning
---

# Vendor Bid Leveling

Reasoning node in the `construction-doc-pipeline`. It takes the **extraction
envelope** produced by `mistral-ocr4` for each bid/quote/proposal and turns a
stack of incomparable numbers into one **leveled matrix** plus a decisive award
recommendation, through the `lean-pm-judgment` lens (senior construction PM / SME
agency mindset: risk-first, lean, defensible, decisive).

**The one rule that shapes everything (inherited from the extraction layer):**
> **Mistral extracts. This skill reasons.**
> Never re-OCR a document and never ask Mistral to compare, score, or pick a
> winner. Consume the raw envelope, preserve its provenance, and do every
> judgment here.

## Inputs — what you read from the envelope

For each bid, read the envelope `mistral-ocr4` already produced; do not re-run OCR.

- `pages[].markdown` — reading-order text; cover letters, exclusions, qualifications.
- `pages[].blocks[]` — paragraph blocks with `bbox` + structural `label`; the
  `table` label marks bid schedules / unit-price tables — use it to find the grid.
- `pages[].images[]` — logos, stamps, signed/sealed proposal pages.
- `document_annotation` / per-block annotations — structured fields, present only
  when a `*_annotation_format` schema was requested upstream from `ocr_process`.
- `confidence` — per-page/word; gate any number you lift from a table on it.

Preserve provenance for every value you carry into the matrix: `{bid, page,
block bbox, confidence}`. The matrix cell points back to where the number came from.

## Suggested annotation schema (bid / quote)

If no `document_annotation` was requested upstream, ask the extraction step to
capture this verbatim (capture *what*, never judge):

```
vendor, bid_date, validity_period, base_bid,
alternates[]:        {id, description, add_deduct, amount}
unit_prices[]:       {description, unit, unit_price}
line_items[]:        {csi_division, description, qty, unit, unit_price, amount}
exclusions[], inclusions[], qualifications[], clarifications[]
allowances[]:        {description, amount}
lead_time, payment_terms, retention,
bond:                {provided, type, cost}
insurance:           {provided, limits, cost}
taxes_freight:       {included, amount}
```

Numbers are captured as written. "Is the base bid actually complete" is decided here.

## Building the leveling matrix

1. Anchor to the **bid scope of work** — pull it from `rfp-analysis` (the RFP/ITB
   scope is the master line-item basis). The matrix rows ARE that scope.
2. Normalize every bid to that common basis: map each bidder's line items onto the
   master rows, aligned by **CSI division / scope item**, not by the bidder's own
   ordering or wording.
3. One column per bidder; one row per master scope item, plus rows for base bid,
   each alternate, allowances, bonds/insurance, taxes/freight, and adjustments.
4. Put excluded/missing scope in the cell as an explicit zero-with-flag, never a
   blank — a blank reads as "free," which is the classic leveling error.
5. Carry a confidence/provenance footnote on every lifted number.

## Detecting scope gaps and overlaps

- **Gaps** — master scope item present, but missing or excluded in a bid. Each gap
  is unpriced scope the owner will pay for later. List per bidder.
- **Risk-shifting exclusions/qualifications** — "by others," "owner to provide,"
  "excludes rock/dewatering/permits," "price held 15 days." These move cost and
  schedule risk to the owner; surface every one, don't bury them in a footnote.
- **Allowance vs firm pricing** — an allowance is a placeholder, not a price.
  Flag allowance-heavy bids; they understate true cost.
- **Unit-price vs lump-sum mismatch** — some bid a unit price, some a lump sum for
  the same scope. Normalize to the RFP's quantities before comparing.
- **Overlaps** — scope double-counted across two trades/packages; net it out so
  the owner isn't paying twice.

## Apples-to-apples adjustments

Produce an **adjusted bid** per bidder = base bid, then:

- **Add back** excluded in-scope work at a fair value (your estimate or another
  bidder's price for the same item) so all bids cover identical scope.
- **Normalize alternates** — compare only the alternates actually being awarded;
  apply the same set to every bid.
- **Account for** taxes, freight, bond, and insurance: add them where excluded so
  every adjusted number is on the same all-in basis.
- **Flag unbalanced bids** — front-loaded line items or unit prices wildly off the
  others distort early payments and change-order exposure even if the total looks fine.

State each adjustment as a line with its basis. The adjusted total, not the
as-submitted total, is what you rank.

## Low-bid validation

The low number only wins if it is **complete and correct**:

- **Completeness** — does the low bid carry every master scope row? An apparent
  low is often low because it dropped scope.
- **Math checks** — recompute `qty x unit_price = amount` for each line and sum to
  the base bid. OCR'd table numbers are suspect; re-derive, don't trust.
- **Spread analysis** — lay out all base bids and all adjusted bids. A bidder far
  below the pack is usually an error or a missed scope, not a deal; a bidder far
  above may have read scope no one else did. Investigate both tails.
- **Outlier line items** — within a CSI division, a unit price that is a fraction
  or multiple of the field signals a transcription error or a misunderstanding.

## Recommended award rationale

Deliver a decisive recommendation (lean-PM voice), not a data dump:

- Recommended awardee + adjusted total, and *why* (lowest responsible complete bid,
  acceptable risk profile, schedule fit).
- Risk notes: open exclusions, allowance exposure, lead-time/bond/insurance gaps.
- Ranked runners-up with the delta and the trade-off.
- **Clarification RFIs per bidder** — the exact questions to close each scope gap,
  qualification, or suspect number before award (e.g. "confirm dewatering included
  in base bid," "break out the $X site-work allowance," "verify Div 26 unit price").

## Cross-references

- `rfp-analysis` — upstream; supplies the scope of work being bid (the master rows).
- `invoice-reconciliation` — downstream; once awarded, the leveled line items and
  unit prices become the baseline invoices are checked against.
- `mistral-ocr4` — the extraction layer that feeds this skill.

## Parallel processing

Bid leveling is fan-out by nature:

- Issue extraction + field normalization for all N bids **concurrently** (one batch
  of calls), since each bid's envelope is independent — don't level one at a time.
- Normalize each bid onto the master scope in parallel, then **merge** the
  normalized records into the single matrix as a final reduce step.
- Keep per-bid work independent; the only shared state is the master scope and the
  final matrix.

## Anti-patterns

- Comparing raw bottom-line numbers without leveling — the cheapest as-submitted
  bid is routinely the most expensive once excluded scope is added back.
- Missing buried exclusions/qualifications in the cover letter or fine print.
- Trusting OCR'd table numbers without a confidence/echo check or `qty x price` re-derivation.
- Leaving missing scope as a blank cell (reads as free) instead of a flagged zero.
- Treating an allowance as firm pricing.
- Comparing a different alternate set across bidders.
- Re-OCR'ing a document this pipeline already extracted.
- Asking Mistral to "pick the best bid" — extraction never reasons; this skill decides.

## Checklist

- [ ] Consumed each bid's existing envelope; no re-OCR.
- [ ] Master scope pulled from `rfp-analysis`; matrix rows anchored to it.
- [ ] Every bid normalized by CSI division / scope item, not bidder ordering.
- [ ] Scope gaps, overlaps, and risk-shifting exclusions listed per bidder.
- [ ] Allowances, unit-price vs lump-sum, taxes/freight/bond/insurance normalized.
- [ ] Adjusted (add-back) total computed per bidder; ranking uses adjusted, not as-submitted.
- [ ] Low bid validated: completeness, `qty x unit_price` math, spread/outlier analysis.
- [ ] Provenance + confidence carried on every lifted number.
- [ ] Decisive award recommendation with risk notes and per-bidder clarification RFIs.
- [ ] Structured result handed to the presentation step.
