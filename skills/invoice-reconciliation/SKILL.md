---
name: invoice-reconciliation
description: Reconcile construction invoices and AIA-style pay applications against the Schedule of Values, PO/change orders, and prior pay apps - consuming a Mistral OCR4 extraction envelope, re-checking all math deterministically, and recommending pay/hold/partial-pay with cited disputed lines
---

# Invoice Reconciliation

Reconcile a vendor/sub invoice or AIA-style progress-billing pay application
(G702/G703 continuation sheet) against the contract basis, then recommend
**pay / hold / partial-pay** with the exact disputed lines and dollars cited.

**The one rule that shapes everything:**
> **Mistral OCR4 extracts. Claude reasons.**
> The `mistral-ocr4` skill produces a stable extraction envelope (raw Mistral
> JSON). This skill **consumes** it and **reasons** over it. Never re-OCR a page
> you already have. Never ask Mistral to evaluate, compare, or do the math —
> the PM/Claude does the reconciliation; arithmetic is computed deterministically
> (a calculator/code cell), never eyeballed.

Apply the `lean-pm-judgment` lens: think like a senior construction PM at an
owner's-rep / SME agency — risk-first, lean, decisive. A dollar billed ahead of
work in place is the owner's risk. Part of `construction-doc-pipeline`; hand the
structured result to the presentation step.

## Inputs (from the extraction envelope)

Consume, don't re-fetch. From `mistral-ocr4`'s `ocr_process` output:
- `pages[].markdown` — reading-order text (totals blocks, notes, signatures).
- `pages[].blocks[]` — each with `bbox` + `label`; `label: table` blocks are the
  G703 continuation sheet / line-item grids. Keep `bbox` + page index as the
  **provenance citation** for every value you flag.
- `document_annotation` / per-block annotations — structured fields, when the
  upstream call supplied a `*_annotation_format` schema (preferred over regex).
- `confidence` — per page/word. Low-confidence numeric cells get re-read or
  questioned, never silently trusted.

Preserve provenance end to end: every flag cites `page N, line/row M`.

## Suggested annotation schema (request upstream)

Ask `mistral-ocr4` to capture these **verbatim** (capture what, never judge):
```
vendor, invoice_no, invoice_date, po_number, contract_ref,
line_items[{ description, scheduled_value, qty, unit, unit_price, amount,
             percent_complete, work_completed_to_date }],
previous_billings, this_period, materials_stored,
subtotal, retainage_percent, retainage_amount, tax,
change_orders[{ co_number, description, amount, approved }],
total_due, lien_waiver_status
```

## Reconciliation workflow

1. **Identify the contract basis.** Pull the Schedule of Values (SOV), executed
   PO, and approved change orders. Cross-reference `vendor-bid-leveling` /
   `rfp-analysis` outputs — the awarded bid + contract is the SOV's source of
   truth. No basis = automatic hold.
2. **Math integrity (deterministic, every line).** Recompute, don't read:
   - extension: `qty x unit_price == amount`
   - completed-to-date: `previous_billings + this_period (+ materials_stored) == work_completed_to_date`
   - `% complete == work_completed_to_date / scheduled_value`
   - column sums == printed subtotal; `subtotal + tax - retainage == total_due`
   - retainage: `retainage_amount == retainage_percent x work_completed_to_date`
   Flag **every** discrepancy with its page/line citation and the delta in dollars.
3. **Multi-way match.** For each line, compare invoice vs:
   - **SOV** — line exists, scheduled value matches, not over-billed past SOV.
   - **PO + approved COs** — quantities/prices within contract; scope is in contract.
   - **Prior pay apps (continuation sheet)** — `previous_billings` ties to the
     last approved app's completed-to-date; no duplicate billing of the same work.
   Flag: over-billing, billing ahead of % complete in place, duplicate billing,
   scope-not-in-contract lines, unit-price drift from the contract.
4. **Retainage & lien waiver.** Confirm the correct retainage % was withheld;
   confirm a lien waiver is present and its amount/period matches this payment
   (conditional for the current draw, unconditional for prior paid amounts).
   Stored materials require supporting docs (invoices/photos/bill-of-sale) and
   off-site stored materials need a bonded/insured arrangement.
5. **Change orders.** Only **approved** COs may be billed; reject billing against
   pending/verbal COs. Re-check CO math and that CO totals roll into the revised
   contract sum used for % complete.
6. **Decide.** Issue pay / hold / partial-pay with the exact disputed lines and
   dollar amounts, the recommended approved amount, and questions for the vendor.

## Parallel processing (default to it)

Fan out — reconciliation across invoices is independent work:
- Many invoices / draws → reconcile each concurrently in one batch of calls.
- One large continuation sheet → process page ranges concurrently, stitch by
  page index, then run the cross-page sums once at the end.
- Keep each unit independent; don't thread state between them.

## Output to the presentation step

Structured, not prose:
- recommendation: `pay | hold | partial-pay`, with approved amount.
- disputed_lines[]: `{ page, line, issue, billed, recommended, delta, citation }`.
- math_exceptions[]: every failed recompute with the delta.
- retainage/lien-waiver/CO status flags.
- vendor_questions[]: specific, answerable items blocking payment.
- low_confidence_cells[]: values needing re-read before reliance.

## Anti-patterns

- Trusting OCR'd numbers without an independent arithmetic re-check.
- Ignoring `confidence` — paying off a low-confidence misread digit.
- Approving amounts that bill ahead of actual % complete / work in place.
- Missing duplicate lines or work already billed on a prior pay app.
- Paying out-of-scope or not-in-contract lines because they "look reasonable."
- Billing against pending/verbal change orders.
- Letting Mistral compute or judge totals, compliance, or over-billing.
- Re-OCRing pages already in the envelope, or mutating extracted values to "fix" them.
- Releasing payment without a matching lien waiver / stored-materials backup.

## Checklist

- [ ] Reconciling from the extraction envelope; no re-OCR, values unmutated.
- [ ] Contract basis (SOV / PO / approved COs) located; cross-ref bid-leveling/RFP.
- [ ] Every extension, sum, %-complete, completed-to-date, retainage, and total recomputed deterministically.
- [ ] Multi-way match run: invoice vs SOV vs PO/CO vs prior pay apps.
- [ ] Over-billing, ahead-of-%-complete, duplicate, and out-of-scope lines flagged with citations.
- [ ] Retainage % verified; lien waiver present and amount/period matched.
- [ ] Stored materials documented; off-site materials properly secured.
- [ ] Only approved change orders billed; CO math checked.
- [ ] Low-confidence numeric cells re-read or queried.
- [ ] pay/hold/partial-pay recommendation with disputed lines, dollar deltas, and vendor questions.
- [ ] Structured result + provenance handed to the presentation step.
