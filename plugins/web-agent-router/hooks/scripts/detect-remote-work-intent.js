#!/usr/bin/env node
/**
 * detect-remote-work-intent.js  (UserPromptSubmit, plugin-scoped)
 *
 * Detects when a prompt references any remote/web task — browsing, scraping,
 * crawling, form-filling, monitoring a page, testing a site — across ANY
 * installed web tool (Fetch, Firecrawl, Puppeteer/Playwright, Browserbase),
 * not just one. On a match it instructs Claude to run the routing gate
 * (skills/web-agent-router) via AskUserQuestion BEFORE picking a tool, unless
 * the user already named a specific tool. Never blocks or rewrites the
 * prompt; on no match it stays silent.
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

  const remoteVerbs =
    /\b(scrape|crawl|extract|pull|grab|harvest|monitor|fetch|browse|navigate|click|fill|submit|login|sign.?in|automate|visit|screenshot|test)\b/;
  const webNouns =
    /\b(web ?page|web ?site|url|page|site|form|button|link|browser|html|dom|selector|sitemap)\b/;
  const targetRefs = /\bhttps?:\/\/\S+|\b\S+\.(com|org|io|net|gov|dev|app)\b/;
  // Mentioning a specific tool by name is itself an unambiguous signal —
  // it doesn't need a verb+noun pair to count as a match.
  const namedTool = /\b(firecrawl|browserbase|puppeteer|playwright|stagehand)\b/.test(text);

  const matched =
    namedTool ||
    (remoteVerbs.test(text) && (webNouns.test(text) || targetRefs.test(text))) ||
    (remoteVerbs.test(text) && targetRefs.test(text));

  if (!matched) return null;

  // If the user already named a specific tool, don't force the gate —
  // let Claude use what was asked for.
  if (namedTool) {
    return (
      "[web-agent-router] Remote/web task with a tool already named in the prompt — " +
      "use that tool directly, no need to run the routing gate."
    );
  }

  return (
    "[web-agent-router] This prompt looks like a remote/web task (browsing, scraping, " +
    "crawling, form-filling, or site testing) and no specific tool was named. " +
    "Before picking a tool, run the routing gate from skills/web-agent-router: ask ONE " +
    "AskUserQuestion with the 4-way task-shape options (single page read / multi-page " +
    "crawl / automate my own app / interact with a third-party site), then use the tool " +
    "that question maps to (Fetch / Firecrawl / Playwright-Puppeteer / Browserbase). " +
    "Skip the gate only if the task is trivially obvious AND low-stakes (e.g. fetching one " +
    "well-known static doc URL)."
  );
}
