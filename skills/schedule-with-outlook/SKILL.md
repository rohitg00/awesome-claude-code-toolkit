---
name: schedule-with-outlook
description: >
  Manage Microsoft Outlook contacts and calendar from your AI assistant — search contacts,
  schedule Teams meetings, find free time, and keep relationship notes all in one place via
  Rarefriend. Use when the user wants to: search Outlook contacts, schedule an Outlook or
  Teams meeting, check their Outlook calendar, find free time, reschedule or cancel Outlook
  events, add notes about people, tag and organise their Microsoft network, or connect their
  Microsoft account. Triggers on: Outlook, Microsoft, Teams, Exchange, Office 365, Microsoft
  contacts, Outlook calendar, schedule Teams meeting, book meeting, free slot, Outlook contact,
  notes, tags, Microsoft calendar, Teams call, Office meeting.
license: MIT-0
compatibility: Requires Rarefriend MCP (@rarefriend-ai/mcp). Works with Claude Code, Cursor, Codex, OpenClaw, Gemini CLI, and other Agent Skills-compatible clients.
user-invocable: true
argument-hint: '[setup|contacts|calendar|notes|tags|connect]'
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

Rarefriend connects your Microsoft Outlook contacts and calendar to a full relationship layer — notes after every meeting, tags to organise your network, and instant recall on anyone in your Microsoft ecosystem.

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
   - **No Microsoft integrations** → offer to connect. Ask which they need: `microsoft_contacts`, `microsoft_calendar`, or `microsoft_email`.
   - **Microsoft integrations present** → proceed directly.

---

## Core Workflows

### Search contacts

Two search paths — use both for best results:

```
search_contacts(query, searchMode?, tag?, source?, limit?, offset?)
  source: 'microsoft_contacts'   — filter to only Outlook-synced contacts
  searchMode: 'all' | 'name' | 'company' | 'role' | 'email' | 'exact'
  tag: filter to contacts with this exact tag

search_microsoft_contacts(query, limit?)   — searches Outlook/Exchange directory directly
get_microsoft_contact(contactId)           — full Outlook contact details
```

Use `search_contacts` first (broader, includes notes and tags). Use `search_microsoft_contacts` when the user wants to look up the raw Outlook/Exchange directory.

**Source attribution:** Each contact includes `sourceLabel` (e.g. "Microsoft Contacts", "LinkedIn (extension)", "Google Contacts"). Always mention this — e.g. _"Found Sarah Chen in Microsoft Contacts"_ or _"Marcus Lee — LinkedIn (extension), Director at Acme"_.

To edit a contact, use `update_contact` — Microsoft contacts are read-only via the Outlook tools.

### Check Outlook calendar

```
get_upcoming_microsoft_events(limit?, days?)
search_microsoft_calendar_events(query, timeMin?, timeMax?)
```

### Find available time

```
find_available_microsoft_time(durationMinutes, preferredDays?,
                               preferredTimeRange?, attendeeEmails?)
```

Always call before scheduling. For multi-person meetings, pass `attendeeEmails` to check all attendees' availability.

If the user gives a name instead of an email:

1. `search_microsoft_contacts("name")` or `search_contacts("name")` → get email
2. Pass email to `find_available_microsoft_time`

### Create Outlook events

```
create_microsoft_calendar_event(
  title*,
  startTime*,   — ISO 8601 with timezone
  endTime*,
  description?,
  attendees?,   — string[] of email addresses
  location?
)
```

### Reschedule and cancel

```
reschedule_microsoft_event(eventId, startTime, endTime)
cancel_microsoft_event(eventId)
```

Use `search_microsoft_calendar_events` to find the `eventId` first.

### Notes

Notes live in Rarefriend, not Outlook — they persist even if the Microsoft integration is disconnected.

```
create_note(contactId, content, isPinned?)
update_note(noteId, content?, isPinned?)
delete_note(noteId)
list_notes(contactId, limit?, offset?)
get_note(noteId)
pin_note(noteId, pinned)
search_notes(query, limit?)     — full-text across ALL contacts
get_recent_notes(limit?)        — most recent notes, any contact
```

After any meeting or Teams call, create a note immediately. Use `pin_note` for critical context.

### Tags

```
list_tags()
add_tag(contactId, tag)
remove_tag(contactId, tag)
rename_tag(oldTag, newTag)
```

