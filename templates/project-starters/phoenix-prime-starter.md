# Phoenix Prime Starter

A minimal, opinionated template for wiring Claude Code (or any agent CLI) into a persistent operating system.

## What it does

Seven markdown files (~400 lines) that give an agent:
- Persistent identity across sessions (SOUL.md, IDENTITY.md)
- A live work queue it picks up without prompting (PRIORITIES.md)
- Epistemic tagging and pushback protocol
- Boot sequence and memory discipline (AGENTS.md)
- Deterministic boot from version-controlled files

## Quick start

1. Click **Use this template** on GitHub
2. Replace `{{PLACEHOLDER}}` values in IDENTITY.md and USER.md. Do not include API keys, credentials, or personal data — remove secrets/PII before committing.
3. Run `claude`
4. First message: "Read the boot sequence in AGENTS.md and tell me the current state."

> **Advanced:** Use `--dangerously-skip-permissions` only in isolated VMs or containers where auto-approving all tool calls is acceptable. Not recommended for general use.

## Links

- **Repository**: https://github.com/phoenixprimeAI/phoenix-prime-starter
- **Full deployment (Phoenix Kit)**: https://phoenixprime.me/kit

## Why use this

Most Claude Code resources focus on skills or commands. This template solves agent persistence — instead of re-explaining context every session, the agent boots from its own identity files. No npm, no Python, no runtime. Just markdown.

Built by [Phoenix Prime](https://phoenixprime.me), an AI CEO agent running in production on Hetzner.
