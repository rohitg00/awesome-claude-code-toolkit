# Project Ignition (Jev platform)

**Purpose:** put the upfront blueprinting and the back-end number work in Jev's
deterministic, typed lane, and spend frontier-model tokens only on the part that
needs them: Astra and Opus producing the numbers and the narrative.

```
 CPR + Plans Atlas
        |
        v
 [1] BLUEPRINT  (deterministic, $0)        ignition.py blueprint
        |  division packets, CPM skeleton, typed work orders
        v
 [2] MAGIC      (frontier seats)           Astra  gpt-6-astra        -> raw/astra.json
                                           Opus   claude-opus-5-5    -> raw/opus.json
                                           Compass (Perplexity)      -> benchmarks.csv
        v
 [3] JEV        (deterministic, typed)     ignition.py process
        |  PERT compare, CPM, unit-price decisions,
        |  confidence dating, $/SF sanity
        v
 [4] ITB PAGES  (8.5 x 11)                 ignition.py itb [--pdf]
```

## Who does what

- **Jev ("Gavel")** referees. Typed answers only, no opinions, no vote. Every
  judgment is an enum with a rationale, logged to `jev-judgments.jsonl` so the
  council engine can replay it through the hosted Jev model. The rules in
  `ignition.py` answer first at zero cost.
- **Astra** (`gpt-6-astra`) and **Opus** (`claude-opus-5-5`) each answer the same
  work order independently. Two independent answers are what make the comparison
  meaningful.
- **Compass** (Perplexity `sonar-pro`) supplies public $/SF rows with citations.
- **Never** send work orders to **Ledger** (DeepSeek) or **Mason** (GLM): they
  contain owner, bid and pricing content.

## Files (all under `<project>/model/ignition/`)

- **`blueprint.json`**: facts, gaps, CPM tasks, one packet per division (scope
  items, takeoff, existing cost lines, spec sections, sheets, price lines).
- **`work-orders/astra.json`, `opus.json`, `compass.json`**: ready to run.
- **`raw/astra.json`, `raw/opus.json`**: the seat replies (shape in
  `schemas/ignition-output.schema.json`).
- **`benchmarks.csv`**: public $/SF rows (template in `resources/benchmarks/`).
- **`processed.json`**: PERT, schedule, price decisions, confidence, sanity,
  `needs_human_review`.
- **`jev-judgments.jsonl`**: every typed judgment.
- **`itb/`**: `itb-packages.html` (+ `.pdf`) and `ignition-summary.html` (internal).

## Decision rules (all deterministic)

**PERT.** E = (O + 4M + P) / 6, sd = (P - O) / 6, working days.
Gap between the two seats' E: agree up to 15%, minor up to 35%, divergent above.
Agree or minor use the mean; divergent uses the higher value and escalates.
Combined sd = sqrt(mean variance + (gap / 2)^2), so disagreement widens the range.
One seat only: used, sd widened 25%, flagged.
**CPM:** phases run finish-to-start (P0 mobilize, P1 demo and site, P2 structure
and enclosure, P3 rough-in, P4 finishes, P5 closeout). Output: critical path,
expected and P80 duration, and the chance of meeting a stated contract duration.

**Not applicable.** Each division packet carries an `evidence` count (sheets, spec
sections, scope items, takeoff, cost lines, trade package). A packet with none of
those but a stray spec mention is `low_evidence`, and the work order tells the seats
to return it `not_applicable` with a reason. When every answering seat agrees, Jev
records `not_applicable`, the task drops to zero days, and the division gets no
price lines and no ITB page.

**Unit prices, in order:**
1. A JOC contract unit price is **never overridden** (`contract_price`).
2. Seats within 10%: mean. Within 25%: mean, unless only one cites a dated source.
3. Wider than 25%: take the documented price; else the one nearest an existing
   CPR rate; else **escalate** (mean is provisional).
4. One seat only: `single_source`. No seat: `no_price`.

**Confidence** = freshness x basis x agreement.
- Freshness by price age: up to 90 days 1.0, to 180 days 0.9, to 365 days 0.75,
  older 0.5, undated 0.4.
- Basis: vendor quote 1.0, book 0.95, public bid 0.9, model estimate 0.6.
- Agreement: agree 1.0, minor 0.85, divergent 0.6, single source 0.75.
- **Valid through** = price date + shelf life: 90 days for divisions 05 and 26,
  120 days for 07, 22, 23, 31, 32, otherwise 180.
- Range on each extended cost = +/- (1 - confidence) x 50%.

**$/SF sanity.** Area is `building.gross_sf`; when only `building.work_area_sf` (the renovated area as printed on the drawings) is known, the check runs on that and says so in `sf_basis` and a caveat. Direct cost (plus markups if `--markup-pct` is given) divided by
gross SF, against the best sourced benchmark row: same city beats same state beats
national, newest year wins, building type and project type must fit. Verdict:
`within_band`, `below_band`, `above_band`, `no_benchmark` or `no_sf`. Division-level
rows (`scope` = division number) add per-division checks. Caveats are printed when
the benchmark is not hard cost or is two or more years old.

## Guardrails

- **Draft only.** `status: draft_pending_pm_approval`; nothing leaves the building.
- **Never invent.** No gross SF means no $/SF check. No benchmark row means
  `no_benchmark`, never a made-up band. Seat quantities that replace missing
  takeoff quantities are flagged for verification against the drawings.
- **ITB pages carry no prices**, no budget and no margin; the internal summary is
  the only file with pricing.
- Replies that fail validation are flagged in `needs_human_review`, not repaired.

## Run it

```
python scripts/ignition.py blueprint --project <dir>        # or deploy_atlas.py --ignite
python scripts/ignition.py seats     --project <dir>        # runs work-orders on Astra (codex CLI) and Opus (claude CLI)
# or run work-orders/astra.json and opus.json yourself; save replies under raw/
python scripts/ignition.py process   --project <dir> --markup-pct 0.18
python scripts/ignition.py itb       --project <dir> --pdf
python scripts/ignition.py selftest                          # math, rules, no-price-leak check
```

## Limits to know

- `seats` uses the logged-in `claude` and `codex` CLIs (the user's own accounts). It makes one validated retry per seat; replies that still fail validation are kept and flagged in `needs_human_review`. Its `run` block records the CLI and attempts.
- The local rules answer Jev's judgments. Replaying `jev-judgments.jsonl` through
  the hosted Jev model is a council-engine step; the hosted endpoint is not called
  from this script.
- Phases run strictly finish-to-start; real overlap shortens the schedule, so the
  CPM is a conservative first pass.
- The $/SF check is only as good as the cited benchmark rows Compass supplies.
