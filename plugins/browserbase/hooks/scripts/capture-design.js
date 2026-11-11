#!/usr/bin/env node
/**
 * capture-design.js  (UserPromptSubmit hook)
 *
 * Detects intent to capture a website's design, take design-oriented
 * screenshots, or reverse-engineer a visual design language — then routes
 * to the capture-design command with extraction instructions.
 */

const { run } = require("./lib/prompt-hook");
run(analyze);

function analyze(promptRaw) {
  const text = String(promptRaw || "").toLowerCase();
  if (!text) return null;

  const designCapture =
    /\b(capture|copy|clone|replicate|reverse.?engineer|extract|analyze|document)\b/.test(text) &&
    /\b(design|style|theme|look|aesthetic|ui|visual|layout|css|branding)\b/.test(text) &&
    (/\bhttps?:\/\/\S+/.test(text) || /\b(site|website|page|landing|homepage)\b/.test(text));

  const screenshotDesign =
    /\b(screenshot|screen.?shot|snap|capture)\b/.test(text) &&
    /\b(design|site|page|website|landing|homepage)\b/.test(text);

  const designLanguage =
    /\b(design\s*(language|system|tokens|spec)|style\s*guide|brand\s*guide|visual\s*identity)\b/.test(text);

  const designMd =
    /\bdesign\.md\b/.test(text);

  const makeItLookLike =
    /\b(make|build|create|design)\b.*\b(like|similar|inspired|based on|matching)\b/.test(text) &&
    /\bhttps?:\/\/\S+/.test(text);

  if (!designCapture && !screenshotDesign && !designLanguage && !designMd && !makeItLookLike)
    return null;

  const hasUrl = /\bhttps?:\/\/\S+/.test(text);
  const hasSearchQuery =
    /\b(search|find|google|look up|best|top)\b/.test(text) &&
    /\b(site|website|page|design|landing|example)\b/.test(text);

  let resolution = "";
  if (hasUrl) {
    resolution =
      "Target URL detected in the prompt — navigate directly to it.";
  } else if (hasSearchQuery) {
    resolution =
      "No URL given but a search query is implied — use Stagehand to Google the query, " +
      "extract the top organic result URL, and confirm with the user before proceeding.";
  } else {
    resolution =
      "No URL or search query detected — ask the user for a target website URL or search term.";
  }

  return (
    "[browserbase:capture-design] Design capture intent detected. " +
    "Use /browserbase:capture-design to screenshot the target site and generate a design.md scaffold.\n\n" +
    resolution + "\n\n" +
    "Workflow:\n" +
    "1. Resolve target (URL or Google search → top result)\n" +
    "2. Open in Browserbase cloud browser (env: 'BROWSERBASE')\n" +
    "3. Capture screenshots: desktop full-page (1440×900), above-fold, mobile (390×844), key sections\n" +
    "4. Extract design tokens from live DOM via page.evaluate() + getComputedStyle():\n" +
    "   - Colors: backgrounds, text, borders, accents (computed hex values)\n" +
    "   - Typography: font-family, sizes, weights, line-heights (from actual elements)\n" +
    "   - Spacing: padding, margins, gaps (from section/component elements)\n" +
    "   - Layout: max-width, grid columns, breakpoints\n" +
    "   - Components: buttons, cards, nav, forms (border-radius, shadows, padding)\n" +
    "   - Effects: box-shadows, transitions, gradients, backdrop-filters\n" +
    "5. Generate design.md with CSS custom properties, component classes, and section map\n" +
    "6. Save screenshots to .browserbase/design-captures/<domain>-<timestamp>/\n" +
    "7. Report file paths and design summary to user\n\n" +
    "The design.md must be modular and reusable — every value extracted from real CSS, never guessed."
  );
}
