# DeepRFP MCP Connector

A Model Context Protocol (MCP) custom connector for [DeepRFP](https://deeprfp.com/),
the AI RFP/tender platform used in public procurement. It exposes DeepRFP's AI
agents — tender analysis, proposal drafting, questionnaire automation,
compliance matrices, and proposal review — as MCP tools so Claude can drive your
bid workflow directly.

> **Note on the API.** DeepRFP does not publish an official public API. This
> connector is built against DeepRFP's documented agent capabilities and keeps
> the HTTP layer fully configurable (`DEEPRFP_API_BASE_URL`) so it can target
> whatever endpoint your DeepRFP account exposes or a compatible proxy. Confirm
> the endpoint paths and request shapes with DeepRFP for your account before
> relying on it in production.

## Tools

| Tool | Description |
|------|-------------|
| `deeprfp_list_projects` | List RFP/tender projects, optionally filtered by status. |
| `deeprfp_get_project` | Retrieve a project with its documents and generated artifacts. |
| `deeprfp_create_project` | Create a project for a specific opportunity. |
| `deeprfp_analyze_rfp` | Analyzer agent: requirements, dates, criteria, bid/no-bid recommendation. |
| `deeprfp_draft_response` | Writer agent: draft proposal sections grounded in your content library. |
| `deeprfp_answer_questionnaire` | Auto-fill questionnaire/RFQ questions from your library. |
| `deeprfp_generate_compliance_matrix` | Map tender requirements to responses/evidence. |
| `deeprfp_review_proposal` | Color/red-team review with optional rewrite. |
| `deeprfp_search_library` | Search your content library for reusable material. |

## Configuration

| Env var | Required | Default | Purpose |
|---------|----------|---------|---------|
| `DEEPRFP_API_KEY` | yes | — | Bearer token for your DeepRFP account. |
| `DEEPRFP_API_BASE_URL` | no | `https://api.deeprfp.com/v1` | API base URL. |
| `DEEPRFP_TIMEOUT_MS` | no | `120000` | Per-request timeout in milliseconds. |

## Install & build

```bash
cd mcp-servers/deeprfp
npm install
npm run build
```

## Installable bundle (.mcpb)

For a one-click install in Claude Desktop, build an MCP bundle:

```bash
cd mcp-servers/deeprfp
bash scripts/pack-mcpb.sh    # produces deeprfp.mcpb
```

`deeprfp.mcpb` is a self-contained, installable connector (server code +
dependencies + [`manifest.json`](manifest.json)). Open it in Claude Desktop —
you'll be prompted for your DeepRFP API key — or install via CLI:

```bash
npx @anthropic-ai/mcpb install deeprfp.mcpb
```

## Use with Claude Code

Add it to your MCP config (see [`mcp-configs/procurement.json`](../../mcp-configs/procurement.json)):

```json
{
  "mcpServers": {
    "deeprfp": {
      "command": "node",
      "args": ["./mcp-servers/deeprfp/dist/index.js"],
      "env": {
        "DEEPRFP_API_KEY": "<your-deeprfp-api-key>"
      }
    }
  }
}
```

Or register it directly:

```bash
claude mcp add deeprfp -e DEEPRFP_API_KEY=<your-key> -- node ./mcp-servers/deeprfp/dist/index.js
```

## Development

```bash
npm run dev   # tsc --watch
```

The server speaks MCP over stdio. You can smoke-test it with:

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | DEEPRFP_API_KEY=test node dist/index.js
```
