# Install dsh-plugin-cc

This toolkit entry points at the live marketplace. Install it from the source repo rather than copying the runtime into this toolkit:

```bash
/plugin marketplace add cpj-dev/dsh-plugin-cc
/plugin install dsh@deepseek-dsh
```

Then run `/dsh:setup` once (needs `DEEPSEEK_API_KEY`, Node >= 20, and a DeepSeek Harness source build).

After that, in any git repository:

- `/dsh:check` — readiness probe
- `/dsh:review` — read-only review of local changes
- `/dsh:critique` — adversarial design critique
- `/dsh:delegate <task>` — background delegation
- `/dsh:run <task>` — one-shot or resumable dsh session

Repo: https://github.com/cpj-dev/dsh-plugin-cc
