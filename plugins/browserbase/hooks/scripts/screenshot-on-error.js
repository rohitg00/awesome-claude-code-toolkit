#!/usr/bin/env node
/**
 * screenshot-on-error.js  (UserPromptSubmit hook)
 *
 * Wraps Stagehand browser sessions with automatic screenshot capture on error.
 * When a browser action fails, saves a timestamped full-page screenshot to
 * .browserbase/screenshots/ and injects debug context into the conversation.
 */

const fs = require("fs");
const path = require("path");

const SCREENSHOT_DIR = path.join(process.cwd(), ".browserbase", "screenshots");

const { run } = require("./lib/prompt-hook");
run(analyze);

function analyze(promptRaw) {
  const text = String(promptRaw || "").toLowerCase();
  if (!text) return null;

  const isBrowserTask =
    /\b(scrape|crawl|extract|browse|navigate|click|fill|submit|automate|stagehand)\b/.test(text) ||
    /\bhttps?:\/\/\S+/.test(text);

  if (!isBrowserTask) return null;

  ensureScreenshotDir();

  return (
    "[browserbase:screenshot-on-error] Auto-screenshot is active for this browser session. " +
    "If any Stagehand action throws, capture a screenshot BEFORE closing the session:\n" +
    "```js\n" +
    "try {\n" +
    "  // ... stagehand actions\n" +
    "} catch (err) {\n" +
    "  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');\n" +
    "  const screenshotPath = `${screenshotDir}/${timestamp}.png`;\n" +
    "  await page.screenshot({ path: screenshotPath, fullPage: true });\n" +
    "  console.error(`Screenshot saved: ${screenshotPath}`);\n" +
    "  throw err;\n" +
    "}\n" +
    "```\n" +
    `Screenshot directory: ${SCREENSHOT_DIR}\n` +
    "Always report the screenshot path to the user on failure."
  );
}

function ensureScreenshotDir() {
  try {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  } catch {
    // Directory may already exist or be unwritable — non-fatal
  }
}
