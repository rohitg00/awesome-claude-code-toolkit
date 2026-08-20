#!/usr/bin/env node
/**
 * multi-page-crawler.js  (UserPromptSubmit hook)
 *
 * Detects "crawl this site" / "scrape all pages" intent and injects
 * orchestration patterns for paginated, multi-page scraping with
 * URL deduplication and aggregated results.
 */

const { run } = require("./lib/prompt-hook");
run(analyze);

function analyze(promptRaw) {
  const text = String(promptRaw || "").toLowerCase();
  if (!text) return null;

  const crawlIntent =
    /\b(crawl|spider|scrape all|all pages|every page|paginate|next page|multiple pages|site.?wide|entire site|whole site)\b/.test(text);

  const webContext =
    /\bhttps?:\/\/\S+/.test(text) ||
    /\b(site|website|web ?page|url|browser|crawl|scrape)\b/.test(text);

  const listIntent =
    /\b(all|every|each|complete list|full list)\b/.test(text) &&
    /\b(product|item|page|link|article|listing|result)\b/.test(text) &&
    webContext;

  const paginationSignal =
    /\b(page \d|pagination|load more|show more|next|previous|offset|cursor)\b/.test(text) &&
    webContext;

  if (!crawlIntent && !listIntent && !paginationSignal) return null;

  return (
    "[browserbase:multi-page-crawler] Multi-page crawl detected. Use this orchestration pattern:\n\n" +
    "```js\n" +
    "const visited = new Set();\n" +
    "const results = [];\n" +
    "const queue = [startUrl];\n" +
    "const MAX_PAGES = 50; // safety cap\n" +
    "const SAME_DOMAIN = new URL(startUrl).hostname;\n" +
    "\n" +
    "while (queue.length > 0 && visited.size < MAX_PAGES) {\n" +
    "  const url = queue.shift();\n" +
    "  if (visited.has(url)) continue;\n" +
    "  visited.add(url);\n" +
    "\n" +
    "  await page.goto(url, { waitUntil: 'domcontentloaded' });\n" +
    "\n" +
    "  // Extract data from current page\n" +
    "  const data = await stagehand.extract({ instruction, schema });\n" +
    "  results.push({ url, ...data });\n" +
    "\n" +
    "  // Discover links for next pages (pagination or internal links)\n" +
    "  const links = await stagehand.extract({\n" +
    "    instruction: 'Find pagination links or next-page buttons',\n" +
    "    schema: z.object({ urls: z.array(z.string()) }),\n" +
    "  });\n" +
    "\n" +
    "  for (const link of links.urls) {\n" +
    "    try {\n" +
    "      const parsed = new URL(link, url);\n" +
    "      if (parsed.hostname === SAME_DOMAIN && !visited.has(parsed.href)) {\n" +
    "        queue.push(parsed.href);\n" +
    "      }\n" +
    "    } catch {}\n" +
    "  }\n" +
    "}\n" +
    "```\n\n" +
    "Rules:\n" +
    "- Stay within the same domain (no external links)\n" +
    "- Deduplicate URLs before visiting\n" +
    "- Cap at 50 pages max (adjustable)\n" +
    "- Aggregate all results into a single array\n" +
    "- Report progress: 'Scraped page X of Y...'\n" +
    "- On error, save partial results and report which pages failed\n" +
    "- For pagination: detect 'Next' buttons via observe() and click them with act()"
  );
}
