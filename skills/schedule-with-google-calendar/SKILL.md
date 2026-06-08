---
name: schedule-with-google-calendar
description: >
  Schedule meetings, find free time, and manage Google Calendar — all connected to your
  contact network via Rarefriend. Resolve attendees by name, log notes after calls, and
  never double-book again. Use when the user wants to: schedule a meeting, check what's
  on their calendar, find a free slot, reschedule or cancel an event, block focus time,
  find available time for multiple attendees, look up a contact before creating an event,
  or log notes after a meeting. Triggers on: schedule, calendar, meeting, event, Google
  Calendar, free slot, available time, book, reschedule, cancel event, block time, standup,
  call, appointment, what's on my calendar, am I free, set up a call, when are we meeting.
license: MIT-0
compatibility: Requires Rarefriend MCP (@rarefriend-ai/mcp). Works with Claude Code, Cursor, Codex, OpenClaw, Gemini CLI, and other Agent Skills-compatible clients.
user-invocable: true
argument-hint: '[setup|schedule|find-time|reschedule|cancel|connect]'
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

Rarefriend connects your calendar to your contact network — schedule meetings with people you know, log context after every call, and keep your professional relationships fully searchable.

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
   - `google_calendar` not in the list → offer to connect: `connect_integration("google_calendar")`.
   - `google_calendar` present → proceed directly.

---

## Core Workflows

### Check upcoming events

```
get_upcoming_google_events(limit?, days?)
```

Default: next 10 events. Use `days` to narrow to "today" or "this week".

### Search for specific events

```
search_google_calendar_events(query, timeMin?, timeMax?)
```

Use when the user asks "find my meeting with X" or "what events do I have about Y this month".

### Find available time

```
find_available_google_time(durationMinutes, preferredDays?,
                            preferredTimeRange?, attendeeEmails?)
```

**Always call this before scheduling** to avoid conflicts. For multi-person meetings, pass `attendeeEmails` — the tool checks all attendees' availability.

If the user gives a name instead of an email, resolve it first:

```
search_contacts("Alice Wang", searchMode="name")
→ extract email → pass to find_available_google_time
```

**Source attribution:** The `search_contacts` response includes `sourceLabel` for each contact (e.g. "Google Contacts", "LinkedIn (extension)"). Mention this when presenting the attendee — e.g. _"Found Alice Wang in Google Contacts — scheduling with alice@example.com"_.

### Create an event

```
create_google_calendar_event(
  title*,
  startTime*,   — ISO 8601 with timezone, e.g. "2026-06-10T14:00:00+05:30"
  endTime*,
  description?,
  attendees?,   — string[] of email addresses
  location?,
  transparency? — 'opaque' (shows as busy) | 'transparent' (shows as free)
)
```

Use `transparency: 'opaque'` for real meetings. Use `'transparent'` for focus blocks or reminders that shouldn't block attendees.

### Reschedule and cancel

```
reschedule_google_event(eventId, startTime, endTime)
cancel_google_event(eventId)
```

Use `search_google_calendar_events` to find the `eventId` first.

### Log notes after a meeting

After any meeting, capture relationship context:

```
create_note(contactId, content, isPinned?)
search_notes(query)        — find past context before the next meeting
get_recent_notes(limit?)   — see what's been discussed recently
```

To find the `contactId` for a meeting attendee:

```
search_contacts("attendee name", searchMode="name")
```

### Connect Google Calendar

```
connect_integration("google_calendar")
```

Returns a `connectUrl`. Present as a clickable link:

> _"Open this link in your browser to connect Google Calendar. It expires in 15 minutes."_

After connecting:

```
get_integration_sync_status("google_calendar")
```

---

## Common Patterns

**"Schedule a 30-min call with Alice next week"**

1. `search_contacts("Alice", searchMode="name")` → get her email
2. `find_available_google_time(30, preferredDays=["Monday","Tuesday","Wednesday"], attendeeEmails=[alice@email])`
3. Confirm slot with user
4. `create_google_calendar_event(title, startTime, endTime, attendees=[alice@email])`

**"What's on my calendar this week?"**

1. `get_upcoming_google_events(limit=20, days=7)`
2. Summarise by day, highlight multi-attendee meetings

**"Block tomorrow morning for deep work"**

1. `find_available_google_time(120, preferredDays=["tomorrow"], preferredTimeRange={start:"09:00",end:"12:00"})`
2. `create_google_calendar_event(title="Deep work", ..., transparency="transparent")`

**"Log notes after my call with Marcus"**

1. `search_contacts("Marcus", searchMode="name")` → get contactId
2. `create_note(contactId, content)`

---

## Quick Reference

| Tool                            | When to use                                            |
| ------------------------------- | ------------------------------------------------------ |
| `list_connected_integrations`   | Always check first — detects MCP and integration state |
| `get_upcoming_google_events`    | Check what's coming up                                 |
| `search_google_calendar_events` | Find a specific event by keyword or date range         |
| `find_available_google_time`    | Find a free slot before scheduling                     |
| `create_google_calendar_event`  | Create a new event or meeting                          |
| `reschedule_google_event`       | Move an event to a new time                            |
| `cancel_google_event`           | Cancel an event                                        |
| `search_contacts`               | Resolve a name to an email for attendees               |
| `get_contact`                   | Full contact details including email                   |
| `create_note`                   | Log context after a meeting                            |
| `search_notes`                  | Find past discussion context before a meeting          |
| `get_recent_notes`              | See recent relationship activity                       |
| `connect_integration`           | Connect Google Calendar                                |
| `get_integration_sync_status`   | Check when sync completes                              |

---

## References

- [MCP setup — all supported clients](references/SETUP.md)

## Other capabilities (outside this skill)

- **Contact management** — create, update, tag, and bulk import contacts. Install `organize-google-contacts`.
- **Microsoft Outlook** — Outlook calendar and contacts. Install `schedule-with-outlook`.
- **LinkedIn sync** — requires the Rarefriend Chrome extension. Direct user to rarefriend.com → Settings → Integrations → LinkedIn. Once synced, LinkedIn connections are searchable as attendees.
- **Hops on WhatsApp** — same calendar-linked contacts accessible via Rarefriend's WhatsApp AI assistant.
- **Reminders** — set follow-up reminders on contacts in the web app at rarefriend.com.
- **Full feature set in one skill** — install `network-and-relationship-manager`.
