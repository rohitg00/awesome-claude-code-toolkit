# /browserbase:fill-form

Fill out and submit a web form using Browserbase cloud browsers and Stagehand act.

## Process

1. Identify the target form URL and the fields to fill.
2. Create a Stagehand script with `env: "BROWSERBASE"` and `cacheDir` set.
3. Navigate to the form page with `waitUntil: "domcontentloaded"`.
4. Use `page.observe()` to discover available form fields and cache the results.
5. For each field, use `page.act()` with `%variables%` for dynamic values.
6. Use `page.act("Click the Submit button")` to submit the form.
7. Confirm submission by extracting a success message or checking the resulting page.
8. Surface the session replay link so the user can watch the form being filled.

## Format

```
Form: <URL>
Fields: <field1=value1, field2=value2, ...>
Result: <success/failure + details>
Session: <full browserbase.com/sessions/<id> link>
```

## Rules

- Keep each `act()` call atomic: one field or one click per call.
- Use `%variables%` for dynamic values — string interpolation breaks caching.
- Use `observe()` first to discover fields, then replay cached actions for speed.
- Wait for form elements to be ready with `observe()`, never `setTimeout`.
- Never submit forms containing real credentials or PII in demo/test runs.
