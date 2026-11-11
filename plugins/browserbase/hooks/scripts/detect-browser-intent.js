#!/usr/bin/env node
/**
 * detect-browser-intent.js  (UserPromptSubmit, plugin-scoped)
 *
 * Detects when the user wants to scrape, automate, or browse the web — then
 * nudges toward the Browserbase plugin capabilities. Never blocks or rewrites
 * the prompt; on a match it injects a short context hint, otherwise stays silent.
 */

const { run } = require("./lib/prompt-hook");
run(analyze);

function analyze(promptRaw) {
  const text = String(promptRaw || "").toLowerCase();
  if (!text) return null;

  const scrapeVerbs =
    /\b(scrape|crawl|extract|pull|grab|harvest|monitor|watch|check|fetch|get)\b/;
  const browseVerbs =
    /\b(browse|navigate|click|fill|submit|login|sign.?in|automate|open|visit|go to)\b/;
  const agentVerbs =
    /\b(search the web|find online|look up|web search|browse for|google|research online)\b/;
  const webNouns =
    /\b(web ?page|web ?site|url|page|site|form|button|link|browser|html|dom|selector)\b/;
  const targetRefs =
    /\bhttps?:\/\/\S+|\b(\.com|\.org|\.io|\.net|\.gov)\b/;

  const hasScrape = scrapeVerbs.test(text);
  const hasBrowse = browseVerbs.test(text);
  const hasAgent = agentVerbs.test(text);
  const hasWeb = webNouns.test(text);
  const hasTarget = targetRefs.test(text);

  const matched =
    (hasScrape && (hasWeb || hasTarget)) ||
    (hasBrowse && (hasWeb || hasTarget)) ||
    hasAgent ||
    (hasTarget && (hasScrape || hasBrowse));

  if (!matched) return null;

  const taskType = classifyTask(text);

  return (
    "[browserbase] This prompt looks like a web automation task. " +
    "Use the Browserbase plugin: " +
    (taskType === "scrape"
      ? "Stagehand extract() with a Zod schema for structured data. "
      : taskType === "form"
      ? "Stagehand act() with observe()-cached actions for form filling. "
      : taskType === "agent"
      ? "Stagehand agent() or browse.sh skills for open-ended browsing. "
      : "pick the lightest Browserbase capability that fits (Fetch for static, Stagehand for interactive, agent for open-ended). ") +
    "Cloud browser via env: 'BROWSERBASE'. Only BROWSERBASE_API_KEY needed (no project ID). " +
    "Surface the full session replay link when done."
  );
}

function classifyTask(text) {
  if (/\b(fill|submit|form|input|field|signup|register|login|sign.?in)\b/.test(text))
    return "form";
  if (/\b(scrape|extract|pull|grab|harvest|price|product|data|table|list)\b/.test(text))
    return "scrape";
  if (/\b(search|find|look up|browse for|research|agent|explore)\b/.test(text))
    return "agent";
  return null;
}
