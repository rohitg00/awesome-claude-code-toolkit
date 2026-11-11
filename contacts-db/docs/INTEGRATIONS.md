# Interlinking: NTXP Contacts ⇄ Schedules · Master Contracts · Form Fill

```
                      ┌────────────── NTXP Contacts (contacts.ntxpllc.cloud) ──────────────┐
 Master Contracts ◄───┤ pulls  GET /api/changes, /api/contracts  (cheap delta probe)        │
   (contracts)        │ → facts on every card + "Contract <no>" label to filter by           │
                      │                                                                      │
 Schedules        ◄───┤ webhook  contact.upserted / contact.removed  (signed, retried)       │
   (schedules)    ───►│ POST /api/v1/hooks/in/schedules   assignment.upserted / .removed     │
                      │                                                                      │
 Form Fill        ◄───┤ webhook  contact.upserted / contact.removed                           │
   (formfill)     ───►│ POST /api/v1/hooks/in/formfill    people.seen                         │
                  ───►│ GET  /api/v1/people/resolve · /people/<id> · /context  (autofill)    │
                      └──────────────────────────────────────────────────────────────────────┘
```

**Status of each side — read this first.** *Master Contracts* is integrated against its real, existing API (it is in
this repo and the integration is tested against its actual server). *Schedules* and *Form Fill* live elsewhere and
their code wasn't available when this was built, so this document **is the contract they implement** (what we send,
what we accept, exact schemas). Our side is fully built and tested against a local receiver and the Node reference
verifier below; the first end-to-end run against the real Schedules / Form Fill apps still has to happen.

## 1. Connect an app (once)

```bash
ntxp peers keygen schedules      # prints a secret ONCE (not stored) + a service token
```
Put the same secret in the peer app **and** in `NTXP_PEERS` here:
```json
{"schedules": {"url": "https://<schedules-host>.ntxpllc.cloud", "secret": "<secret>", "hook_path": "/hooks/ntxp-contacts"},
 "contracts": {"url": "https://<contracts-host>.ntxpllc.cloud", "secret": "<secret>"},
 "formfill":  {"url": "https://<formfill-host>.ntxpllc.cloud",  "secret": "<secret>", "events": ["contact.*"]}}
```
Rules enforced at load: **https only, host must end in `.ntxpllc.cloud`**, no credentials in the URL, secret ≥ 24 chars
without `.`. A bad entry is reported by `ntxp peers status` and skipped (never crashes the app). One secret per peer, so a
compromised app cannot forge another's traffic. When first connecting a peer, send it everything once:
`ntxp peers backfill formfill`. Check health any time: `ntxp peers status` (queue counts, dead letters, cursors; no secrets).

## 2. Signing (both directions)
`X-NTXP-Signature: t=<unix-seconds>,v1=<hex HMAC-SHA256(secret, "<t>." + rawBody)>`, 5-minute replay window, constant-time
compare. Verify against the **raw** body bytes. Reference implementation (tested against our signer):
[`docs/examples/verify_webhook.js`](examples/verify_webhook.js). Python:
```python
import hmac, hashlib, time
def verify(secret, raw: bytes, header: str, now=None):
    p = dict(x.split("=", 1) for x in header.split(","))
    if abs((now or time.time()) - int(p["t"])) > 300: return False
    mac = hmac.new(secret.encode(), f"{p['t']}.".encode() + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, p["v1"])
```

## 3. What we send you — outbound webhooks (`POST <url><hook_path>`)
Headers: `X-NTXP-Event`, `X-NTXP-Event-Id` (use it to de-duplicate), `X-NTXP-Timestamp`, `X-NTXP-Signature`.
Reply **2xx quickly**. `408/425/429/5xx`/timeout → retried with backoff (30 s, 60 s, … up to 1 h, 8 attempts, then
dead-lettered: `ntxp peers status` lists them, `ntxp peers retry <id>` re-queues). Any other `4xx` = "permanent", dead at once.
```json
{"id": "formfill:42-9107", "type": "contact.upserted", "created_at": "2026-10-30T14:03:11+00:00",
 "data": {"id": 42, "full_name": "Eric Vaden", "first_name": "Eric", "last_name": "Vaden", "title": "Owner",
          "company": "Vaden Drywall", "website": "https://vaden.com",
          "email": "eric@vaden.com", "emails": ["eric@vaden.com"], "phone": "+18178478822", "phones": ["+18178478822"],
          "address": {"line1": "411 Elm St", "city": "Fort Worth", "state": "TX", "zip": "76102"},
          "role": "Sub", "trade": "Drywall", "project": "Spruce HS", "labels": ["DBE", "Spruce HS", "Contract RFP-2024-77"],
          "contracts": [{"number": "RFP-2024-77", "title": "Statewide JOC", "coefficient": 1.12, "cooperative_fee": "2%",
                         "expires": "2026-11-29", "executed": true, "flags": ["expiring"], "days_to_expiry": 30, "pdf_url": "…"}],
          "linkedin_url": null, "photo_url": null, "grade_band": "A", "updated_at": "…", "href": "https://contacts.ntxpllc.cloud?focus=contact:42"}}
{"id": "formfill:42-9120", "type": "contact.removed", "data": {"id": 42, "merged_into": null}}
```
* **Exposure-gated**: only contacts the quality grader exposes are ever sent. A contact that is deleted, merged *or held back
  as outdated* arrives as `contact.removed` with **no PII**. Treat it as "delete your copy".
