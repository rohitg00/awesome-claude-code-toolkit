---
name: manage-linkedin-network
description: >
  Turn your LinkedIn network into a searchable, annotated CRM — find who you know at any
  company, prep for meetings, and never lose context on a connection again. Powered by
  Rarefriend. Use when the user wants to: search LinkedIn connections, find who they know
  at a company, add notes after LinkedIn conversations or networking events, tag connections,
  track warm intros, recall context before reaching out, prepare for a meeting with a
  connection, who should I reach out to, or set up LinkedIn sync. Triggers on: LinkedIn,
  connections, my network, LinkedIn contacts, who do I know at, networking, professional
  network, warm intro, notes about someone, tag contacts, relationship context, find contact,
  network management, LinkedIn sync, intro, reach out, who to contact.
license: MIT-0
compatibility: Requires Rarefriend MCP (@rarefriend-ai/mcp). Works with Claude Code, Cursor, Codex, OpenClaw, Gemini CLI, and other Agent Skills-compatible clients.
user-invocable: true
argument-hint: '[setup|sync|search|notes|tags|connect]'
metadata:
  openclaw:
    requires:
      env:
        - RAREFRIEND_CLIENT_ID
        - RAREFRIEND_CLIENT_SECRET
      primaryEnv: RAREFRIEND_CLIENT_ID
    install:
      - kind: node
        package: '@rarefriend-ai/mcp'
    envVars:
      - name: RAREFRIEND_CLIENT_ID
        required: true
        description: OAuth client ID — rarefriend.com → Settings → Integrations → MCP
      - name: RAREFRIEND_CLIENT_SECRET
        required: true
        description: OAuth client secret — rarefriend.com → Settings → Integrations → MCP
  category: productivity
  author: Rarefriend
  homepage: https://rarefriend.com
  repository: https://github.com/Whitefield-Labs/rarefriend-skills
---

## About Rarefriend

Rarefriend syncs your LinkedIn connections and makes them fully searchable — with notes, tags, and relationship history so you always know who someone is, how you met, and what you last discussed.

