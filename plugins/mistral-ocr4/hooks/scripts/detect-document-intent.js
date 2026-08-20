#!/usr/bin/env node
/**
 * detect-document-intent.js  (UserPromptSubmit, plugin-scoped)
 *
 * Divines, from ordinary conversational wording, when the user wants a document
 * turned into data - then nudges toward the Mistral OCR4 extraction handoff.
 * It NEVER blocks or rewrites the prompt; on a match it injects a short context
 * hint, otherwise it stays silent.
 *
 * Reasoning stays with the model: this only routes toward EXTRACTION.
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
    // Modern Claude Code contract: stdout under hookSpecificOutput.additionalContext
    // is appended to the model's context for this turn.
    console.log(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "UserPromptSubmit",
          additionalContext: hint,
        },
      })
    );
  }
  // Silence on no match keeps the hook non-intrusive.
});

if (process.stdin.isTTY) {
  // No stdin (manual invocation): emit nothing.
  process.exit(0);
}

function analyze(promptRaw) {
  const text = String(promptRaw || "").toLowerCase();
  if (!text) return null;

  // Verbs that imply "turn this document into data".
  const extractVerbs =
    /\b(ocr|read|parse|pull|grab|extract|scrape|digit(?:ize|ise)|transcribe|get(?: me)?|capture|lift)\b/;
  // Things that are documents.
  const docNouns =
    /\b(pdf|scan(?:ned)?|drawing|blueprint|spec(?:ification)?s?|submittal|rfp|rfq|rfi|solicitation|addendum|addenda|bid|quote|proposal|invoice|estimate|takeoff|schedule|plan ?set|cut ?sheet|datasheet|data ?sheet|contract|purchase ?order|p\.?o\.?|line ?items?|door schedule|equipment list|title ?block)\b/;
  // File-ish references.
  const fileRef =
    /\.(pdf|png|jpe?g|tiff?|webp|avif|docx?|pptx?)\b|https?:\/\/\S+\.(pdf|png|jpe?g|tiff?|webp|avif)/;
  // "what does this <doc> say" style questions about a document's contents.
  const contentsQ =
    /\bwhat(?:'s| is| does)\b[^?]*\b(say|in|contain|inside|this (?:doc|file|pdf|page|sheet|drawing|spec))/;

  const hasVerb = extractVerbs.test(text);
  const hasDoc = docNouns.test(text);
  const hasFile = fileRef.test(text);
  const hasContentsQ = contentsQ.test(text);

  // Fire when intent is reasonably clear, not on every mention of a noun.
  const matched =
    (hasVerb && (hasDoc || hasFile)) ||
    (hasContentsQ && (hasDoc || hasFile)) ||
    (hasFile && hasDoc);

  if (!matched) return null;

  const docType = classifyDocType(text);
  const typeNote = docType
    ? ` This reads like a ${docType} document - capture fields verbatim (no judgment).`
    : "";

  return (
    "[mistral-ocr4] This prompt looks like a document-to-data extraction task. " +
    "Use the mistral-ocr4 skill / MCP for OCR: pick the input mode (document_url " +
    "vs files_upload->file_id vs base64), run pages/documents in parallel, set " +
    "include_blocks or a *_annotation_format schema when structure/fields are " +
    "needed, and hand off the raw extraction envelope. Mistral extracts; you do " +
    "all reasoning." +
    typeNote
  );
}

function classifyDocType(text) {
  const map = [
    [/\b(rfp|rfq|rfi|solicitation|addend|bid (?:package|set)|proposal)\b/, "RFP/solicitation"],
    [/\b(invoice|estimate|quote|purchase ?order|p\.?o\.?|line ?items?|takeoff)\b/, "invoice/vendor pricing"],
    [/\b(submittal|cut ?sheet|datasheet|data ?sheet|product data)\b/, "submittal"],
    [/\b(drawing|blueprint|plan ?set|title ?block|detail|section view|elevation)\b/, "engineering/design drawing"],
    [/\b(spec(?:ification)?s?|division \d|csi)\b/, "specification"],
    [/\b(door schedule|equipment list|finish schedule|schedule)\b/, "schedule/table"],
    [/\b(vendor|subcontractor|supplier)\b/, "vendor"],
  ];
  for (const [re, label] of map) if (re.test(text)) return label;
  return null;
}