* **No echo**: a change that came *from* a peer is never sent back to that same peer (it is sent to the others).
* Ordering isn't guaranteed across retries — compare `data.updated_at`; the latest wins. The first run after enabling a peer
  records a starting point only (no flood); use `ntxp peers backfill <peer>` for the initial sync.
* `events` in a peer's config filters by pattern (`contact.*`, `contact.removed`).

## 4. What you send us — inbound webhooks (`POST /api/v1/hooks/in/<peer>`, signed, no bearer)
Body `{"id": "<unique event id>", "type": "...", "data": {...}}`. Applied exactly once per `id` (re-delivery returns
`{"duplicate": true}`). Unknown `type` → `200 {"ignored": ...}` so you can add events without breaking us.

**Schedules** — `assignment.upserted` / `assignment.removed`
```json
{"id": "sch-evt-881", "type": "assignment.upserted",
 "data": {"assignment_id": "A-1042", "project": "Natatorium", "role": "Sub", "start": "2026-11-02", "end": "2026-11-20",
          "status": "scheduled|active|completed|cancelled", "person": {"contact_id": 42}}}
```
`person` is `{"contact_id": n}` or `{"email": "..."}` — **exact match only, never fuzzy** (otherwise `{"matched": false}`; get
ids from `/api/v1/people/resolve`). Effect: the assignment shows on that person's card and in prompt-injected context
(`🗓 active: Natatorium (2026-11-02 → 2026-11-20)`); the project becomes a filterable project tag in the live app (people can
be on several projects; the project filter matches any). Ended or `cancelled` assignments drop off the card.

**Form Fill** — `people.seen` (people captured on a filled form; ≤ 200 per event)
```json
{"id": "ff-evt-77", "type": "people.seen",
 "data": {"form": "W-9", "people": [{"name": "Dana Okafor", "email": "dana@okaforbuilders.com", "phone": "214-555-0188",
          "company": "Okafor Builders", "title": "Estimator", "address": {"line1": "9 Elm St", "city": "Plano", "state": "TX", "zip": "75024"}}]}}
```
Goes through the normal de-duplicating resolver (a known person is merged, not duplicated), is labelled `Form: <form>`, and is
graded like any other source.

## 5. What you can ask us — `/api/v1` (Bearer `svc.<peer>.<secret>`; read-only; exposure-gated)
```
GET /api/v1/people/resolve?email=…|phone=…|q=…&limit=10   -> {"matches":[{id, full_name, company, email, phone, …}]}
GET /api/v1/people/<id>        -> the full autofill bag above + "assignments"   (404 if not exposed)
GET /api/v1/context?id=…|q=…   -> {"card": {...}, "text": "**Eric Vaden** — Owner · Vaden Drywall — ✉ … 📄 contract: … 🗓 …"}
GET /api/v1/ping
```
A peer token works **only** on `/api/v1` — it is refused on the human `/api`, `/mcp` and `/carddav`. Form Fill's autofill flow:
resolve by email → `people/<id>` → fill name, title, company, address, phone, plus contract number/coefficient from `contracts[]`.

## 6. Master Contracts (we read, never write)
Every cycle (default 30 s) we call `GET /api/changes?since=<seq>`; only when it reports a change do we fetch
`GET /api/contracts`. Each contract's **owner entity** is matched to our organizations by normalized name (we never create
organizations or contacts from contract data). Matched orgs get the contract's facts on every contact's card and an org label
**`Contract <number>`**, so the live page can filter "everyone at organizations on contract X". Flags are computed at read time:
`expired`, `expiring` (≤ 90 days), `unexecuted`. Deleting a contract removes its facts and label on the next cycle.
We send `Authorization: Bearer svc.contacts.<secret>` in case your Master Contracts is behind the same scheme; if it uses
other auth, tell us and it's a one-line change in `peers/contracts.py`.

## 7. Operations & security
* Runs inside `ntxp serve-http` (background thread; `NTXP_PEERS_INTERVAL`, default 30 s). Prefer cron? set `NTXP_PEERS_AUTORUN=0`
  and run `ntxp peers run --watch`. Delivery uses a leased outbox in the database (Supabase), so it survives restarts and is safe
  with more than one worker.
* A peer being down never blocks the others (each pull/delivery is isolated).
* Rotate a secret by changing it in both places (webhooks signed with the old one are rejected until both sides match).
* PII travels only between NTXP hosts: outbound URLs are restricted to `*.ntxpllc.cloud` over https.
