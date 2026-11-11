# /browserbase:scrape-page

Scrape a web page using Browserbase cloud browsers and Stagehand extract.

## Process

1. Determine the target URL and what data to extract.
2. Check whether the target needs a full browser (JavaScript-rendered, interactive) or a lightweight fetch (static HTML). Default to Stagehand for anything uncertain.
3. Define a Zod schema for the structured output — name every field with its type.
4. Create a Stagehand script with `env: "BROWSERBASE"` and `cacheDir` set.
5. Navigate to the target URL with `waitUntil: "domcontentloaded"`.
6. Use `page.extract()` with the schema and a clear instruction describing what to pull.
7. Run the script and confirm a session appears on the Browserbase dashboard.
8. Surface the extracted data and the full session replay link.

## Format

```
Target: <URL>
Data: <fields extracted>
Session: <full browserbase.com/sessions/<id> link>
```

## Rules

- Always use `env: "BROWSERBASE"` — never run headless locally for this command.
- Set `cacheDir: "./stagehand-cache"` so repeated runs are faster.
- Never set `BROWSERBASE_PROJECT_ID` — the API key resolves the project.
- Leave `MODEL_API_KEY` blank on free-tier accounts so Model Gateway handles LLM calls.
- If the target site is bot-protected (LinkedIn, Yelp, Instagram, etc.), warn the user before running.