**Bulk tagging:** "tag everyone at Acme Corp as client"

1. `search_contacts("Acme Corp", searchMode="company")`
2. Loop `add_tag(contactId, "client")` for each result

### Connect Microsoft

```
connect_integration("microsoft_contacts")    — Outlook/Exchange contacts
connect_integration("microsoft_calendar")    — Outlook calendar
connect_integration("microsoft_email")       — Outlook email (search inbox, find email threads)
```

Present the returned `connectUrl` as a clickable link:

> _"Open this link in your browser to connect [integration]. It expires in 15 minutes."_

After connecting:

```
get_integration_sync_status("microsoft_contacts")
```

---

## Common Patterns

**"Schedule a Teams call with John next week"**

1. `search_contacts("John", searchMode="name")` or `search_microsoft_contacts("John")` → get email
2. `find_available_microsoft_time(30, preferredDays=["Monday","Tuesday","Wednesday"], attendeeEmails=[john@email])`
3. Confirm slot with user
4. `create_microsoft_calendar_event(title, startTime, endTime, attendees=[john@email])`

**"What meetings do I have this week?"**

1. `get_upcoming_microsoft_events(limit=20, days=7)`
2. Summarise by day

**"Add a note after my call with Sarah"**

1. `search_contacts("Sarah", searchMode="name")` → get contactId
2. `create_note(contactId, content)`

**"Tag everyone at Acme Corp as client"**

1. `search_contacts("Acme Corp", searchMode="company")`
2. Loop `add_tag(contactId, "client")`

---

## Quick Reference

| Tool                               | When to use                                            |
| ---------------------------------- | ------------------------------------------------------ |
| `list_connected_integrations`      | Always check first — detects MCP and integration state |
| `search_microsoft_contacts`        | Search Outlook/Exchange directory                      |
| `get_microsoft_contact`            | Full Outlook contact details                           |
| `search_contacts`                  | Search CRM contacts (includes synced Outlook, + notes) |
| `get_contact`                      | Full CRM profile for one person                        |
| `update_contact`                   | Edit a contact's CRM fields                            |
| `get_upcoming_microsoft_events`    | Check Outlook calendar                                 |
| `search_microsoft_calendar_events` | Find a specific event                                  |
| `find_available_microsoft_time`    | Find free slot before scheduling                       |
| `create_microsoft_calendar_event`  | Create Outlook/Teams meeting                           |
| `reschedule_microsoft_event`       | Move an event                                          |
| `cancel_microsoft_event`           | Cancel an event                                        |
| `create_note`                      | Log a meeting, call, or interaction                    |
| `update_note`                      | Edit a note                                            |
| `delete_note`                      | Remove a note                                          |
| `list_notes`                       | All notes for one contact                              |
| `get_note`                         | Full note content                                      |
| `pin_note`                         | Mark as critical context                               |
| `search_notes`                     | Find notes by keyword across all contacts              |
| `get_recent_notes`                 | Latest activity across the network                     |
| `list_tags`                        | See all tags in use                                    |
| `add_tag` / `remove_tag`           | Categorise contacts                                    |
| `rename_tag`                       | Rename a tag everywhere                                |
| `connect_integration`              | Connect Microsoft account (contacts, calendar, email)  |
| `get_integration_sync_status`      | Check when sync completes                              |
| `list_microsoft_emails`            | List recent Outlook inbox emails                       |
| `search_microsoft_emails`          | Search Outlook emails by subject, sender, or keyword   |

---

## References

- [MCP setup — all supported clients](references/SETUP.md)

## Other capabilities (outside this skill)

- **Outlook email search** — list and search your Outlook inbox, cross-reference email threads with CRM notes. Install `find-outlook-emails`.
- **Google Contacts and Calendar** — Install `organize-google-contacts` and `schedule-with-google-calendar`.
- **LinkedIn sync** — requires the Rarefriend Chrome extension. Direct user to rarefriend.com → Settings → Integrations → LinkedIn. Once synced, LinkedIn connections are searchable here.
- **Hops on WhatsApp** — same contacts and notes accessible via Rarefriend's WhatsApp AI assistant.
- **Reminders and phone contacts** — available in the web app at rarefriend.com.
- **Full feature set in one skill** — install `network-and-relationship-manager`.
