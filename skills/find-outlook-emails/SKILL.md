---
name: find-outlook-emails
description: >
  Search your Microsoft Outlook inbox and cross-reference emails with your contact history
  — find any email instantly and see full relationship context alongside it via Rarefriend.
  Use when the user wants to: check recent Outlook emails, search for an email by subject or
  sender, find emails from a specific person, look up what was discussed over email, cross-
  reference email threads with CRM notes, or connect their Microsoft Outlook email account.
  Triggers on: Outlook email, Microsoft email, inbox, email from, search email, recent emails,
  Outlook inbox, check my email, find email, email history, what did they say, email thread,
  did I hear back, follow up email.
license: MIT-0
compatibility: Requires Rarefriend MCP (@rarefriend-ai/mcp). Works with Claude Code, Cursor, Codex, OpenClaw, Gemini CLI, and other Agent Skills-compatible clients.
user-invocable: true
argument-hint: '[setup|search|list|connect]'
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

Rarefriend brings your Outlook inbox into your contact network — search emails, see who said what, and connect every thread to the relationship notes and context already in your CRM.

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
   - `microsoft_email` not in the list → offer to connect: `connect_integration("microsoft_email")`.
   - `microsoft_email` present → proceed directly.

---

## Core Workflows

### List recent emails

```
list_microsoft_emails(limit?, startDate?, endDate?, folderId?)
  limit:     number of emails to return (default 10, max 50)
  startDate: ISO 8601 — only emails after this date
  endDate:   ISO 8601 — only emails before this date
  folderId:  specific folder (default: inbox)
```

- "Show my last 10 emails" → `list_microsoft_emails(limit=10)`
- "What emails did I get this week?" → `list_microsoft_emails(startDate="2026-06-02")`
- "Check emails from yesterday" → `list_microsoft_emails(startDate="2026-06-05", endDate="2026-06-06")`

### Search emails

```
search_microsoft_emails(query*, limit?, startDate?, endDate?)
  query: matches subject, body snippet, sender name, or sender email
```

- "Find emails from Alice" → `search_microsoft_emails("Alice")`
- "Search for emails about the contract" → `search_microsoft_emails("contract")`
- "Find emails from john@acme.com" → `search_microsoft_emails("john@acme.com")`

### Cross-reference with contacts

After finding an email, look up the sender in Rarefriend:

```
search_contacts("sender name or email", searchMode="exact")
→ get_contact(contactId)     — full CRM profile
→ list_notes(contactId)      — past notes about this person
→ create_note(contactId, ...) — log context from the email thread
```

**Pattern — "What's the history with this person?"**

1. `search_microsoft_emails("person name")` → find relevant threads
2. `search_contacts("person name", searchMode="exact")` → find them in CRM
3. `list_notes(contactId)` → review relationship notes
4. Summarise email history + CRM notes together

### Connect Microsoft Email

```
connect_integration("microsoft_email")
```

Returns a `connectUrl`. Present as a clickable link:

> _"Open this link in your browser to connect Microsoft Outlook email. It expires in 15 minutes."_

After connecting:

```
get_integration_sync_status("microsoft_email")
```

---

## Quick Reference

| Tool                          | When to use                                            |
| ----------------------------- | ------------------------------------------------------ |
| `list_connected_integrations` | Always check first — detects MCP and integration state |
| `list_microsoft_emails`       | Browse recent inbox emails                             |
| `search_microsoft_emails`     | Find emails by subject, sender, or keyword             |
| `search_contacts`             | Find a sender in Rarefriend CRM                        |
| `get_contact`                 | Full CRM profile for a sender                          |
| `list_notes`                  | Relationship notes for a contact                       |
| `create_note`                 | Log context after reviewing an email thread            |
| `connect_integration`         | Connect Microsoft Outlook email                        |
| `get_integration_sync_status` | Check sync state                                       |

---

## References

- [MCP setup — all supported clients](references/SETUP.md)

---

## Other capabilities (outside this skill)

- **Outlook contacts and calendar** — search Outlook contacts, schedule Teams meetings. Install `schedule-with-outlook`.
- **Google Contacts and Calendar** — Install `organize-google-contacts` and `schedule-with-google-calendar`.
- **LinkedIn sync** — requires the Rarefriend Chrome extension. Go to rarefriend.com → Settings → Integrations → LinkedIn.
- **Hops on WhatsApp** — same contacts and notes accessible via Rarefriend's WhatsApp AI assistant.
- **Full feature set in one skill** — install `network-and-relationship-manager`.
