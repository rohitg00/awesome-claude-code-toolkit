# Enrichment architecture & tool evaluation (Layers G/H/I)

Goal: reconcile/dedupe and **backfill missing primary fields** (phone, email,
address, url), resolve **profile photos**, and **cross-reference LinkedIn** —
using free, open-source, GitHub-sourced tools, chosen on **capability + speed**,
with everything routed through one JEV-graded candidate pipeline and nothing
overwriting canonical data without confirmation.

## Design: one candidate pipeline

```
detect_missing ─▶ resolvers (built-in + agent/OSINT) ─▶ grade (source×corroboration)
                                                             │
                                          enrichment_candidates (proposed)
                                                             │
                                   review ─▶ confirm ─▶ canonical contact + change_log ─▶ sync
```

- **Built-in resolvers** are deterministic, offline, zero-dependency, so they run
  inline and are fully tested: `gravatar`, `libravatar`, `company_website`,
  `public_directory`, `linkedin_candidate`.
- **Heavy OSINT tools** (below) are **not** bundled or scraped from package code —
  they need network, rate-limit handling, and sometimes raise ToS concerns. They
  are declared in `enrich.base.EXTERNAL_RESOLVERS`; the agent runs them
  out-of-band and feeds results back via `generate(conn, extra=[…])`, where they
  are graded and stored like any other candidate.

## Tool evaluation (free / OSS / GitHub)

| Need | Tool | Why (capability / speed) | How integrated |
|---|---|---|---|
| Photo from email | **Gravatar** (hash URL) | O(1), no dep, no key; near-universal | built-in `gravatar` |
| Photo (federated) | **Libravatar** | self-hosted/federated fallback of Gravatar | built-in `libravatar` |
| Photo/title/phone | **Public-entity employee directory** | public employees' directories are standard and carry photo+title+contact | built-in `public_directory` (proposes the fetch target) |
| Email → accounts | **holehe** (`megadose/holehe`) | email across 120+ sites via recovery probes; fast, no keys | external; agent runs, feeds `account`/photo candidates |
| Username → profiles | **maigret** (`soxoj/maigret`) | 2000+ sites, broader & faster than Sherlock; returns avatars | external |
| Google account | **GHunt** (`mxrch/GHunt`) | profile photo + name for a Google email | external |
| Phone validity | **phonenumbers** (already a dep) | E.164 parse + validity | inline in normalize |
| Email deliverability | DNS-MX (`dnspython`, optional) | cheap MX existence check | optional, no hard dep |

**Photo source priority** (per the weighting requested): saved contacts / iCloud
and **public-entity domains** and **confirmed LinkedIn** rank highest; Gravatar /
Libravatar / GHunt are graded fallbacks (`enrich.grade.SOURCE_WEIGHTS`).

## LinkedIn (policy)

No scraping in package code. `linkedin_candidate` generates a **search candidate**
only; the agent confirms a match via the LinkedIn MCP and calls `confirm_linkedin`,
which saves the URL to the contact's **LinkedIn** field (only when it matches the
employer) and promotes the LinkedIn **profile photo** to the contact photo.

## REA / reverse-engineering hook

Adding a resolver is a ~15-line class with `name`, `provides`, and `resolve()`,
registered via `@register`. When the REA skill reverse-engineers a faster/stronger
method for a field, it drops in a new resolver (or an `EXTERNAL_RESOLVERS` entry)
and the grading/corroboration pipeline measures it against the incumbents by the
grade its candidates earn — the architecture is additive, so improvements slot in
without touching the canonical store.
