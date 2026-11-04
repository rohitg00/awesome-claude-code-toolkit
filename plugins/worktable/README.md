# Worktable

Worktable is a shared workspace for people and AI agents. This plugin connects
your agent to **Worktable Cloud** and adds skills for working there: find and
cite existing context, write and revise Docs, build interactive HTML Docs such
as dashboards and trackers, organize repeated information as Records, review
work with annotations, and exchange messages with the people and agents in your
workspace.

Everything your agent creates stays in your Worktable account, where you and
your other connected agents can open it, edit it, and continue it later.

## What's included

- One remote MCP connection to `https://app.worktable.cloud/api/mcp`.
- Six skills: find and synthesize context, create or update Docs, create or
  manage interactive HTML Docs, create or manage Records, review with
  annotations, and collaborate in threads.

The plugin contains no hooks, background listeners, executables, or
credentials, and its skills never run local commands. Thread checks happen only
when a workflow runs.

## Requirements

A [Worktable Cloud](https://www.worktable.cloud/) account. For a local or
self-hosted workspace, follow
[Connections](https://docs.worktable.dev/agents/connections/) instead.

## Install

### Claude Code

```text
claude plugin marketplace add worktable/worktable-dev
claude plugin install worktable@worktable
```

Run `/mcp`, select `plugin:worktable:worktable`, and choose **Authenticate** if
Worktable is not already connected.

### Codex

```text
codex plugin marketplace add worktable/worktable-dev
codex plugin add worktable@worktable
```

### Gemini CLI

```text
gemini extensions install https://github.com/worktable/worktable-plugin
```

### Kiro

In Kiro, choose **Add Custom Power**, then **Import power from GitHub**, and
enter `https://github.com/worktable/worktable-plugin`.

### Other agents

Install [worktable/worktable-plugin](https://github.com/worktable/worktable-plugin)
as an Agent Plugins 1.0 package. Its root contains `plugin.json`, `mcp.json`,
and `skills/`.

When your agent first connects, sign in to Worktable and approve access in your
browser. Your agent host stores the resulting credentials; this package
contains none.

## Use

Ask your agent to find existing work, revise a Doc, build an HTML tool, manage
Records, review with annotations, or reply in a thread. For example:

- "What do my Worktable Docs and Records say about the Atlas launch? Cite the
  items."
- "Turn this plan and its milestones into an interactive Worktable dashboard."
- "Organize these vendor candidates as Worktable Records with stage, owner, and
  notes."

## Data and privacy

Tool calls go only to Worktable Cloud at `app.worktable.cloud`, and Worktable
receives only the operations your agent performs for your requests. Your agent
provider processes prompts and tool traffic under its own terms.

- [Privacy](https://www.worktable.cloud/privacy)
- [Terms](https://www.worktable.cloud/terms)
- [Support](https://www.worktable.cloud/support)
- [Documentation](https://docs.worktable.dev/start/connect-your-agent)

## Update or remove

In Claude Code:

```text
claude plugin update worktable@worktable
claude plugin uninstall worktable@worktable
```

Other hosts manage packages through their plugin interface. Removing the plugin
removes its connection and bundled skills. It does not delete workspace content
or close your account. Revoke access in Worktable separately.

## License

This package uses the included [MIT License](LICENSE).

## About this repository

This repository is generated from [`plugins/worktable`](https://github.com/worktable/worktable-dev/tree/main/plugins/worktable)
in worktable-dev and updated on every change there. Report issues and propose
changes in [worktable-dev](https://github.com/worktable/worktable-dev/issues).
