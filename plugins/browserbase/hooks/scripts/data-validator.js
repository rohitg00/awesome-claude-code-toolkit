#!/usr/bin/env node
/**
 * data-validator.js  (UserPromptSubmit hook)
 *
 * Detects extraction/scraping prompts and injects instructions to validate
 * extracted data against Zod schemas. On validation failure, re-runs
 * extraction once with a refined prompt before returning partial results.
 */

const { run } = require("./lib/prompt-hook");
run(analyze);

function analyze(promptRaw) {
  const text = String(promptRaw || "").toLowerCase();
  if (!text) return null;

  const isExtraction =
    /\b(extract|scrape|pull|grab|get)\b/.test(text) &&
    /\b(data|info|details|price|name|title|field|table|list|product|review|contact)\b/.test(text);

  const hasSchema = /\b(schema|zod|z\.|structured|typed|validate)\b/.test(text);
  const hasUrl = /\bhttps?:\/\/\S+/.test(text);

  if (!isExtraction && !hasSchema) return null;
  if (!hasUrl && !isExtraction) return null;

  return (
    "[browserbase:data-validator] Structured data validation is active. " +
    "After every Stagehand extract() call, validate the result:\n\n" +
    "1. Define the expected schema with Zod BEFORE extraction\n" +
    "2. After extract(), run schema.safeParse(result)\n" +
    "3. If validation fails:\n" +
    "   a. Log which fields failed: missing, wrong type, or empty\n" +
    "   b. Re-run extract() ONCE with a refined instruction that specifically targets the missing fields\n" +
    "   c. Merge the retry result with the original (retry wins on conflicts)\n" +
    "   d. Validate again — if still failing, return what we have with warnings\n" +
    "4. Report to the user: total fields expected, fields populated, fields empty/missing\n\n" +
    "```js\n" +
    "const result = await stagehand.extract({ instruction, schema });\n" +
    "const parsed = schema.safeParse(result);\n" +
    "if (!parsed.success) {\n" +
    "  const missing = parsed.error.issues.map(i => i.path.join('.'));\n" +
    "  console.warn(`Validation failed for: ${missing.join(', ')}`);\n" +
    "  const retry = await stagehand.extract({\n" +
    "    instruction: `Focus on extracting these specific fields: ${missing.join(', ')}`,\n" +
    "    schema,\n" +
    "  });\n" +
    "  Object.assign(result, retry);\n" +
    "}\n" +
    "```\n" +
    "Always show the user a validation summary after extraction."
  );
}
