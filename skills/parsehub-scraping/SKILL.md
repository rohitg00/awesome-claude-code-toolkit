---
name: parsehub-scraping
description: Run ParseHub scraping projects and pull their data via the ParseHub API v2 — start runs, poll status, retrieve JSON/CSV results. Use when the user mentions ParseHub, or wants to run/schedule an existing point-and-click scraper. Requires PARSEHUB_API_KEY.
---

# ParseHub Scraping

ParseHub is a point-and-click web scraper: you build the extraction visually in the
ParseHub desktop app, then trigger runs and collect results over the API. This skill
covers the API side only — project *authoring* happens in the ParseHub app, not here.

**When ParseHub is the wrong tool:** if there is no existing ParseHub project for the
target site, building one requires the desktop app. For ad-hoc scraping with no
pre-built project, use Browserbase/Stagehand (`skills/browserbase-automation`) instead.

## Setup

```bash
export PARSEHUB_API_KEY=...    # from parsehub.com → Account → API key
```

Never commit the key. `scripts/parsehub.sh` reads it from the environment only.

## API

Base URL `https://www.parsehub.com/api/v2`. The key goes in the query string on GET
and in the form-encoded body on POST. Rate limit is 5 req/sec.

| Action | Method | Endpoint |
|--------|--------|----------|
| List projects | GET | `/projects` |
| Get project | GET | `/projects/{PROJECT_TOKEN}` |
| Run project | POST | `/projects/{PROJECT_TOKEN}/run` |
| Get run status | GET | `/runs/{RUN_TOKEN}` |
| Get run data | GET | `/runs/{RUN_TOKEN}/data` |
| Last ready data | GET | `/projects/{PROJECT_TOKEN}/last_ready_run/data` |
| Cancel run | POST | `/runs/{RUN_TOKEN}/cancel` |
| Delete run | DELETE | `/runs/{RUN_TOKEN}` |

Useful parameters:

- `run`: `start_url`, `start_template`, `start_value_override` (JSON) to parameterize a run
- `data`: `format=json` (default) or `format=csv`
- `list`: `offset`, `limit`, `include_options`

## Workflow

Start → poll → retrieve. A run's `status` moves through `initialized` → `running` →
`complete` (or `cancelled` / `error`); data is only available once `complete`.

```bash
scripts/parsehub.sh projects                      # list projects
scripts/parsehub.sh run <PROJECT_TOKEN>           # start a run, prints run token
scripts/parsehub.sh status <RUN_TOKEN>            # check status
scripts/parsehub.sh data <RUN_TOKEN>              # fetch results (json)
scripts/parsehub.sh last <PROJECT_TOKEN>          # last successful run's data
scripts/parsehub.sh wait <RUN_TOKEN>              # poll to completion, then print data
```

Prefer `last` over `run` when fresh data isn't required — it's free and instant,
whereas each run consumes account run quota.

## Notes

- Runs are asynchronous and can take minutes; poll with backoff rather than a tight
  loop, or configure a webhook in the project settings to avoid polling entirely.
- `start_value_override` is how you reuse one project across many inputs — pass a JSON
  object overriding the project's starting values instead of cloning the project.
- Free-tier accounts have limited pages-per-run and retention; old run data is purged,
  so persist anything you need rather than relying on `last_ready_run`.

## Docs

- API reference: https://www.parsehub.com/docs/ref/api/v2/
