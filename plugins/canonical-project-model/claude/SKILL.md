---
name: ntxp-plans-atlas
description: Claude adapter for the NTXP Canonical Project Record and Plans Atlas. Follows the shared contract in ../AGENTS.md; adds Claude Code, claude.ai/Cowork, and Claude API mechanics.
---

# NTXP Plans Atlas — Claude Adapter

Read and follow the shared contract in `../AGENTS.md` and the defaults in
`../config/defaults.yaml`. The root `SKILL.md` is the full Claude skill; this
file covers platform mechanics only.

## Claude Code (CLI, desktop, web)

- **Install:** add the toolkit marketplace and install the plugin
  (`/plugin marketplace add ntxptrevor/awesome-claude-code-toolkit`, then
  `/plugin install canonical-project-model`). Or place the skill folder at
  `~/.claude/skills/ntxp-plans-atlas/` for every project on the machine. In cloud
  sessions, add that copy step to the environment's setup script, because
  containers are ephemeral.
- **Run the scripts directly** with Bash. Never re-derive script output by hand
  when the script can run.
- **Parallelize:** normalize sections with parallel subagents, reconciling
  subcontractors first and the QTO before budget, bid, and submittal sections.
  Deploy the atlas in parallel with section normalization, because it depends
  only on the drawings.
- **Model routing:** use the frontier model for blueprinting, conflict
  adjudication, and the final record. Use a mid-tier model for section
  normalizers and a small model for mechanical passes (unit normalization,
  sorting). Convene the parsing council only on the triggers in
  `../reference/model-council.md`.
- **Publishing:** render the viewer or dashboard with `--fragment` when it will
  be embedded in an Artifact; otherwise ship the standalone HTML file.

## claude.ai and Cowork

- Upload the packaged `.skill.zip` under *Settings → Capabilities → Skills*.
  Re-uploading the same skill name replaces the prior version. The description
  must stay at or under 1,024 characters.
- Code execution and file creation must be enabled so the scripts can run.
  PyMuPDF may not be present; the extractor then runs in manifest-only mode,
  and you must say so.
- Deploy automatically on the AGENTS.md section 3 events, and file the viewer
  under the project's Construction Documents folder. With the Google Drive
  connector, resolve that folder through the NTXP folder system before writing.

## Claude API

- Register `../tools/functions.json` with each function's `parameters` object
  passed as `input_schema`; names and descriptions are unchanged. Execute calls
  with `python scripts/run_tool.py <name> '<arguments-json>'` and return stdout
  as the `tool_result`.
- Put `../AGENTS.md` in the system prompt and mark it for prompt caching: it is
  stable across every call for a project.
- Settings: low temperature for normalization; JSON-only output for sections,
  validated against the schemas on the host.
