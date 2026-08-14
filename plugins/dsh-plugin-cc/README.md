# dsh-plugin-cc

Claude Code marketplace bridging to the [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`dsh`) agent.

## Install

```bash
/plugin marketplace add cpj-dev/dsh-plugin-cc
/plugin install dsh@deepseek-dsh
/dsh:setup
```

## Commands

| Command | Purpose |
|---|---|
| `/dsh:check` | Readiness probe |
| `/dsh:review` | Read-only review of local changes |
| `/dsh:critique` | Adversarial design critique |
| `/dsh:delegate <task>` | Background delegation |
| `/dsh:run <task>` | One-shot or resumable dsh session |

Source: https://github.com/cpj-dev/dsh-plugin-cc
