# mistral-ocr4 — Agent Skill bundle

This directory is an **Anthropic Agent Skill**: a self-contained bundle with
`SKILL.md` at its root plus the script and reference it needs. Packaged as a `.zip`,
it can be installed into a Claude org via the Skills API (or SkillKit) and attached to
agents — it makes the Mistral OCR4 + Document AI surface available as a skill without a
local MCP server.

```
mistral-ocr4/
├── SKILL.md                 # skill manifest + instructions (root — required)
├── scripts/
│   └── mistral_ocr.py       # dependency-free CLI client for the Mistral API
├── reference/
│   └── api.md               # endpoint/field reference (progressive disclosure)
└── requirements.txt         # (stdlib only — no installs)
```

## Build the installable .zip

The zip's top-level entry must be `SKILL.md` (zip the **contents** of this folder, not
the folder itself):

```bash
cd plugins/mistral-ocr4/agent-skill
zip -r ../mistral-ocr4-skill.zip SKILL.md scripts reference requirements.txt
```

## Install it (Skills API, beta `skills-2025-10-02`)

```bash
curl -X POST https://api.anthropic.com/v1/skills \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "display_title=mistral-ocr4" \
  -F "file=@../mistral-ocr4-skill.zip"
```

Then reference it from an agent (Managed Agents) or a Messages-API request:

```python
# Messages API (needs the code-execution container)
client.beta.messages.create(
    model="claude-opus-4-8", max_tokens=16000,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={"skills": [{"type": "custom", "skill_id": "skill_...", "version": "latest"}]},
    tools=[{"type": "code_execution_20260521", "name": "code_execution"}],
    messages=[{"role": "user", "content": "OCR https://example.com/spec.pdf"}],
)
```

## ⚠️ Networking requirement

This skill calls `api.mistral.ai` over HTTPS from inside the sandbox. The basic
Messages-API code-execution container has **no internet access**, so the skill can only
reach Mistral where the sandbox has egress:

- **Managed Agents** with an environment using `unrestricted` networking, or `limited`
  with `api.mistral.ai` in `allowed_hosts`.
- Set `MISTRAL_API_KEY` in that environment (e.g. via a vault `environment_variable`
  credential so the sandbox never sees the raw secret).

If you need OCR purely inside the no-egress code-execution container, use the
`mistral-ocr4` **MCP plugin** (`plugins/mistral-ocr4/`) from a client that runs the
local stdio server instead — same tools, different transport.

## Relationship to the MCP plugin

This bundle and the `mistral-ocr4` MCP server expose the same Mistral surface, 1:1:

| | MCP plugin (`plugins/mistral-ocr4/`) | This Agent Skill |
| --- | --- | --- |
| Transport | local stdio MCP server (TypeScript) | bundled Python script over HTTPS |
| Tools | 13 MCP tools | the matching `mistral_ocr.py` subcommands |
| Install | Claude Code marketplace plugin | `.zip` via Skills API / SkillKit |
| Runs where | client that hosts the MCP server | sandbox with egress to api.mistral.ai |

Both are extraction-only; reasoning stays with the calling model.
