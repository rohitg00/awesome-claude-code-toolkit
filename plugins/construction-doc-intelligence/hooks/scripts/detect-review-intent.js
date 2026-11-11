#!/usr/bin/env node
/**
 * detect-review-intent.js  (UserPromptSubmit, plugin-scoped)
 *
 * Divines, from ordinary conversational wording, when the user wants a construction
 * document *reviewed / evaluated / leveled / reconciled* (not merely OCR'd) and
 * nudges toward the construction-doc-intelligence pipeline. It never blocks or
 * rewrites the prompt; on a match it injects a short context hint, otherwise it
 * stays silent.
 *
 * Division of labor: pure "read/parse this PDF" intent is handled by the
 * mistral-ocr4 plugin's hook (extraction). This hook fires for the *reasoning*
 * layer — review, comparison, judgment.
 */

const stdinData = [];
process.stdin.on("data", (chunk) => stdinData.push(chunk));
process.stdin.on("end", () => {
  const input = Buffer.concat(stdinData).toString().trim();
  let prompt = "";
  try {
    const parsed = JSON.parse(input);
    prompt = parsed.prompt || parsed.message || parsed.user_prompt || input;
  } catch (e) {
    prompt = input;
  }

  const hint = analyze(prompt);
  if (hint) {
    console.log(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "UserPromptSubmit",
          additionalContext: hint,
        },
      })
    );
  }
});

if (process.stdin.isTTY) {
  process.exit(0);
}

function analyze(promptRaw) {
  const text = String(promptRaw || "").toLowerCase();
  if (!text) return null;

  // Reasoning/review verbs — the pipeline's job, beyond mere extraction.
  const reviewVerbs =
    /\b(review|evaluate|assess|analyz|compare|level|reconcile|vet|audit|score|rank|qualify|red[- ]?line|check (?:for )?compliance|go[\/ ]?no[- ]?go|recommend|which (?:bid|vendor|quote))\b/;
  // Construction document nouns.
  const docNouns =
    /\b(rfp|rfq|rfi|solicitation|addend|bid|quote|proposal|invoice|pay ?app|pay application|application for payment|schedule of values|submittal|cut ?sheet|shop drawing|product data|spec(?:ification)?s?|drawing|plan ?set|blueprint|change order|takeoff|estimate|vendor|subcontractor|contract)\b/;

  const hasReview = reviewVerbs.test(text);
  const hasDoc = docNouns.test(text);

  if (!(hasReview && hasDoc)) return null;

  const route = classifyRoute(text);

  return (
    "[construction-doc-intelligence] This looks like a construction document REVIEW " +
    "(reasoning), not just extraction. Run the pipeline: triage → extract via the " +
    "mistral-ocr4 MCP (parallel, with a doc-type annotation schema) → route to the " +
    `domain skill (${route}) → apply lean-pm-judgment (rank by risk, quote binding ` +
    "language verbatim, recompute critical numbers, make the call with confidence) → " +
    "present with citations → feed agentic-self-improvement. Mistral extracts; you reason."
  );
}

function classifyRoute(text) {
  const map = [
    [/\b(rfp|rfq|rfi|solicitation|addend|bid (?:package|set)|proposal)\b/, "rfp-analysis"],
    [/\b(level|compare|which (?:bid|vendor|quote)|vendor|subcontractor|quote)\b/, "vendor-bid-leveling"],
    [/\b(invoice|pay ?app|pay application|application for payment|schedule of values|reconcile|change order)\b/, "invoice-reconciliation"],
    [/\b(submittal|cut ?sheet|shop drawing|product data)\b/, "submittal-review"],
    [/\b(drawing|plan ?set|blueprint|spec(?:ification)?s?|detail|coordination|clash)\b/, "engineering-design-review"],
  ];
  for (const [re, route] of map) if (re.test(text)) return route;
  return "the matching domain skill";
}