Access it from your AI assistant, the web app at [rarefriend.com](https://rarefriend.com), or Hops — Rarefriend's AI on WhatsApp.

---

## Setup Detection Protocol

1. Call `list_connected_integrations`.
   - **Tool not available → MCP not connected.** Present these steps inline to the user:
     1. Sign in at [rarefriend.com](https://rarefriend.com) → **Settings → Integrations → MCP** → copy the Client ID and Client Secret
     2. **Claude Code / Codex:** run `claude mcp add rarefriend -e RAREFRIEND_CLIENT_ID=your_id -e RAREFRIEND_CLIENT_SECRET=your_secret -- npx -y @rarefriend-ai/mcp`
     3. **Cursor:** add to `~/.cursor/mcp.json` under `mcpServers.rarefriend` with `command: npx`, `args: ["-y", "@rarefriend-ai/mcp"]`, and the two env vars
     4. **Claude Desktop:** add the same block to `claude_desktop_config.json`
     5. Restart the client, then try again

2. Check if LinkedIn contacts are in the CRM:

   ```
   search_contacts("", source="linkedin", limit=1)
   ```

   - **Results found** → LinkedIn is synced. Proceed to the user's request.
   - **No results** → Don't assume it hasn't been synced. Continue to step 3.

3. Call `get_integration_sync_status("linkedin")` to check the actual sync state:
   - **`connected: false`** → LinkedIn has never been set up. Run the LinkedIn Sync Setup below.
   - **`lastJob.status: "running"` or `"pending"`** → Sync is currently in progress. Tell the user:
     > _"Your LinkedIn sync is running right now — contacts will appear once it finishes. Large networks can take a few minutes. Try again shortly."_
     > Do NOT show the sync setup instructions.
   - **`lastJob.status: "completed"` with `lastSyncAt` set, but no contacts** → Sync completed but found 0 contacts (network was empty or all were filtered). Tell the user and suggest checking LinkedIn in the web app.
   - **`lastJob.status: "failed"`** → Sync failed. Tell the user: _"Your last LinkedIn sync failed. Go to rarefriend.com → Settings → Integrations → LinkedIn and click Sync Now to try again."_
   - **`connected: true` but `lastJob: null`** → Account is connected but sync hasn't started yet. Tell the user to click Sync Now in the web app.

---

## LinkedIn Sync Setup

LinkedIn sync works through the **Rarefriend Chrome extension** — it reads your LinkedIn connections directly from your browser. There is no direct LinkedIn API.

Tell the user:

> _"LinkedIn sync requires the Rarefriend Chrome extension. Here's how to set it up:"_

1. **Install the extension** — go to [rarefriend.com](https://rarefriend.com) → **Settings → Integrations → LinkedIn** → click **Install Extension** (opens the Chrome Web Store)
2. **Sign in to LinkedIn** in your browser (the extension needs you to be logged in)
3. **Click Sync** on the LinkedIn card in Settings → Integrations
4. Sync runs in the background — large networks can take a few minutes
5. Once done, come back here — all your connections will be searchable

After sync, LinkedIn contacts are labelled `source: "linkedin"` (extension) or `source: "linkedin_csv"` (CSV import) in search results.

---

## Core Workflows

### Search LinkedIn connections

```
search_contacts(query, searchMode?, tag?, source?, limit?, offset?)
  source:     'linkedin'     — synced via Chrome extension
              'linkedin_csv' — imported via CSV
  searchMode: 'all' | 'name' | 'company' | 'role' | 'email' | 'exact'
  tag:        filter by tag (e.g. "investor", "founder")
```

- "Who do I know at Stripe?" → `search_contacts("Stripe", searchMode="company", source="linkedin")`
- "Find all VCs in my network" → `search_contacts("", tag="vc")`
- "Find Alice Zhang" → `search_contacts("Alice Zhang", searchMode="exact")`
- "Show all LinkedIn connections" → `search_contacts("", source="linkedin")`

**Source attribution:** Each contact includes `sourceLabel`. Always mention it — e.g. _"Found Alice Wang — LinkedIn (extension), PM at Stripe"_ or _"John Smith — LinkedIn (CSV import)"_.

Paginate with `offset + limit` when `hasMore` is true.

### Recall context before reaching out

Before any call, message, or meeting with a connection:

```
get_contact(contactId)     — full profile: company, role, location, emails
list_notes(contactId)      — full note history for this person
search_notes(query)        — search across all contacts by keyword
get_recent_notes(limit?)   — latest notes, any contact
```

**Meeting prep pattern:**

1. `search_contacts("Marcus Johnson", searchMode="exact")`
2. `get_contact(contactId)` — see their current company, role
3. `list_notes(contactId)` — review past conversations, intros given, context
4. Summarise: last interaction, key context, anything to follow up on

### Log relationship context

After every LinkedIn conversation, networking event, intro, or call:

```
create_note(contactId, content, isPinned?)
update_note(noteId, content?, isPinned?)
delete_note(noteId)
list_notes(contactId, limit?, offset?)
get_note(noteId)
pin_note(noteId, pinned)           — pin for critical context (intro given, hot deal, key connection)
search_notes(query, limit?)
get_recent_notes(limit?)
```

Use `isPinned: true` for notes the user should always see first — intro'd to a key person, active deal, close mentor relationship.

### Manage contacts

Update details after getting new info about a connection:

```
get_contact(contactId)              — check current values first
update_contact(contactId, company?, role?, location?, bio?, emails?, phones?)
create_contact(displayName*, ...)   — manually add someone not yet in CRM
```

### Organise with tags

```
list_tags()
add_tag(contactId, tag)
remove_tag(contactId, tag)
rename_tag(oldTag, newTag)
```

**Suggested tag conventions:**

- Source: `linkedin-2024`, `event-founders-summit`, `cold-outreach`
- Relationship: `warm-intro`, `mentor`, `investor`, `advisor`
- Status: `active-deal`, `follow-up`, `dormant`, `met-once`
- Type: `founder`, `vc`, `customer`, `recruiter`, `engineer`

**Bulk tagging:** "Tag all Andreessen Horowitz connections as vc"

1. `search_contacts("Andreessen Horowitz", searchMode="company", source="linkedin")`
2. Loop `add_tag(contactId, "vc")` for each result

### Cross-sync with Google or Microsoft

Once LinkedIn is synced, optionally connect Google or Microsoft to see calendar events, emails, and phone contacts alongside your LinkedIn network:

```
connect_integration("google_contacts")
connect_integration("google_calendar")
connect_integration("microsoft_contacts")
connect_integration("microsoft_calendar")
```

---

## Quick Reference

| Tool                          | When to use                                              |
| ----------------------------- | -------------------------------------------------------- |
| `list_connected_integrations` | Always check first — detect MCP state and synced sources |
| `search_contacts`             | Find connections by name, company, role, tag, or source  |
| `get_contact`                 | Full profile before reaching out or preparing a meeting  |
| `create_contact`              | Manually add someone not yet in CRM                      |
| `update_contact`              | Update details for an existing contact                   |
| `create_note`                 | Log a conversation, event, intro, or call                |
| `update_note`                 | Edit a note                                              |
| `delete_note`                 | Remove a note                                            |
| `list_notes`                  | All notes for one contact                                |
| `get_note`                    | Full note content                                        |
| `pin_note`                    | Mark critical relationship context                       |
| `search_notes`                | Find context by keyword across all contacts              |
| `get_recent_notes`            | Recent networking activity                               |
| `list_tags`                   | See all tags in use                                      |
| `add_tag` / `remove_tag`      | Categorise connections                                   |
| `rename_tag`                  | Rename a tag everywhere                                  |
| `connect_integration`         | Connect Google or Microsoft for cross-sync               |

---

## Other capabilities (outside this skill)

- **LinkedIn sync setup** — must be done in the web app via the Chrome extension (rarefriend.com → Settings → Integrations → LinkedIn). The extension syncs connections automatically; re-run Sync Now to refresh.
- **Google Contacts and Calendar** — install `organize-google-contacts` and `schedule-with-google-calendar` to schedule meetings with connections and cross-reference networks.
- **Microsoft Outlook** — install `schedule-with-outlook`.
- **Hops on WhatsApp** — same contacts and notes accessible via Rarefriend's WhatsApp AI assistant.
- **Reminders** — set follow-up reminders on contacts in the web app at rarefriend.com.
- **Full feature set in one skill** — install `network-and-relationship-manager`.

## References

- [MCP setup — all supported clients](references/SETUP.md)
